"""Load interlinear word alignments from STEPBible TAHOT/TAGNT into word_alignments table.

Parses tab-separated files where each data row has:
  Col 0: Reference (e.g. Gen.1.1#01=L)
  Col 1: Hebrew/Greek text
  Col 2: Transliteration
  Col 3: English gloss
  Col 4: Strong's numbers (disambiguated, root in {curly brackets})
  Col 5: Morphology code

Usage: python -m etl.06_load_word_alignments
"""

import re
from pathlib import Path

from .config import RAW_DATA_DIR, BATCH_SIZE
from .db import get_connection, bulk_insert, table_count


TAHOT_DIR = RAW_DATA_DIR / "STEPBible-Data" / "Translators Amalgamated OT+NT"

TAHOT_FILES = [
    "TAHOT Gen-Deu - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    "TAHOT Jos-Est - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    "TAHOT Job-Sng - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
    "TAHOT Isa-Mal - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt",
]

TAGNT_FILES = [
    "TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
    "TAGNT Act-Rev - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt",
]

# Book abbreviation mapping: STEPBible -> our DB book names
STEP_BOOK_MAP = {
    "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deu": "Deuteronomy", "Jos": "Joshua", "Jdg": "Judges", "Rut": "Ruth",
    "1Sa": "1 Samuel", "2Sa": "2 Samuel", "1Ki": "1 Kings", "2Ki": "2 Kings",
    "1Ch": "1 Chronicles", "2Ch": "2 Chronicles", "Ezr": "Ezra", "Neh": "Nehemiah",
    "Est": "Esther", "Job": "Job", "Psa": "Psalms", "Pro": "Proverbs",
    "Ecc": "Ecclesiastes", "Sng": "Song of Solomon", "Isa": "Isaiah",
    "Jer": "Jeremiah", "Lam": "Lamentations", "Eze": "Ezekiel", "Dan": "Daniel",
    "Hos": "Hosea", "Joe": "Joel", "Amo": "Amos", "Oba": "Obadiah",
    "Jon": "Jonah", "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk",
    "Zep": "Zephaniah", "Hag": "Haggai", "Zec": "Zechariah", "Mal": "Malachi",
    # NT
    "Mat": "Matthew", "Mar": "Mark", "Luk": "Luke", "Joh": "John",
    "Act": "Acts", "Rom": "Romans", "1Co": "1 Corinthians", "2Co": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Phi": "Philippians", "Col": "Colossians",
    "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy",
    "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon", "Heb": "Hebrews",
    "Jam": "James", "1Pe": "1 Peter", "2Pe": "2 Peter", "1Jo": "1 John",
    "2Jo": "2 John", "3Jo": "3 John", "Jud": "Jude", "Rev": "Revelation",
}

# Regex to parse reference: Book.Chapter.Verse#WordPosition=TextType
REF_PATTERN = re.compile(r"^(\w+)\.(\d+)\.(\d+)#(\d+)=")

# Regex to extract root Strong's number from dStrongs field
# Root is in {curly brackets}: e.g., H9003/{H7225G} -> H7225
ROOT_STRONGS_PATTERN = re.compile(r"\{([HG]\d+)")


def _extract_root_strongs(dstrongs: str) -> str:
    """Extract the primary root Strong's number from the dStrongs field."""
    match = ROOT_STRONGS_PATTERN.search(dstrongs)
    if match:
        # Remove trailing letter variants (H7225G -> H7225)
        raw = match.group(1)
        # Strip trailing alphabetic disambiguation
        return re.sub(r"[A-Z]$", "", raw)
    # Fallback: take first H/G number
    fallback = re.search(r"([HG]\d+)", dstrongs)
    if fallback:
        return re.sub(r"[A-Z]$", "", fallback.group(1))
    return ""


def _normalize_strongs(s: str) -> str:
    """Normalize to H0001 / G0001 format."""
    match = re.match(r"([HG])(\d+)", s)
    if match:
        prefix = match.group(1)
        num = int(match.group(2))
        return f"{prefix}{num:04d}"
    return s


def _is_data_line(line: str) -> bool:
    """Check if a line is a data row (starts with a book reference)."""
    if not line or line.startswith("\t") or line.startswith("=") or line.startswith("FIELD"):
        return False
    if line.startswith("TAHOT") or line.startswith("TAGNT") or line.startswith("(This"):
        return False
    if line.startswith("Translators") or line.startswith("This data"):
        return False
    return bool(REF_PATTERN.match(line.split("\t")[0].strip()))


