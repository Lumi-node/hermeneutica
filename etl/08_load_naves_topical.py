"""Load Nave's Topical Bible + Torrey's from MetaV into nave_topics and nave_topic_verses.

Source: data/raw/MetaV/CSV/Topics.csv and TopicIndex.csv
Maps ~32K topics to ~93K verse references.

Usage: python -m etl.08_load_naves_topical
"""

import csv

from .config import RAW_DATA_DIR
from .db import get_connection, bulk_insert, table_count


METAV_DIR = RAW_DATA_DIR / "MetaV" / "CSV"


def run():
    topics_file = METAV_DIR / "Topics.csv"
    index_file = METAV_DIR / "TopicIndex.csv"
    verses_file = METAV_DIR / "Verses.csv"

    if not topics_file.exists():
        print(f"ERROR: {topics_file} not found. Clone MetaV first.")
        return

    conn = get_connection()
    try:
        # --- Load topics ---
        print("Loading topics...")
        topic_rows = []
        with open(topics_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                try:
                    tid = int(row[0])
                except ValueError:
                    continue
                topic = row[1].strip()
                subtopic = row[2].strip() if len(row) > 2 else ""
                topic_rows.append((tid, topic[:120], subtopic[:200]))

        count = bulk_insert(
            conn,
            table="nave_topics",
            columns=["id", "topic", "subtopic"],
            rows=topic_rows,
            conflict_columns=["id"],
        )
        total_topics = table_count(conn, "nave_topics")
        print(f"  Topics: processed {len(topic_rows)}, DB total: {total_topics}")

        # --- Build MetaV VerseID -> our verse_id mapping ---
        # MetaV uses sequential VerseIDs (1-31102), we need to map to our verse_id
        print("Building verse ID mapping...")

        # Load MetaV verse ordering
        metav_verses = {}  # metav_verse_id -> (book_id, chapter, verse_num)
        with open(verses_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) < 4:
                    continue
                try:
                    mv_id = int(row[0])
                    book_id = int(row[1])
                    chapter = int(row[2])
                    verse_num = int(row[3])
                except ValueError:
                    continue
                metav_verses[mv_id] = (book_id, chapter, verse_num)

        print(f"  MetaV verses: {len(metav_verses)}")

        # Load MetaV book ordering
        metav_books = {}  # metav_book_id -> book_name
        books_file = METAV_DIR / "Books.csv"
        with open(books_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                try:
                    bid = int(row[0])
                except ValueError:
                    continue
                metav_books[bid] = row[1].strip()

        # Map MetaV book names to our DB book names
        METAV_BOOK_MAP = {
            "Psalm": "Psalms",
            "Song of Solomon": "Song of Solomon",
            "Revelation of John": "Revelation",
            "I Samuel": "1 Samuel", "II Samuel": "2 Samuel",
            "I Kings": "1 Kings", "II Kings": "2 Kings",
            "I Chronicles": "1 Chronicles", "II Chronicles": "2 Chronicles",
            "I Corinthians": "1 Corinthians", "II Corinthians": "2 Corinthians",
            "I Thessalonians": "1 Thessalonians", "II Thessalonians": "2 Thessalonians",
            "I Timothy": "1 Timothy", "II Timothy": "2 Timothy",
            "I Peter": "1 Peter", "II Peter": "2 Peter",
            "I John": "1 John", "II John": "2 John",
            "III John": "3 John",
        }

        # Build our verse lookup
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM translations WHERE abbreviation = 'KJV'")
            kjv_id = cur.fetchone()[0]

            cur.execute("""
                SELECT b.name, ch.chapter_number, v.verse_number, v.id
                FROM verses v
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE v.translation_id = %s
            """, (kjv_id,))
            our_verses = {}
            for bname, ch, vn, vid in cur.fetchall():
                our_verses[(bname, ch, vn)] = vid

        # Build MetaV ID -> our verse ID mapping
        mv_to_ours = {}
        for mv_id, (book_id, chapter, verse_num) in metav_verses.items():
            book_name = metav_books.get(book_id, "")
            book_name = METAV_BOOK_MAP.get(book_name, book_name)
            our_vid = our_verses.get((book_name, chapter, verse_num))
            if our_vid:
                mv_to_ours[mv_id] = our_vid

        print(f"  Mapped {len(mv_to_ours)}/{len(metav_verses)} MetaV verses to our DB")

        # --- Load topic-verse index ---
        print("Loading topic-verse mappings...")
        index_rows = []
        skipped = 0
        with open(index_file, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) < 2:
                    continue
                try:
                    topic_id = int(row[0])
                    mv_verse_id = int(row[1])
                except ValueError:
                    continue

                our_vid = mv_to_ours.get(mv_verse_id)
                if our_vid is None:
                    skipped += 1
                    continue

                index_rows.append((topic_id, our_vid))

        # Bulk insert in batches
        batch_size = 1000
        loaded = 0
        for i in range(0, len(index_rows), batch_size):
            batch = index_rows[i:i + batch_size]
            bulk_insert(
                conn,
                table="nave_topic_verses",
                columns=["topic_id", "verse_id"],
                rows=batch,
                conflict_columns=["topic_id", "verse_id"],
            )
            loaded += len(batch)

        total_mappings = table_count(conn, "nave_topic_verses")
        print(f"  Mappings: processed {len(index_rows)}, skipped {skipped}, DB total: {total_mappings}")

        # --- Summary ---
        with conn.cursor() as cur:
            cur.execute("SELECT count(DISTINCT topic) FROM nave_topics")
            distinct_topics = cur.fetchone()[0]
            cur.execute("SELECT count(DISTINCT verse_id) FROM nave_topic_verses")
            distinct_verses = cur.fetchone()[0]

        print(f"\nSummary:")
        print(f"  Distinct top-level topics: {distinct_topics}")
        print(f"  Total topic entries (with subtopics): {total_topics}")
        print(f"  Topic-verse mappings: {total_mappings}")
        print(f"  Distinct verses referenced: {distinct_verses}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
