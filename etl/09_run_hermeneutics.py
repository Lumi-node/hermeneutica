"""
Run hermeneutics classification on high-value chapters and load results into DB.

Identifies the most ethically dense chapters (using Nave's topic density),
classifies them with the hermeneutics engine (Claude), and stores the
results in passage_classifications + distilled_principles tables.

Usage:
    python -m etl.09_run_hermeneutics                    # classify all high-value chapters
    python -m etl.09_run_hermeneutics --limit 10         # classify 10 chapters (test run)
    python -m etl.09_run_hermeneutics --min-topics 5     # only chapters with 5+ ethical topics
    python -m etl.09_run_hermeneutics --stats            # show classification status
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from etl.db import get_connection, table_count
from src.hermeneutics import (
    classify_passage,
    PassageClassification,
    HERMENEUTICS_DIR,
    _save_cached,
    _load_cached,
)


ETHICAL_TOPICS = [
    'Justice', 'Mercy', 'Faith', 'Love', 'Righteousness', 'Truth',
    'Wisdom', 'Repentance', 'Forgiveness', 'Obedience', 'Humility', 'Grace',
    'Sin', 'Redemption', 'Covenant', 'Holiness', 'Faithfulness', 'Compassion',
    'Honesty', 'Integrity', 'Patience', 'Generosity', 'Courage',
    'Perseverance', 'Self-Denial', 'Temptation', 'Duty', 'Conscience',
    'Charity', 'Kindness', 'Prayer', 'Gratitude', 'Hope', 'Peace', 'Trust',
    'Afflictions Made Beneficial', 'Golden Rule', 'Responsibility',
    'Reward of Saints, the', 'Punishment', 'Protection',
]


def get_high_value_chapters(conn, min_ethical_topics: int = 3) -> list[dict]:
    """Query DB for chapters with the highest density of ethical teaching."""
    topic_list = ",".join(f"'{t}'" for t in ETHICAL_TOPICS)

    with conn.cursor() as cur:
        cur.execute(f"""
            WITH chapter_ethics AS (
                SELECT ch.id as chapter_id, b.name as book, ch.chapter_number as ch_num,
                       b.genre,
                       count(DISTINCT nt.topic) FILTER (
                           WHERE nt.topic IN ({topic_list})
                       ) as ethical_topics,
                       array_agg(DISTINCT nt.topic ORDER BY nt.topic) FILTER (
                           WHERE nt.topic IN ({topic_list})
                       ) as topic_list
                FROM chapters ch
                JOIN books b ON b.id = ch.book_id
                JOIN verses v ON v.chapter_id = ch.id AND v.translation_id = 1
                JOIN nave_topic_verses ntv ON ntv.verse_id = v.id
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                GROUP BY ch.id, b.name, ch.chapter_number, b.genre
            )
            SELECT chapter_id, book, ch_num, genre, ethical_topics, topic_list
            FROM chapter_ethics
            WHERE ethical_topics >= {min_ethical_topics}
            ORDER BY ethical_topics DESC, book, ch_num
        """)
        rows = cur.fetchall()

    return [
        {
            "chapter_id": r[0],
            "book": r[1],
            "chapter": r[2],
            "genre": r[3],
            "ethical_topics": r[4],
            "topics": r[5],
        }
        for r in rows
    ]


def get_chapter_text(conn, book: str, chapter: int) -> str:
    """Get the full KJV text of a chapter."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT string_agg(v.verse_number || '. ' || v.text, ' ' ORDER BY v.verse_number)
            FROM verses v
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            WHERE b.name = %s AND ch.chapter_number = %s
              AND v.translation_id = (SELECT id FROM translations WHERE abbreviation = 'KJV')
        """, (book, chapter))
        row = cur.fetchone()
        return row[0] if row and row[0] else ""


def load_classification_to_db(conn, classification: PassageClassification, chapter_id: int):
    """Store a classification and its principles in the database."""
    with conn.cursor() as cur:
        # Insert classification
        cur.execute("""
            INSERT INTO passage_classifications
                (chapter_id, genre, genre_confidence, themes, teaching_type,
                 ethics_reasoning, classified_by, classified_at, schema_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now(), %s)
            ON CONFLICT (chapter_id) DO UPDATE SET
                genre = EXCLUDED.genre,
                genre_confidence = EXCLUDED.genre_confidence,
                themes = EXCLUDED.themes,
                teaching_type = EXCLUDED.teaching_type,
                ethics_reasoning = EXCLUDED.ethics_reasoning,
                classified_by = EXCLUDED.classified_by,
                classified_at = EXCLUDED.classified_at
            RETURNING id
        """, (
            chapter_id,
            classification.genre,
            classification.genre_confidence,
            classification.themes,
            classification.teaching_type,
            classification.ethics_reasoning,
            classification.classified_by,
            classification.schema_version,
        ))
        class_id = cur.fetchone()[0]

        # Delete old principles and ethics scores for this classification
        cur.execute("DELETE FROM distilled_principles WHERE classification_id = %s", (class_id,))
        cur.execute("DELETE FROM passage_ethics_scores WHERE classification_id = %s", (class_id,))

        # Insert principles
        for i, principle in enumerate(classification.distilled_principles):
            cur.execute("""
                INSERT INTO distilled_principles (classification_id, principle_text, principle_order)
                VALUES (%s, %s, %s)
            """, (class_id, principle, i))

        # Insert ethics scores
        for subset, score in classification.ethics_mapping.items():
            cur.execute("""
                INSERT INTO passage_ethics_scores (classification_id, ethics_subset, relevance_score)
                VALUES (%s, %s, %s)
            """, (class_id, subset, score))

        conn.commit()


async def classify_chapters(
    chapters: list[dict],
    conn,
    model: str = "claude-sonnet-4-20250514",
    concurrency: int = 5,
):
    """Classify chapters concurrently, with caching and DB storage."""
    sem = asyncio.Semaphore(concurrency)
    classified = 0
    skipped = 0

    async def _classify_one(ch: dict):
        nonlocal classified, skipped

        book = ch["book"]
        chapter = ch["chapter"]
        chapter_id = ch["chapter_id"]

        # Check cache first
        cached = _load_cached(book, chapter)
        if cached is not None:
            # Still load to DB if not there
            load_classification_to_db(conn, cached, chapter_id)
            skipped += 1
            return

        # Get chapter text
        text = get_chapter_text(conn, book, chapter)
        if not text:
            print(f"  WARNING: No text for {book} {chapter}")
            return

        async with sem:
            try:
                print(f"  [{classified + skipped + 1}] Classifying {book} {chapter} ({ch['ethical_topics']} ethical topics)...")
                result = await classify_passage(book, chapter, text, model=model)
                _save_cached(result)
                load_classification_to_db(conn, result, chapter_id)
                classified += 1

                # Show a sample principle
                if result.distilled_principles:
                    print(f"       -> {result.distilled_principles[0][:80]}...")

            except Exception as e:
                print(f"  ERROR classifying {book} {chapter}: {e}")

    tasks = [_classify_one(ch) for ch in chapters]
    await asyncio.gather(*tasks)

    return classified, skipped


def show_stats(conn):
    """Show current classification status."""
    total_chapters = table_count(conn, "chapters")
    classified = table_count(conn, "passage_classifications")
    principles = table_count(conn, "distilled_principles")
    ethics_scores = table_count(conn, "passage_ethics_scores")

    print(f"\n{'='*50}")
    print(f"HERMENEUTICS CLASSIFICATION STATUS")
    print(f"{'='*50}")
    print(f"Total chapters:           {total_chapters:,}")
    print(f"Classified:               {classified:,}")
    print(f"Coverage:                 {classified/total_chapters*100:.1f}%")
    print(f"Distilled principles:     {principles:,}")
    print(f"Ethics scores:            {ethics_scores:,}")

    if classified > 0:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT b.name, count(*) as classified_count
                FROM passage_classifications pc
                JOIN chapters ch ON ch.id = pc.chapter_id
                JOIN books b ON b.id = ch.book_id
                GROUP BY b.name
                ORDER BY classified_count DESC
                LIMIT 10
            """)
            print(f"\nTop classified books:")
            for row in cur.fetchall():
                print(f"  {row[0]}: {row[1]}")

        with conn.cursor() as cur:
            cur.execute("""
                SELECT principle_text FROM distilled_principles ORDER BY random() LIMIT 5
            """)
            print(f"\nSample principles:")
            for row in cur.fetchall():
                print(f"  -> {row[0][:100]}")


def main():
    parser = argparse.ArgumentParser(description="Run hermeneutics classification on high-value chapters")
    parser.add_argument("--limit", type=int, default=None, help="Max chapters to classify")
    parser.add_argument("--min-topics", type=int, default=3, help="Min ethical topics per chapter (default: 3)")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-20250514", help="Claude model for classification")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent API calls")
    parser.add_argument("--stats", action="store_true", help="Show classification status")
    args = parser.parse_args()

    conn = get_connection()

    try:
        if args.stats:
            show_stats(conn)
            return

        chapters = get_high_value_chapters(conn, min_ethical_topics=args.min_topics)
        print(f"Found {len(chapters)} high-value chapters (min {args.min_topics} ethical topics)")

        if args.limit:
            chapters = chapters[:args.limit]
            print(f"Limited to {args.limit} chapters")

        print(f"Model: {args.model}")
        print(f"Concurrency: {args.concurrency}")

        classified, skipped = asyncio.run(
            classify_chapters(chapters, conn, model=args.model, concurrency=args.concurrency)
        )

        print(f"\nDone: {classified} newly classified, {skipped} from cache")
        show_stats(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
