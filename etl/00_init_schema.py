"""Initialize the bible_research database schema.

Usage: python -m etl.00_init_schema
"""

from pathlib import Path
from .db import get_connection
from .config import SQL_DIR


def run():
    schema_file = SQL_DIR / "schema.sql"
    if not schema_file.exists():
        print(f"ERROR: {schema_file} not found")
        return

    ddl = schema_file.read_text()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
        print("Schema initialized successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
