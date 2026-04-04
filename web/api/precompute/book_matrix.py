"""Book cross-reference density matrix computation."""

import os
import sys
import json
import psycopg2

# Add project root to path for module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from etl.config import DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD

def main():
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public", "data", "book_matrix.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("Computing book cross-reference matrix...")

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=DB_HOST,
            port=DB_PORT,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        query = """
        SELECT b1.id, b2.id, COUNT(*), AVG(cr.relevance_score)
        FROM cross_references cr
        JOIN verses v1 ON v1.id = cr.source_verse_id
        JOIN chapters ch1 ON ch1.id = v1.chapter_id
        JOIN books b1 ON b1.id = ch1.book_id
        JOIN verses v2 ON v2.id = cr.target_verse_id
        JOIN chapters ch2 ON ch2.id = v2.chapter_id
        JOIN books b2 ON b2.id = ch2.book_id
        GROUP BY b1.id, b2.id
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "source": row[0],
                "target": row[1],
                "count": row[2],
                "avg_relevance": float(row[3]) if row[3] is not None else None
            })

        json_content = json.dumps(data, indent=2)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_content)

        file_size = os.path.getsize(output_path)
        print(f"Wrote {len(data)} edges to book_matrix.json ({file_size} bytes)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()