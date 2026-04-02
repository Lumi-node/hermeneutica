"""Load KJV verses from scrollmapper/bible_databases into the verses table.

Source: data/raw/bible_databases/sources/en/KJV/KJV.json
Format: {"books": [{"name": "Genesis", "chapters": [{"chapter": 1, "verses": [{"verse": 1, "text": "..."}]}]}]}

Usage: python -m etl.03_load_verses_kjv
"""

import json

from .config import RAW_DATA_DIR, BATCH_SIZE
from .db import get_connection, bulk_insert, table_count


KJV_PATH = RAW_DATA_DIR / "bible_databases" / "sources" / "en" / "KJV" / "KJV.json"

# Book name normalization: scrollmapper uses Roman numerals and some variations
BOOK_NAME_MAP = {
    "Psalm": "Psalms",
    "Song of Songs": "Song of Solomon",
    "Revelation of John": "Revelation",
    "I Samuel": "1 Samuel",
    "II Samuel": "2 Samuel",
    "I Kings": "1 Kings",
    "II Kings": "2 Kings",
    "I Chronicles": "1 Chronicles",
    "II Chronicles": "2 Chronicles",
    "I Corinthians": "1 Corinthians",
    "II Corinthians": "2 Corinthians",
    "I Thessalonians": "1 Thessalonians",
    "II Thessalonians": "2 Thessalonians",
    "I Timothy": "1 Timothy",
    "II Timothy": "2 Timothy",
    "I Peter": "1 Peter",
    "II Peter": "2 Peter",
    "I John": "1 John",
    "II John": "2 John",
    "III John": "3 John",
    "Sirach": None,  # skip deuterocanonical
}


def run():
    if not KJV_PATH.exists():
        print(f"ERROR: {KJV_PATH} not found. Run download_sources.sh first.")
        return

    conn = get_connection()
    try:
        # Get translation ID for KJV
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM translations WHERE abbreviation = 'KJV'")
            row = cur.fetchone()
            if not row:
                print("ERROR: KJV translation not found. Run 01_load_translations first.")
                return
            trans_id = row[0]

        # Build lookup: (book_name) -> {chapter_number: chapter_id}
        with conn.cursor() as cur:
            cur.execute("""
                SELECT b.name, ch.chapter_number, ch.id
                FROM chapters ch
                JOIN books b ON b.id = ch.book_id
            """)
            chapter_lookup = {}
            for book_name, ch_num, ch_id in cur.fetchall():
                chapter_lookup.setdefault(book_name, {})[ch_num] = ch_id

        # Load KJV JSON
        with open(KJV_PATH) as f:
            data = json.load(f)

        total_inserted = 0
        total_verses = 0
        batch = []

        for book in data["books"]:
            book_name = book["name"]
            # Normalize name
            book_name = BOOK_NAME_MAP.get(book_name, book_name)
            if book_name is None:
                continue  # skip deuterocanonical

            if book_name not in chapter_lookup:
                print(f"  WARNING: Book '{book['name']}' (normalized: '{book_name}') not found in DB, skipping")
                continue

            for chapter in book["chapters"]:
                ch_num = int(chapter["chapter"])
                ch_id = chapter_lookup[book_name].get(ch_num)
                if ch_id is None:
                    print(f"  WARNING: {book_name} chapter {ch_num} not found in DB, skipping")
                    continue

                for verse in chapter["verses"]:
                    v_num = int(verse["verse"])
                    text = verse["text"].strip()
                    if not text:
                        continue

                    batch.append((ch_id, v_num, trans_id, text))
                    total_verses += 1

                    if len(batch) >= BATCH_SIZE:
                        count = bulk_insert(
                            conn,
                            table="verses",
                            columns=["chapter_id", "verse_number", "translation_id", "text"],
                            rows=batch,
                            conflict_columns=["chapter_id", "verse_number", "translation_id"],
                        )
                        total_inserted += count
                        batch = []

        # Final batch
        if batch:
            count = bulk_insert(
                conn,
                table="verses",
                columns=["chapter_id", "verse_number", "translation_id", "text"],
                rows=batch,
                conflict_columns=["chapter_id", "verse_number", "translation_id"],
            )
            total_inserted += count

        db_count = table_count(conn, "verses")
        print(f"KJV: processed {total_verses} verses, DB total: {db_count}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
