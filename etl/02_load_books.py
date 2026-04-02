"""Seed the books and chapters tables with the 66-book Protestant canon.

Usage: python -m etl.02_load_books
"""

from .db import get_connection, bulk_insert, table_count


# (name, abbreviation, testament, genre, book_order, chapter_count)
BOOKS = [
    # --- Old Testament ---
    ("Genesis",        "Gen",  "OT", "Law",       1,  50),
    ("Exodus",         "Exo",  "OT", "Law",       2,  40),
    ("Leviticus",      "Lev",  "OT", "Law",       3,  27),
    ("Numbers",        "Num",  "OT", "Law",       4,  36),
    ("Deuteronomy",    "Deu",  "OT", "Law",       5,  34),
    ("Joshua",         "Jos",  "OT", "History",   6,  24),
    ("Judges",         "Jdg",  "OT", "History",   7,  21),
    ("Ruth",           "Rut",  "OT", "History",   8,   4),
    ("1 Samuel",       "1Sa",  "OT", "History",   9,  31),
    ("2 Samuel",       "2Sa",  "OT", "History",  10,  24),
    ("1 Kings",        "1Ki",  "OT", "History",  11,  22),
    ("2 Kings",        "2Ki",  "OT", "History",  12,  25),
    ("1 Chronicles",   "1Ch",  "OT", "History",  13,  29),
    ("2 Chronicles",   "2Ch",  "OT", "History",  14,  36),
    ("Ezra",           "Ezr",  "OT", "History",  15,  10),
    ("Nehemiah",       "Neh",  "OT", "History",  16,  13),
    ("Esther",         "Est",  "OT", "History",  17,  10),
    ("Job",            "Job",  "OT", "Wisdom",   18,  42),
    ("Psalms",         "Psa",  "OT", "Wisdom",   19, 150),
    ("Proverbs",       "Pro",  "OT", "Wisdom",   20,  31),
    ("Ecclesiastes",   "Ecc",  "OT", "Wisdom",   21,  12),
    ("Song of Solomon","Sol",  "OT", "Wisdom",   22,   8),
    ("Isaiah",         "Isa",  "OT", "Prophecy", 23,  66),
    ("Jeremiah",       "Jer",  "OT", "Prophecy", 24,  52),
    ("Lamentations",   "Lam",  "OT", "Prophecy", 25,   5),
    ("Ezekiel",        "Eze",  "OT", "Prophecy", 26,  48),
    ("Daniel",         "Dan",  "OT", "Prophecy", 27,  12),
    ("Hosea",          "Hos",  "OT", "Prophecy", 28,  14),
    ("Joel",           "Joe",  "OT", "Prophecy", 29,   3),
    ("Amos",           "Amo",  "OT", "Prophecy", 30,   9),
    ("Obadiah",        "Oba",  "OT", "Prophecy", 31,   1),
    ("Jonah",          "Jon",  "OT", "Prophecy", 32,   4),
    ("Micah",          "Mic",  "OT", "Prophecy", 33,   7),
    ("Nahum",          "Nah",  "OT", "Prophecy", 34,   3),
    ("Habakkuk",       "Hab",  "OT", "Prophecy", 35,   3),
    ("Zephaniah",      "Zep",  "OT", "Prophecy", 36,   3),
    ("Haggai",         "Hag",  "OT", "Prophecy", 37,   2),
    ("Zechariah",      "Zec",  "OT", "Prophecy", 38,  14),
    ("Malachi",        "Mal",  "OT", "Prophecy", 39,   4),
    # --- New Testament ---
    ("Matthew",        "Mat",  "NT", "Gospel",   40,  28),
    ("Mark",           "Mar",  "NT", "Gospel",   41,  16),
    ("Luke",           "Luk",  "NT", "Gospel",   42,  24),
    ("John",           "Joh",  "NT", "Gospel",   43,  21),
    ("Acts",           "Act",  "NT", "History",  44,  28),
    ("Romans",         "Rom",  "NT", "Epistle",  45,  16),
    ("1 Corinthians",  "1Co",  "NT", "Epistle",  46,  16),
    ("2 Corinthians",  "2Co",  "NT", "Epistle",  47,  13),
    ("Galatians",      "Gal",  "NT", "Epistle",  48,   6),
    ("Ephesians",      "Eph",  "NT", "Epistle",  49,   6),
    ("Philippians",    "Phi",  "NT", "Epistle",  50,   4),
    ("Colossians",     "Col",  "NT", "Epistle",  51,   4),
    ("1 Thessalonians","1Th",  "NT", "Epistle",  52,   5),
    ("2 Thessalonians","2Th",  "NT", "Epistle",  53,   3),
    ("1 Timothy",      "1Ti",  "NT", "Epistle",  54,   6),
    ("2 Timothy",      "2Ti",  "NT", "Epistle",  55,   4),
    ("Titus",          "Tit",  "NT", "Epistle",  56,   3),
    ("Philemon",       "Phm",  "NT", "Epistle",  57,   1),
    ("Hebrews",        "Heb",  "NT", "Epistle",  58,  13),
    ("James",          "Jam",  "NT", "Epistle",  59,   5),
    ("1 Peter",        "1Pe",  "NT", "Epistle",  60,   5),
    ("2 Peter",        "2Pe",  "NT", "Epistle",  61,   3),
    ("1 John",         "1Jo",  "NT", "Epistle",  62,   5),
    ("2 John",         "2Jo",  "NT", "Epistle",  63,   1),
    ("3 John",         "3Jo",  "NT", "Epistle",  64,   1),
    ("Jude",           "Jud",  "NT", "Epistle",  65,   1),
    ("Revelation",     "Rev",  "NT", "Apocalyptic", 66, 22),
]


def run():
    conn = get_connection()
    try:
        # Insert books
        book_count = bulk_insert(
            conn,
            table="books",
            columns=["name", "abbreviation", "testament", "genre", "book_order", "chapter_count"],
            rows=BOOKS,
            conflict_columns=["name"],
        )
        print(f"Books: inserted {book_count} (total defined: {len(BOOKS)})")

        # Build chapter rows: need book IDs
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, chapter_count FROM books ORDER BY book_order")
            db_books = cur.fetchall()

        chapter_rows = []
        for book_id, book_name, ch_count in db_books:
            for ch_num in range(1, ch_count + 1):
                chapter_rows.append((book_id, ch_num))

        ch_count = bulk_insert(
            conn,
            table="chapters",
            columns=["book_id", "chapter_number"],
            rows=chapter_rows,
            conflict_columns=["book_id", "chapter_number"],
        )

        total_chapters = table_count(conn, "chapters")
        print(f"Chapters: inserted {ch_count} (total in DB: {total_chapters})")

    finally:
        conn.close()


if __name__ == "__main__":
    run()
