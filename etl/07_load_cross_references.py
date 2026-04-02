"""Load cross-references from scrollmapper/bible_databases into cross_references table.

Source: data/raw/bible_databases/sources/extras/cross_references_*.json
Format: {"cross_references": [{"from_verse": {"book": ..., "chapter": N, "verse": N},
         "to_verse": [{"book": ..., "chapter": N, "verse_start": N, "verse_end": N}], "votes": N}]}

Usage: python -m etl.07_load_cross_references
"""

import json
from pathlib import Path

from .config import RAW_DATA_DIR, BATCH_SIZE
from .db import get_connection, bulk_insert, table_count


XREF_DIR = RAW_DATA_DIR / "bible_databases" / "sources" / "extras"

# Book name normalization (scrollmapper -> our DB)
XREF_BOOK_MAP = {
    "Psalm": "Psalms",
    "Song of Songs": "Song of Solomon",
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


def run():
    conn = get_connection()
    try:
        # Build verse lookup: (book_name, chapter, verse) -> verse_id (KJV)
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
            verse_lookup = {}
            for book_name, ch_num, v_num, v_id in cur.fetchall():
                verse_lookup[(book_name, ch_num, v_num)] = v_id

        # Find max votes across all files (for normalization)
        max_votes = 1
        all_refs = []

        for i in range(7):
            filepath = XREF_DIR / f"cross_references_{i}.json"
            if not filepath.exists():
                continue
            with open(filepath) as f:
                data = json.load(f)
            refs = data.get("cross_references", [])
            all_refs.extend(refs)
            for ref in refs:
                votes = ref.get("votes", 0)
                if votes > max_votes:
                    max_votes = votes

        print(f"Loaded {len(all_refs)} cross-reference entries from JSON")
        print(f"Max votes: {max_votes}")

        batch = []
        total_loaded = 0
        skipped = 0

        for ref in all_refs:
            from_v = ref.get("from_verse", {})
            from_book = from_v.get("book", "")
            from_book = XREF_BOOK_MAP.get(from_book, from_book)
            from_ch = from_v.get("chapter", 0)
            from_verse = from_v.get("verse", 0)
            votes = ref.get("votes", 0)
            relevance = max(0.0, min(1.0, votes / max_votes))

            source_id = verse_lookup.get((from_book, from_ch, from_verse))
            if source_id is None:
                skipped += 1
                continue

            source_ref = f"{from_book[:3]}.{from_ch}.{from_verse}"

            to_verses = ref.get("to_verse", [])
            for tv in to_verses:
                to_book = tv.get("book", "")
                to_book = XREF_BOOK_MAP.get(to_book, to_book)
                to_ch = tv.get("chapter", 0)
                to_vs = tv.get("verse_start", 0)

                target_id = verse_lookup.get((to_book, to_ch, to_vs))
                if target_id is None:
                    skipped += 1
                    continue

                target_ref = f"{to_book[:3]}.{to_ch}.{to_vs}"

                batch.append((
                    source_id,
                    target_id,
                    round(relevance, 4),
                    "thematic",
                    source_ref[:20],
                    target_ref[:20],
                ))

                if len(batch) >= BATCH_SIZE:
                    bulk_insert(
                        conn,
                        table="cross_references",
                        columns=["source_verse_id", "target_verse_id", "relevance_score",
                                 "ref_type", "source_ref", "target_ref"],
                        rows=batch,
                        conflict_columns=["source_verse_id", "target_verse_id"],
                    )
                    total_loaded += len(batch)
                    batch = []

        if batch:
            bulk_insert(
                conn,
                table="cross_references",
                columns=["source_verse_id", "target_verse_id", "relevance_score",
                          "ref_type", "source_ref", "target_ref"],
                rows=batch,
                conflict_columns=["source_verse_id", "target_verse_id"],
            )
            total_loaded += len(batch)

        db_total = table_count(conn, "cross_references")
        print(f"\nCross-references: processed {total_loaded}, skipped {skipped}, DB total: {db_total}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