def parse_tahot_file(filepath: Path) -> list[dict]:
    """Parse a TAHOT (Hebrew OT) file.

    Columns: Ref | Hebrew | Transliteration | English | dStrongs | Morphology | ...
    """
    records = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not _is_data_line(line):
                continue

            cols = line.split("\t")
            if len(cols) < 6:
                continue

            ref = cols[0].strip()
            match = REF_PATTERN.match(ref)
            if not match:
                continue

            book_abbrev = match.group(1)
            chapter = int(match.group(2))
            verse = int(match.group(3))
            word_pos = int(match.group(4))

            book_name = STEP_BOOK_MAP.get(book_abbrev)
            if not book_name:
                continue

            original_word = cols[1].strip().replace("\\", "").replace("/", "")
            transliteration = cols[2].strip() if len(cols) > 2 else ""
            english_gloss = cols[3].strip().replace("/", " ").strip() if len(cols) > 3 else ""
            dstrongs = cols[4].strip() if len(cols) > 4 else ""
            morphology = cols[5].strip() if len(cols) > 5 else ""

            if not english_gloss:
                english_gloss = "(untranslated)"

            root_strongs = _extract_root_strongs(dstrongs)
            if root_strongs:
                root_strongs = _normalize_strongs(root_strongs)
            else:
                continue

            records.append({
                "book_name": book_name,
                "chapter": chapter,
                "verse": verse,
                "word_position": word_pos,
                "original_word": original_word[:60],
                "strongs_number": root_strongs,
                "morphology_code": morphology[:30] if morphology else None,
                "english_gloss": english_gloss[:120],
                "transliteration": transliteration[:80] if transliteration else None,
            })

    return records


# Regex for TAGNT Strong's+morph field: G0976=N-NSF
TAGNT_STRONGS_PATTERN = re.compile(r"([GH]\d+\w?)=(.+)")


def parse_tagnt_file(filepath: Path) -> list[dict]:
    """Parse a TAGNT (Greek NT) file.

    Columns: Ref | Greek (translit) | English | dStrong=Morph | Lexical | Editions | ...
    """
    records = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not _is_data_line(line):
                continue

            cols = line.split("\t")
            if len(cols) < 4:
                continue

            ref = cols[0].strip()
            match = REF_PATTERN.match(ref)
            if not match:
                continue

            book_abbrev = match.group(1)
            chapter = int(match.group(2))
            verse = int(match.group(3))
            word_pos = int(match.group(4))

            book_name = STEP_BOOK_MAP.get(book_abbrev)
            if not book_name:
                continue

            # Col 1: Greek word, optionally with transliteration in parens
            greek_field = cols[1].strip() if len(cols) > 1 else ""
            translit_match = re.match(r"(.+?)\s*\((.+?)\)", greek_field)
            if translit_match:
                original_word = translit_match.group(1).strip()
                transliteration = translit_match.group(2).strip()
            else:
                original_word = greek_field
                transliteration = ""

            # Col 2: English gloss
            english_gloss = cols[2].strip() if len(cols) > 2 else ""
            english_gloss = english_gloss.replace("/", " ").strip()
            if not english_gloss:
                english_gloss = "(untranslated)"

            # Col 3: dStrong=Morphology (e.g., G0976=N-NSF)
            strongs_morph = cols[3].strip() if len(cols) > 3 else ""
            sm_match = TAGNT_STRONGS_PATTERN.match(strongs_morph)
            if not sm_match:
                continue

            raw_strongs = sm_match.group(1)
            morphology = sm_match.group(2)

            # Normalize Strong's (strip trailing disambiguation letters)
            strongs_number = _normalize_strongs(re.sub(r"[A-Z]$", "", raw_strongs))

            records.append({
                "book_name": book_name,
                "chapter": chapter,
                "verse": verse,
                "word_position": word_pos,
                "original_word": original_word[:60],
                "strongs_number": strongs_number,
                "morphology_code": morphology[:30] if morphology else None,
                "english_gloss": english_gloss[:120],
                "transliteration": transliteration[:80] if transliteration else None,
            })

    return records


