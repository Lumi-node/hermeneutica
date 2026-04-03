"""
Embedding engine for Bible research.

Generates 2000-dim embeddings using Qwen/Qwen3-Embedding-8B on GPU,
with Matryoshka truncation from native 4096 dims to pgvector HNSW max (2000).
Supports instruction prefixes for retrieval-quality embeddings.

Multilingual: embeds English, Hebrew, and Greek into a shared vector space.

Usage:
    python -m src.embeddings                    # embed everything
    python -m src.embeddings --verses           # verses only
    python -m src.embeddings --strongs          # Strong's definitions only
    python -m src.embeddings --search "love"    # semantic search demo
"""

import argparse
import sys
import torch
import numpy as np

from sentence_transformers import SentenceTransformer

sys.path.insert(0, ".")
from etl.config import EMBEDDING_MODEL, EMBEDDING_DIM
from etl.db import get_connection, table_count


class EmbeddingEngine:
    """Batch embedding engine with GPU acceleration and pgvector storage.

    Uses Qwen3-Embedding-8B (8B params, 4096 native dims) with Matryoshka
    truncation to 2000 dims for pgvector HNSW compatibility.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL, device: str = "cuda", batch_size: int = 8):
        print(f"Loading model: {model_name} on {device}...")
        self.model = SentenceTransformer(
            model_name, device=device, trust_remote_code=True,
            model_kwargs={"torch_dtype": torch.float16},
        )
        self.model_name = model_name
        self.batch_size = batch_size
        self.truncate_dim = EMBEDDING_DIM  # Matryoshka truncation

    def encode(self, texts: list[str], instruction: str = "") -> np.ndarray:
        """Encode texts to normalized vectors, truncated to EMBEDDING_DIM.

        Args:
            texts: List of texts to embed.
            instruction: Optional instruction prefix for retrieval tasks.
                         Qwen3-Embedding supports task-specific instructions.
        """
        if instruction:
            texts = [instruction + t for t in texts]

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        # Matryoshka truncation + re-normalize
        if embeddings.shape[1] > self.truncate_dim:
            embeddings = embeddings[:, :self.truncate_dim]
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = embeddings / norms

        return embeddings

    def embed_verses(self, conn, translation: str = "KJV"):
        """Embed all verses for a given translation."""
        with conn.cursor() as cur:
            # Find verses not yet embedded
            cur.execute("""
                SELECT v.id, v.text
                FROM verses v
                JOIN translations t ON t.id = v.translation_id
                LEFT JOIN verse_embeddings ve ON ve.verse_id = v.id AND ve.model_name = %s
                WHERE t.abbreviation = %s AND ve.id IS NULL
                ORDER BY v.id
            """, (self.model_name, translation))
            rows = cur.fetchall()

        if not rows:
            print(f"  All {translation} verses already embedded.")
            return

        ids = [r[0] for r in rows]
        texts = [r[1] for r in rows]
        print(f"  Embedding {len(texts)} {translation} verses...")

        embeddings = self.encode(texts)
        self._store_embeddings(conn, "verse_embeddings", "verse_id", ids, embeddings)
        print(f"  Stored {len(ids)} verse embeddings.")

    def embed_strongs(self, conn):
        """Embed all Strong's definitions."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT se.id,
                       se.transliteration || ': ' ||
                       COALESCE(se.gloss, '') || '. ' ||
                       COALESCE(se.root_definition, '') as text
                FROM strongs_entries se
                LEFT JOIN strongs_embeddings sem ON sem.strongs_id = se.id AND sem.model_name = %s
                WHERE sem.id IS NULL
                ORDER BY se.id
            """, (self.model_name,))
            rows = cur.fetchall()

        if not rows:
            print("  All Strong's entries already embedded.")
            return

        ids = [r[0] for r in rows]
        texts = [r[1] for r in rows]
        print(f"  Embedding {len(texts)} Strong's definitions...")

        embeddings = self.encode(texts)
        self._store_embeddings(conn, "strongs_embeddings", "strongs_id", ids, embeddings)
        print(f"  Stored {len(ids)} Strong's embeddings.")

    def embed_chapters(self, conn, translation: str = "KJV"):
        """Embed chapters by concatenating their verses."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ch.id, t.id as trans_id,
                       string_agg(v.text, ' ' ORDER BY v.verse_number) as chapter_text
                FROM chapters ch
                JOIN verses v ON v.chapter_id = ch.id
                JOIN translations t ON t.id = v.translation_id
                LEFT JOIN chapter_embeddings ce ON ce.chapter_id = ch.id
                    AND ce.translation_id = t.id AND ce.model_name = %s
                WHERE t.abbreviation = %s AND ce.id IS NULL
                GROUP BY ch.id, t.id
                ORDER BY ch.id
            """, (self.model_name, translation))
            rows = cur.fetchall()

        if not rows:
            print(f"  All {translation} chapters already embedded.")
            return

        chapter_ids = [r[0] for r in rows]
        trans_ids = [r[1] for r in rows]
        texts = [r[2][:2048] for r in rows]  # truncate to model max
        print(f"  Embedding {len(texts)} {translation} chapters...")

        embeddings = self.encode(texts)

        # Store with translation_id
        values = []
        for i, emb in enumerate(embeddings):
            vec_str = "[" + ",".join(f"{x:.6f}" for x in emb) + "]"
            values.append((chapter_ids[i], trans_ids[i], self.model_name, vec_str))

        with conn.cursor() as cur:
            from psycopg2.extras import execute_values
            execute_values(
                cur,
                """INSERT INTO chapter_embeddings (chapter_id, translation_id, model_name, embedding)
                   VALUES %s
                   ON CONFLICT (chapter_id, translation_id, model_name) DO NOTHING""",
                values,
                template="(%s, %s, %s, %s::vector)",
                page_size=100,
            )
            conn.commit()
        print(f"  Stored {len(values)} chapter embeddings.")

    def _store_embeddings(self, conn, table: str, id_col: str, ids: list[int], embeddings: np.ndarray):
        """Bulk store embeddings in a pgvector table. Inserts in small batches for large vectors."""
        store_batch = 50  # Small batches for 2000-dim vectors
        stored = 0

        with conn.cursor() as cur:
            for start in range(0, len(ids), store_batch):
                end = min(start + store_batch, len(ids))
                for i in range(start, end):
                    vec_str = "[" + ",".join(f"{x:.6f}" for x in embeddings[i]) + "]"
                    cur.execute(
                        f"""INSERT INTO {table} ({id_col}, model_name, embedding)
                            VALUES (%s, %s, %s::vector)
                            ON CONFLICT ({id_col}, model_name) DO NOTHING""",
                        (ids[i], self.model_name, vec_str),
                    )
                conn.commit()
                stored += (end - start)
                if stored % 1000 == 0:
                    print(f"    Stored {stored}/{len(ids)}...")
        print(f"    Stored {stored}/{len(ids)} total.")


def semantic_search(conn, query: str, table: str = "verses", top_k: int = 10, model_name: str = EMBEDDING_MODEL):
    """Search for verses or Strong's entries by semantic similarity."""
    engine = EmbeddingEngine(model_name)
    query_emb = engine.encode([query])[0]
    vec_str = "[" + ",".join(f"{x:.6f}" for x in query_emb) + "]"

    if table == "verses":
        with conn.cursor() as cur:
            cur.execute(f"SET hnsw.ef_search = 100")
            cur.execute("""
                SELECT b.name, ch.chapter_number, v.verse_number, v.text,
                       1 - (ve.embedding <=> %s::vector) as similarity
                FROM verse_embeddings ve
                JOIN verses v ON v.id = ve.verse_id
                JOIN chapters ch ON ch.id = v.chapter_id
                JOIN books b ON b.id = ch.book_id
                WHERE ve.model_name = %s
                ORDER BY ve.embedding <=> %s::vector
                LIMIT %s
            """, (vec_str, model_name, vec_str, top_k))
            return cur.fetchall()

    elif table == "strongs":
        with conn.cursor() as cur:
            cur.execute(f"SET hnsw.ef_search = 100")
            cur.execute("""
                SELECT se.strongs_number, se.original_word, se.transliteration,
                       COALESCE(se.gloss, left(se.root_definition, 60)),
                       1 - (sem.embedding <=> %s::vector) as similarity
                FROM strongs_embeddings sem
                JOIN strongs_entries se ON se.id = sem.strongs_id
                WHERE sem.model_name = %s
                ORDER BY sem.embedding <=> %s::vector
                LIMIT %s
            """, (vec_str, model_name, vec_str, top_k))
            return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(description="Bible embedding engine")
    parser.add_argument("--verses", action="store_true", help="Embed verses")
    parser.add_argument("--strongs", action="store_true", help="Embed Strong's definitions")
    parser.add_argument("--chapters", action="store_true", help="Embed chapters")
    parser.add_argument("--all", action="store_true", help="Embed everything")
    parser.add_argument("--search", type=str, default=None, help="Semantic search query")
    parser.add_argument("--search-strongs", type=str, default=None, help="Search Strong's by meaning")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    args = parser.parse_args()

    conn = get_connection()

    if args.search:
        results = semantic_search(conn, args.search, table="verses", top_k=args.top_k)
        print(f"\nSemantic search: '{args.search}'\n")
        for r in results:
            print(f"  [{r[4]:.3f}] {r[0]} {r[1]}:{r[2]} — {r[3][:90]}")
        conn.close()
        return

    if args.search_strongs:
        results = semantic_search(conn, args.search_strongs, table="strongs", top_k=args.top_k)
        print(f"\nStrong's semantic search: '{args.search_strongs}'\n")
        for r in results:
            print(f"  [{r[4]:.3f}] {r[0]} {r[1]} ({r[2]}) — {r[3]}")
        conn.close()
        return

    try:
        engine = EmbeddingEngine()

        if args.all or args.verses or not any([args.verses, args.strongs, args.chapters, args.search]):
            print("\n--- Verses ---")
            engine.embed_verses(conn, "KJV")

        if args.all or args.strongs:
            print("\n--- Strong's ---")
            engine.embed_strongs(conn)

        if args.all or args.chapters:
            print("\n--- Chapters ---")
            engine.embed_chapters(conn, "KJV")

        # Summary
        print(f"\n--- Embedding Summary ---")
        for tbl in ["verse_embeddings", "strongs_embeddings", "chapter_embeddings"]:
            count = table_count(conn, tbl)
            print(f"  {tbl}: {count:,}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
