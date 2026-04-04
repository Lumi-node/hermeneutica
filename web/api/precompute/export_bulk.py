"""Binary export for frontend: verses_bulk.bin and strongs_bulk.bin."""

import os
import sys
import struct
import psycopg2
from pathlib import Path

# Add project root to path for module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from etl.config import DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD

# Define genre mapping
GENRE_TO_ID = {
    'Law': 0,
    'History': 1,
    'Wisdom': 2,
    'Prophecy': 3,
    'Gospel': 4,
    'Epistle': 5,
    'Apocalyptic': 6
}

# Define part-of-speech mapping
POS_TO_ID = {
    'noun': 0,
    'verb': 1,
    'adjective': 2,
    'adverb': 3,
    'pronoun': 4,
}

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "public" / "data"


def get_db_connection():
    """Establish database connection."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return None


def export_verses_bulk():
    """Export all verse data to binary format."""
    print("\nExporting verses to binary format...")

    conn = get_db_connection()
    if not conn:
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            query = """
            SELECT v.id as verse_id, uv.x, uv.y, uv.z,
                   b.id as book_id, ch.chapter_number, v.verse_number,
                   b.testament, b.genre,
                   COALESCE((SELECT MAX(pes.relevance_score) FROM passage_ethics_scores pes
                             JOIN passage_classifications pc ON pc.id = pes.classification_id
                             WHERE pc.chapter_id = ch.id), 0.0) as ethics_max,
                   (SELECT COUNT(*) FROM cross_references cr WHERE cr.source_verse_id = v.id) as xref_count
            FROM verses v
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            JOIN umap_verse_coords uv ON uv.verse_id = v.id
            WHERE v.translation_id = 1
            ORDER BY v.id
            """
            cur.execute(query)
            rows = cur.fetchall()

        print(f"Retrieved {len(rows)} verse records")

        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "verses_bulk.bin"

        # Pack data: 28-byte records
        # Format: <i ffff B B H H B B f
        # verse_id(4) x(4) y(4) z(4) book_id(1) chapter_number(1) verse_number(2)
        # cross_ref_count(2) testament(1) genre_id(1) ethics_max(4)
        data = bytearray()
        for row in rows:
            (verse_id, x, y, z, book_id, chapter_number, verse_number,
             testament, genre, ethics_max, xref_count) = row

            testament_id = 0 if testament == 'OT' else 1
            genre_id = GENRE_TO_ID.get(genre, 5)

            # Pack as: int32 float32 float32 float32 uint8 uint8 uint16 uint16 uint8 uint8 float32
            record = struct.pack('<ifffBBHHBBf',
                int(verse_id), float(x), float(y), float(z),
                int(book_id), int(chapter_number), int(verse_number),
                int(xref_count), int(testament_id), int(genre_id), float(ethics_max)
            )
            data.extend(record)

        with open(output_path, 'wb') as f:
            f.write(data)

        print(f"Wrote verses_bulk.bin ({len(data)} bytes, {len(rows)} records)")
        return True

    except Exception as e:
        print(f"Error exporting verses: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def export_strongs_bulk():
    """Export all Strong's data to binary format."""
    print("\nExporting Strong's entries to binary format...")

    conn = get_db_connection()
    if not conn:
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            query = """
            SELECT se.id as strongs_id, usc.x, usc.y, usc.z,
                   CASE WHEN se.language = 'heb' THEN 0 ELSE 1 END as language,
                   CASE LOWER(se.part_of_speech)
                       WHEN 'noun' THEN 0
                       WHEN 'verb' THEN 1
                       WHEN 'adjective' THEN 2
                       WHEN 'adverb' THEN 3
                       WHEN 'pronoun' THEN 4
                       ELSE 5
                   END as pos_id,
                   COALESCE((SELECT COUNT(*) FROM word_alignments wa WHERE wa.strongs_number = se.strongs_number), 0) as usage_count,
                   CASE WHEN EXISTS(SELECT 1 FROM word_alignments wa WHERE wa.strongs_number = se.strongs_number LIMIT 1) THEN 1 ELSE 0 END as has_twot
            FROM strongs_entries se
            JOIN umap_strongs_coords usc ON usc.strongs_id = se.id
            ORDER BY se.id
            """
            cur.execute(query)
            rows = cur.fetchall()

        print(f"Retrieved {len(rows)} Strong's records")

        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / "strongs_bulk.bin"

        # Pack data: 24-byte records
        # Format: <i ffff B B H B xxx
        # strongs_id(4) x(4) y(4) z(4) language(1) pos_id(1) usage_count(2) has_twot(1) reserved(3)
        data = bytearray()
        for row in rows:
            (strongs_id, x, y, z, language, pos_id, usage_count, has_twot) = row

            # Pack as: int32 float32 float32 float32 uint8 uint8 uint16 uint8 + 3 padding bytes
            record = struct.pack('<ifffBBHBxxx',
                int(strongs_id), float(x), float(y), float(z),
                int(language), int(pos_id), int(usage_count), int(has_twot)
            )
            data.extend(record)

        with open(output_path, 'wb') as f:
            f.write(data)

        print(f"Wrote strongs_bulk.bin ({len(data)} bytes, {len(rows)} records)")
        return True

    except Exception as e:
        print(f"Error exporting Strong's entries: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


def main():
    print("\n" + "="*70)
    print("Binary Export Pipeline for Hermeneutica Explorer")
    print("="*70)

    try:
        success_verses = export_verses_bulk()
        success_strongs = export_strongs_bulk()

        if success_verses and success_strongs:
            print("\n" + "="*70)
            print("Export completed successfully!")
            print("="*70 + "\n")
        else:
            print("\nWarning: Some exports did not complete successfully")
            sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()