def run():
    conn = get_connection()
    try:
        # Build verse lookup: (book_name, chapter, verse, translation_id) -> verse_id
        # For Hebrew, we need to use KJV verse IDs since we don't have Hebrew text loaded yet
        # The word alignments reference the same verse structure
        with conn.cursor() as cur:
            cur.execute("""
                SELECT b.name, ch.chapter_number, v.verse_number, v.translation_id, v.id
                FROM verses v
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
            """)
            verse_lookup = {}
            for book_name, ch_num, v_num, trans_id, v_id in cur.fetchall():
                verse_lookup[(book_name, ch_num, v_num, trans_id)] = v_id

        # Get KJV translation ID (we'll link alignments to KJV verses for now)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM translations WHERE abbreviation = 'KJV'")
            kjv_id = cur.fetchone()[0]

        total_loaded = 0
        total_skipped = 0

        # Process TAHOT (Hebrew OT)
        for filename in TAHOT_FILES:
            filepath = TAHOT_DIR / filename
            if not filepath.exists():
                print(f"  WARNING: {filepath} not found, skipping")
                continue

            print(f"  Parsing {filename}...")
            records = parse_tahot_file(filepath)
            print(f"    Parsed {len(records)} word records")

            batch = []
            skipped = 0
            for r in records:
                verse_id = verse_lookup.get((r["book_name"], r["chapter"], r["verse"], kjv_id))
                if verse_id is None:
                    skipped += 1
                    continue

                batch.append((
                    verse_id,
                    r["word_position"],
                    r["original_word"],
                    r["strongs_number"],
                    r["morphology_code"],
                    r["english_gloss"],
                    r["transliteration"],
                ))

                if len(batch) >= BATCH_SIZE:
                    bulk_insert(
                        conn,
                        table="word_alignments",
                        columns=["verse_id", "word_position", "original_word",
                                 "strongs_number", "morphology_code", "english_gloss",
                                 "transliteration"],
                        rows=batch,
                        conflict_columns=["verse_id", "word_position"],
                    )
                    total_loaded += len(batch)
                    batch = []

            if batch:
                bulk_insert(
                    conn,
                    table="word_alignments",
                    columns=["verse_id", "word_position", "original_word",
                             "strongs_number", "morphology_code", "english_gloss",
                             "transliteration"],
                    rows=batch,
                    conflict_columns=["verse_id", "word_position"],
                )
                total_loaded += len(batch)

            total_skipped += skipped
            if skipped:
                print(f"    Skipped {skipped} (verse not found in DB)")

        # Process TAGNT (Greek NT)
        for filename in TAGNT_FILES:
            filepath = TAHOT_DIR / filename
            if not filepath.exists():
                print(f"  WARNING: {filepath} not found, skipping")
                continue

            print(f"  Parsing {filename}...")
            records = parse_tagnt_file(filepath)
            print(f"    Parsed {len(records)} word records")

            batch = []
            skipped = 0
            for r in records:
                verse_id = verse_lookup.get((r["book_name"], r["chapter"], r["verse"], kjv_id))
                if verse_id is None:
                    skipped += 1
                    continue

                batch.append((
                    verse_id,
                    r["word_position"],
                    r["original_word"],
                    r["strongs_number"],
                    r["morphology_code"],
                    r["english_gloss"],
                    r["transliteration"],
                ))

                if len(batch) >= BATCH_SIZE:
                    bulk_insert(
                        conn,
                        table="word_alignments",
                        columns=["verse_id", "word_position", "original_word",
                                 "strongs_number", "morphology_code", "english_gloss",
                                 "transliteration"],
                        rows=batch,
                        conflict_columns=["verse_id", "word_position"],
                    )
                    total_loaded += len(batch)
                    batch = []

            if batch:
                bulk_insert(
                    conn,
                    table="word_alignments",
                    columns=["verse_id", "word_position", "original_word",
                             "strongs_number", "morphology_code", "english_gloss",
                             "transliteration"],
                    rows=batch,
                    conflict_columns=["verse_id", "word_position"],
                )
                total_loaded += len(batch)

            total_skipped += skipped
            if skipped:
                print(f"    Skipped {skipped} (verse not found in DB)")

        db_total = table_count(conn, "word_alignments")
        print(f"\nWord alignments: loaded {total_loaded}, skipped {total_skipped}, DB total: {db_total}")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
