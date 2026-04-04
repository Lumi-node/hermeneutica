import os
import sys
import time
import numpy as np
import psycopg2
import psycopg2.extras
from umap import UMAP
from typing import List, Tuple

# Add project root to path for module resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from etl.config import DB_NAME, DB_USER, DB_HOST, DB_PORT, DB_PASSWORD

# Constants
MODEL_NAME = 'Qwen/Qwen3-Embedding-8B'
EXPECTED_VERSE_COUNT = 31102
TABLE_NAME = 'verse_embeddings'
UMAP_TABLE_NAME = 'umap_verse_coords'


def get_db_connection():
    """Establish and return a database connection."""
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
        print(f"❌ Failed to connect to database: {e}")
        return None


def check_existing_umap_results(conn: psycopg2.extensions.connection) -> bool:
    """Check if UMAP results already exist for the target model and count."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {UMAP_TABLE_NAME} WHERE model_name = %s",
                (MODEL_NAME,)
            )
            count = cur.fetchone()[0]
            return count == EXPECTED_VERSE_COUNT
    except Exception as e:
        print(f"⚠️ Warning: Error checking existing UMAP results: {e}")
        return False


def extract_embeddings(conn: psycopg2.extensions.connection) -> List[Tuple[str, np.ndarray]]:
    """Extract verse_id and parsed embeddings from database."""
    print("🔄 Extracting verse embeddings from database...")
    embeddings = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT verse_id, embedding FROM {TABLE_NAME} WHERE model_name = %s",
                (MODEL_NAME,)
            )
            rows = cur.fetchall()
            print(f"✅ Extracted {len(rows)} embeddings for model '{MODEL_NAME}'")
            for verse_id, embedding_text in rows:
                try:
                    # Parse pgvector string format: "[1.0,2.0,...]" -> remove brackets and split
                    vec = np.fromstring(embedding_text[1:-1], sep=',')
                    embeddings.append((verse_id, vec))
                except Exception as e:
                    print(f"❌ Failed to parse embedding for verse_id {verse_id}: {e}")
        return embeddings
    except Exception as e:
        print(f"❌ Failed to extract embeddings: {e}")
        return []


def run_umap_reduction(vectors: List[np.ndarray]) -> np.ndarray:
    """Run UMAP dimensionality reduction on the input vectors."""
    print("🔄 Running UMAP reduction (n_components=3, n_neighbors=30, min_dist=0.1, metric='cosine')...")
    try:
        reducer = UMAP(
            n_components=3,
            n_neighbors=30,
            min_dist=0.1,
            metric='cosine',
            random_state=42,
            verbose=True
        )
        coords = reducer.fit_transform(vectors)
        print("✅ UMAP reduction completed")
        return coords
    except Exception as e:
        print(f"❌ UMAP reduction failed: {e}")
        raise


def insert_umap_results(conn: psycopg2.extensions.connection, data: List[Tuple]):
    """Insert or update (UPSERT) UMAP coordinates into the database."""
    print("🔄 Inserting UMAP coordinates into database...")
    try:
        with conn.cursor() as cur:
            # Use psycopg2.extras.execute_values for bulk insert with UPSERT
            sql = f"""
                INSERT INTO {UMAP_TABLE_NAME} (verse_id, x, y, z, model_name)
                VALUES %s
                ON CONFLICT (verse_id)
                DO UPDATE SET x = EXCLUDED.x, y = EXCLUDED.y, z = EXCLUDED.z, model_name = EXCLUDED.model_name
            """
            psycopg2.extras.execute_values(cur, sql, data, page_size=1000)
            conn.commit()
        print(f"✅ Inserted/updated {len(data)} UMAP coordinates")
    except Exception as e:
        print(f"❌ Failed to insert UMAP results: {e}")
        conn.rollback()
        raise


def main():
    start_time = time.time()
    conn = get_db_connection()
    if not conn:
        print("Script aborted due to database connection failure.")
        sys.exit(1)

    try:
        # Idempotency check
        if check_existing_umap_results(conn):
            print(f"UMAP results for '{MODEL_NAME}' already exist with {EXPECTED_VERSE_COUNT} entries. Skipping computation.")
            return

        print(f"\n{'='*70}")
        print(f"UMAP Precomputation for Verse Embeddings")
        print(f"{'='*70}\n")

        # Step 1: Extract embeddings
        embeddings = extract_embeddings(conn)
        if len(embeddings) != EXPECTED_VERSE_COUNT:
            print(f"Warning: Expected {EXPECTED_VERSE_COUNT} verses, but got {len(embeddings)}")

        if not embeddings:
            print("No embeddings extracted. Aborting.")
            sys.exit(1)

        # Separate verse_ids and vectors
        verse_ids, vectors = zip(*embeddings)
        vectors = np.array(vectors)
        print(f"Vector shape: {vectors.shape}")

        # Step 2: Run UMAP
        coords = run_umap_reduction(vectors)
        print(f"Coordinates shape: {coords.shape}")

        # Step 3: Prepare data for insertion
        upsert_data = [
            (verse_id, float(x), float(y), float(z), MODEL_NAME)
            for verse_id, (x, y, z) in zip(verse_ids, coords)
        ]

        # Step 4: Insert into database
        insert_umap_results(conn, upsert_data)

        elapsed = time.time() - start_time
        print(f"\nUMAP precomputation completed successfully in {elapsed:.1f}s.")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()