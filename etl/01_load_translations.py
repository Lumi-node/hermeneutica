"""Seed the translations table.

Usage: python -m etl.01_load_translations
"""

from .db import get_connection, bulk_insert


TRANSLATIONS = [
    ("KJV", "King James Version", "eng", "public_domain",
     "https://github.com/scrollmapper/bible_databases"),
    ("HEB", "Westminster Leningrad Codex (Hebrew)", "heb", "public_domain",
     "https://github.com/openscriptures/morphhb"),
    ("GRK", "Open Greek New Testament", "grc", "CC BY-SA 4.0",
     "https://github.com/eliranwong/OpenGNT"),
]


def run():
    conn = get_connection()
    try:
        count = bulk_insert(
            conn,
            table="translations",
            columns=["abbreviation", "name", "language", "license", "source_url"],
            rows=TRANSLATIONS,
            conflict_columns=["abbreviation"],
        )
        print(f"Translations: inserted {count}, total {len(TRANSLATIONS)} defined")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
