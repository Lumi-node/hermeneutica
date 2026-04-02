"""Database connection and idempotent helper functions for ETL."""

import psycopg2
import psycopg2.extras

from .config import DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD


def get_connection(dbname: str = DB_NAME):
    """Get a psycopg2 connection to the database."""
    return psycopg2.connect(
        dbname=dbname,
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT,
        password=DB_PASSWORD,
    )


def upsert_row(
    conn, table: str, data: dict,
    conflict_columns: list[str],
    update_on_conflict: bool = False,
) -> int | None:
    """Insert a row, handling conflicts.

    Args:
        conn: psycopg2 connection.
        table: Table name.
        data: Column-value dict.
        conflict_columns: Columns forming the unique constraint.
        update_on_conflict: If True, update non-conflict columns on conflict.

    Returns:
        The id of the inserted/existing row, or None.
    """
    columns = list(data.keys())
    values = list(data.values())
    placeholders = ", ".join(["%s"] * len(values))
    col_list = ", ".join(columns)
    conflict_list = ", ".join(conflict_columns)

    if update_on_conflict:
        update_cols = [c for c in columns if c not in conflict_columns]
        if update_cols:
            update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
            sql = (
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                f"ON CONFLICT ({conflict_list}) DO UPDATE SET {update_clause} "
                f"RETURNING id"
            )
        else:
            sql = (
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                f"ON CONFLICT ({conflict_list}) DO NOTHING RETURNING id"
            )
    else:
        sql = (
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_list}) DO NOTHING RETURNING id"
        )

    with conn.cursor() as cur:
        cur.execute(sql, values)
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None


def bulk_insert(
    conn, table: str, columns: list[str], rows: list[tuple],
    on_conflict: str = "DO NOTHING",
    conflict_columns: list[str] | None = None,
) -> int:
    """Bulk insert rows using execute_values for performance.

    Args:
        conn: psycopg2 connection.
        table: Table name.
        columns: Column names.
        rows: List of value tuples.
        on_conflict: Conflict clause ('DO NOTHING' or custom).
        conflict_columns: Required if on_conflict is not 'DO NOTHING'.

    Returns:
        Number of rows inserted.
    """
    if not rows:
        return 0

    col_list = ", ".join(columns)
    template = "(" + ", ".join(["%s"] * len(columns)) + ")"

    if conflict_columns and on_conflict != "DO NOTHING":
        conflict_list = ", ".join(conflict_columns)
        sql = f"INSERT INTO {table} ({col_list}) VALUES %s ON CONFLICT ({conflict_list}) {on_conflict}"
    elif conflict_columns:
        conflict_list = ", ".join(conflict_columns)
        sql = f"INSERT INTO {table} ({col_list}) VALUES %s ON CONFLICT ({conflict_list}) DO NOTHING"
    else:
        sql = f"INSERT INTO {table} ({col_list}) VALUES %s ON CONFLICT DO NOTHING"

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows, template=template, page_size=500)
        count = cur.rowcount
        conn.commit()
        return count


def get_or_create_id(conn, table: str, unique_cols: dict, extra_data: dict | None = None) -> int:
    """Get existing row ID or insert and return new ID.

    Args:
        conn: psycopg2 connection.
        table: Table name.
        unique_cols: Dict of column=value forming the unique lookup.
        extra_data: Additional columns to set on insert (not used for lookup).

    Returns:
        The row's id.
    """
    # Try select first
    where_clause = " AND ".join(f"{k} = %s" for k in unique_cols)
    with conn.cursor() as cur:
        cur.execute(f"SELECT id FROM {table} WHERE {where_clause}", list(unique_cols.values()))
        row = cur.fetchone()
        if row:
            return row[0]

    # Insert
    data = {**unique_cols, **(extra_data or {})}
    columns = list(data.keys())
    values = list(data.values())
    placeholders = ", ".join(["%s"] * len(values))
    col_list = ", ".join(columns)
    conflict_list = ", ".join(unique_cols.keys())

    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_list}) DO NOTHING RETURNING id",
            values,
        )
        row = cur.fetchone()
        if row:
            conn.commit()
            return row[0]
        # Race condition: another process inserted between SELECT and INSERT
        conn.commit()
        cur.execute(f"SELECT id FROM {table} WHERE {where_clause}", list(unique_cols.values()))
        return cur.fetchone()[0]


def table_count(conn, table: str) -> int:
    """Get row count for a table."""
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table}")
        return cur.fetchone()[0]
