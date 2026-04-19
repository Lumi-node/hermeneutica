"""Embed distilled_principles with bge-small-en-v1.5 for principle search.

Uses fastembed (ONNX, CPU-only) rather than Qwen3 so query-time embedding
can run inside the production API container without GPU. Produces 384-dim
vectors in the `principle_embeddings` table under a distinct model_name.

Idempotent: skips principles already embedded with this model.

Usage:
    python -m etl.11_embed_principles                 # embed all unembedded
    python -m etl.11_embed_principles --reset         # drop + recreate table, then embed all
    DATABASE_URL=postgres://... python -m etl.11_embed_principles   # against remote DB
"""

import argparse
import sys
import time

from etl.db import get_connection

MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


def reset_table(conn) -> None:
    """Drop and recreate principle_embeddings with the correct dim + HNSW index."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS principle_embeddings CASCADE;")
        cur.execute(f"""
            CREATE TABLE principle_embeddings (
                id              SERIAL       PRIMARY KEY,
                principle_id    INTEGER      NOT NULL REFERENCES distilled_principles(id) ON DELETE CASCADE,
                model_name      VARCHAR(80)  NOT NULL DEFAULT '{MODEL_NAME}',
                embedding       vector({EMBEDDING_DIM})  NOT NULL,
                created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
                UNIQUE (principle_id, model_name)
            );
        """)
        cur.execute("""
            CREATE INDEX idx_principle_emb_hnsw ON principle_embeddings
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
        """)
        conn.commit()
    print(f"  Recreated principle_embeddings as vector({EMBEDDING_DIM}).")


def embed_principles(conn, batch_size: int = 128) -> int:
    """Embed all unembedded distilled principles. Returns count inserted."""
    from fastembed import TextEmbedding  # imported here so --reset works without fastembed

    with conn.cursor() as cur:
        cur.execute("""
            SELECT dp.id, dp.principle_text
            FROM distilled_principles dp
            LEFT JOIN principle_embeddings pe
                ON pe.principle_id = dp.id AND pe.model_name = %s
            WHERE pe.id IS NULL
            ORDER BY dp.id
        """, (MODEL_NAME,))
        rows = cur.fetchall()

    if not rows:
        print("  All principles already embedded.")
        return 0

    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]

    print(f"  Loading {MODEL_NAME}...")
    model = TextEmbedding(MODEL_NAME)

    print(f"  Embedding {len(texts)} principles (batch_size={batch_size})...")
    t0 = time.time()
    vectors = list(model.embed(texts, batch_size=batch_size))
    print(f"  Encoded in {time.time() - t0:.1f}s.")

    inserted = 0
    with conn.cursor() as cur:
        for pid, vec in zip(ids, vectors):
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            cur.execute(
                """INSERT INTO principle_embeddings (principle_id, model_name, embedding)
                   VALUES (%s, %s, %s::vector)
                   ON CONFLICT (principle_id, model_name) DO NOTHING""",
                (pid, MODEL_NAME, vec_str),
            )
            inserted += 1
            if inserted % 200 == 0:
                print(f"    Stored {inserted}/{len(ids)}...")
        conn.commit()
    print(f"  Stored {inserted}/{len(ids)} principle embeddings.")
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed distilled principles for semantic search.")
    parser.add_argument("--reset", action="store_true",
                        help="Drop + recreate principle_embeddings before embedding (needed if dim changed).")
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()

    conn = get_connection()
    try:
        if args.reset:
            reset_table(conn)
        embed_principles(conn, batch_size=args.batch_size)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM principle_embeddings WHERE model_name = %s",
                (MODEL_NAME,),
            )
            total = cur.fetchone()[0]
        print(f"\n  principle_embeddings ({MODEL_NAME}): {total:,} rows")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
