"""
Bible Knowledge Graph builder.

Constructs a heterogeneous graph in the knowledge_edges table from multiple
data sources: cross-references, TWOT word families, Nave's topical assignments,
and embedding-based semantic similarity.

Edge types:
    cross_ref       verse → verse       From cross_references table (433K)
    twot_family     strongs → strongs   Shared TWOT root number
    nave_topic      verse → topic       Nave's topical assignment
    nave_shared     verse → verse       Verses sharing a Nave's topic
    semantic_sim    verse → verse       Embedding cosine similarity ≥ threshold
    strongs_sim     strongs → strongs   Strong's embedding similarity ≥ threshold

Usage:
    python -m src.knowledge_graph --all
    python -m src.knowledge_graph --cross-refs
    python -m src.knowledge_graph --twot
    python -m src.knowledge_graph --naves
    python -m src.knowledge_graph --semantic --threshold 0.85
    python -m src.knowledge_graph --stats
    python -m src.knowledge_graph --export graph.graphml
"""

import argparse
import json
import sys
from collections import defaultdict

sys.path.insert(0, ".")
from etl.db import get_connection, table_count


class BibleKnowledgeGraph:
    """Builds and queries the knowledge graph stored in knowledge_edges."""

    def __init__(self, conn):
        self.conn = conn

    def _bulk_insert_edges(self, edges: list[tuple], batch_size: int = 1000) -> int:
        """Insert edges into knowledge_edges. Returns count inserted."""
        if not edges:
            return 0

        inserted = 0
        with self.conn.cursor() as cur:
            for start in range(0, len(edges), batch_size):
                batch = edges[start:start + batch_size]
                from psycopg2.extras import execute_values
                execute_values(
                    cur,
                    """INSERT INTO knowledge_edges
                       (source_type, source_id, target_type, target_id, edge_type, weight, metadata)
                       VALUES %s
                       ON CONFLICT (source_type, source_id, target_type, target_id, edge_type) DO NOTHING""",
                    batch,
                    template="(%s, %s, %s, %s, %s, %s, %s)",
                    page_size=500,
                )
                inserted += len(batch)
                self.conn.commit()
                if inserted % 10000 == 0:
                    print(f"    {inserted:,} edges...")

        return inserted

    # ------------------------------------------------------------------
    # Edge builders
    # ------------------------------------------------------------------

    def build_cross_ref_edges(self):
        """Copy cross_references into knowledge_edges as 'cross_ref' edges."""
        print("Building cross-reference edges...")

        with self.conn.cursor() as cur:
            # Check if already built
            cur.execute("SELECT count(*) FROM knowledge_edges WHERE edge_type = 'cross_ref'")
            existing = cur.fetchone()[0]
            if existing > 0:
                print(f"  Already have {existing:,} cross_ref edges, skipping.")
                return existing

            cur.execute("""
                INSERT INTO knowledge_edges (source_type, source_id, target_type, target_id, edge_type, weight)
                SELECT 'verse', source_verse_id, 'verse', target_verse_id, 'cross_ref', relevance_score
                FROM cross_references
                ON CONFLICT DO NOTHING
            """)
            count = cur.rowcount
            self.conn.commit()

        print(f"  Created {count:,} cross_ref edges.")
        return count

    def build_twot_family_edges(self):
        """Create edges between Strong's entries sharing a TWOT root number."""
        print("Building TWOT word-family edges...")

        with self.conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM knowledge_edges WHERE edge_type = 'twot_family'")
            if cur.fetchone()[0] > 0:
                print("  Already built, skipping.")
                return

            # Group by TWOT base number
            cur.execute("""
                SELECT id, strongs_number, twot_ref
                FROM strongs_entries
                WHERE twot_ref IS NOT NULL
            """)
            rows = cur.fetchall()

        import re
        families = defaultdict(list)
        for sid, snum, twot in rows:
            base = re.match(r"(\d+)", twot)
            if base:
                families[base.group(1)].append((sid, snum, twot))

        edges = []
        for base, members in families.items():
            if len(members) < 2:
                continue
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    edges.append((
                        "strongs", members[i][0],
                        "strongs", members[j][0],
                        "twot_family",
                        1.0,
                        json.dumps({"twot_base": base, "from": members[i][1], "to": members[j][1]}),
                    ))

        inserted = self._bulk_insert_edges(edges)
        print(f"  Created {inserted:,} twot_family edges from {len(families)} word families.")

    def build_nave_topic_edges(self):
        """Create edges from verses to Nave's topic nodes, and seed theme_nodes."""
        print("Building Nave's topic edges...")

        with self.conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM knowledge_edges WHERE edge_type = 'nave_topic'")
            if cur.fetchone()[0] > 0:
                print("  Already built, skipping.")
                return

            # Seed theme_nodes from distinct Nave's topics
            cur.execute("""
                INSERT INTO theme_nodes (theme_name)
                SELECT DISTINCT topic FROM nave_topics
                ON CONFLICT (theme_name) DO NOTHING
            """)
            self.conn.commit()

            theme_count = table_count(self.conn, "theme_nodes")
            print(f"  Seeded {theme_count:,} theme nodes.")

            # Build verse → topic edges
            cur.execute("""
                INSERT INTO knowledge_edges (source_type, source_id, target_type, target_id, edge_type, weight)
                SELECT 'verse', ntv.verse_id, 'theme', tn.id, 'nave_topic', 1.0
                FROM nave_topic_verses ntv
                JOIN nave_topics nt ON nt.id = ntv.topic_id
                JOIN theme_nodes tn ON tn.theme_name = nt.topic
                ON CONFLICT DO NOTHING
            """)
            count = cur.rowcount
            self.conn.commit()

        print(f"  Created {count:,} nave_topic edges.")

    def build_semantic_similarity_edges(self, threshold: float = 0.85, limit_per_verse: int = 5):
        """Find verse pairs above cosine similarity threshold using pgvector.

        This uses the HNSW index for efficient nearest-neighbor search.
        Only creates edges above the threshold, limited to top-k per verse.
        """
        print(f"Building semantic similarity edges (threshold={threshold})...")

        with self.conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM knowledge_edges WHERE edge_type = 'semantic_sim' AND source_type = 'verse'")
            if cur.fetchone()[0] > 0:
                print("  Already built, skipping.")
                return

            cur.execute("SET hnsw.ef_search = 60")

            # Process in chunks to avoid memory issues
            cur.execute("SELECT count(*) FROM verse_embeddings")
            total = cur.fetchone()[0]
            print(f"  Processing {total:,} verses...")

            chunk_size = 500
            total_edges = 0

            for offset in range(0, total, chunk_size):
                cur.execute("""
                    WITH source_batch AS (
                        SELECT ve.verse_id, ve.embedding
                        FROM verse_embeddings ve
                        ORDER BY ve.verse_id
                        LIMIT %s OFFSET %s
                    )
                    SELECT sb.verse_id, ve2.verse_id,
                           1 - (sb.embedding <=> ve2.embedding) as similarity
                    FROM source_batch sb
                    CROSS JOIN LATERAL (
                        SELECT ve.verse_id, ve.embedding
                        FROM verse_embeddings ve
                        WHERE ve.verse_id != sb.verse_id
                        ORDER BY ve.embedding <=> sb.embedding
                        LIMIT %s
                    ) ve2
                    WHERE 1 - (sb.embedding <=> ve2.embedding) >= %s
                """, (chunk_size, offset, limit_per_verse, threshold))

                rows = cur.fetchall()
                if rows:
                    edges = [
                        ("verse", r[0], "verse", r[1], "semantic_sim", round(r[2], 4),
                         json.dumps({"cosine": round(r[2], 4)}))
                        for r in rows
                    ]
                    self._bulk_insert_edges(edges)
                    total_edges += len(edges)

                if (offset + chunk_size) % 5000 == 0:
                    print(f"    Processed {min(offset + chunk_size, total):,}/{total:,}, edges so far: {total_edges:,}")

        print(f"  Created {total_edges:,} semantic_sim (verse) edges.")

    def build_strongs_similarity_edges(self, threshold: float = 0.80, limit_per_entry: int = 10):
        """Find Strong's entries with similar definitions using embedding similarity."""
        print(f"Building Strong's similarity edges (threshold={threshold})...")

        with self.conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM knowledge_edges WHERE edge_type = 'strongs_sim'")
            if cur.fetchone()[0] > 0:
                print("  Already built, skipping.")
                return

            cur.execute("SET hnsw.ef_search = 60")
            cur.execute("""
                SELECT s1.sid, neighbors.se2_id, neighbors.similarity FROM (
                    SELECT sem1.strongs_id as sid, sem1.embedding
                    FROM strongs_embeddings sem1
                ) s1
                CROSS JOIN LATERAL (
                    SELECT sem2.strongs_id as se2_id,
                           1 - (s1.embedding <=> sem2.embedding) as similarity
                    FROM strongs_embeddings sem2
                    WHERE sem2.strongs_id != s1.sid
                    ORDER BY sem2.embedding <=> s1.embedding
                    LIMIT %s
                ) neighbors
                WHERE neighbors.similarity >= %s
            """, (limit_per_entry, threshold))

            rows = cur.fetchall()

        edges = [
            ("strongs", r[0], "strongs", r[1], "strongs_sim", round(r[2], 4),
             json.dumps({"cosine": round(r[2], 4)}))
            for r in rows
        ]
        inserted = self._bulk_insert_edges(edges)
        print(f"  Created {inserted:,} strongs_sim edges.")

    # ------------------------------------------------------------------
    # Stats and export
    # ------------------------------------------------------------------

    def stats(self) -> dict:
        """Return edge type counts and graph metrics."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT edge_type, count(*) as cnt,
                       count(DISTINCT source_id) as sources,
                       count(DISTINCT target_id) as targets,
                       avg(weight) as avg_weight
                FROM knowledge_edges
                GROUP BY edge_type
                ORDER BY cnt DESC
            """)
            rows = cur.fetchall()

        total = sum(r[1] for r in rows)
        return {
            "total_edges": total,
            "edge_types": [
                {
                    "type": r[0],
                    "count": r[1],
                    "distinct_sources": r[2],
                    "distinct_targets": r[3],
                    "avg_weight": round(r[4], 4) if r[4] else None,
                }
                for r in rows
            ],
        }

    def export_graphml(self, filepath: str, edge_types: list[str] | None = None):
        """Export the graph to GraphML format for visualization or external analysis."""
        try:
            import networkx as nx
        except ImportError:
            print("ERROR: networkx not installed. pip install networkx")
            return

        print(f"Exporting to {filepath}...")
        G = nx.DiGraph()

        with self.conn.cursor() as cur:
            where = ""
            params = []
            if edge_types:
                placeholders = ",".join(["%s"] * len(edge_types))
                where = f"WHERE edge_type IN ({placeholders})"
                params = edge_types

            cur.execute(f"""
                SELECT source_type, source_id, target_type, target_id, edge_type, weight
                FROM knowledge_edges {where}
            """, params)

            for row in cur:
                src = f"{row[0]}_{row[1]}"
                tgt = f"{row[2]}_{row[3]}"
                G.add_edge(src, tgt, edge_type=row[4], weight=row[5])

        nx.write_graphml(G, filepath)
        print(f"  Exported {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges.")


def print_stats(conn):
    """Print knowledge graph statistics."""
    kg = BibleKnowledgeGraph(conn)
    s = kg.stats()

    print(f"\n{'='*60}")
    print(f"KNOWLEDGE GRAPH STATISTICS")
    print(f"{'='*60}")
    print(f"Total edges: {s['total_edges']:,}\n")

    headers = ["Edge Type", "Count", "Sources", "Targets", "Avg Weight"]
    rows = []
    for et in s["edge_types"]:
        rows.append([
            et["type"],
            f"{et['count']:,}",
            f"{et['distinct_sources']:,}",
            f"{et['distinct_targets']:,}",
            f"{et['avg_weight']:.4f}" if et["avg_weight"] else "—",
        ])

    from tabulate import tabulate
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def main():
    parser = argparse.ArgumentParser(description="Bible Knowledge Graph builder")
    parser.add_argument("--cross-refs", action="store_true", help="Build cross-reference edges")
    parser.add_argument("--twot", action="store_true", help="Build TWOT word-family edges")
    parser.add_argument("--naves", action="store_true", help="Build Nave's topic edges")
    parser.add_argument("--semantic", action="store_true", help="Build semantic similarity edges")
    parser.add_argument("--strongs-sim", action="store_true", help="Build Strong's similarity edges")
    parser.add_argument("--all", action="store_true", help="Build all edge types")
    parser.add_argument("--threshold", type=float, default=0.85, help="Cosine similarity threshold (default: 0.85)")
    parser.add_argument("--stats", action="store_true", help="Print graph statistics")
    parser.add_argument("--export", type=str, default=None, help="Export to GraphML file")

    args = parser.parse_args()

    conn = get_connection()
    kg = BibleKnowledgeGraph(conn)

    try:
        if args.stats:
            print_stats(conn)
            return

        if args.export:
            kg.export_graphml(args.export)
            return

        build_any = args.all or args.cross_refs or args.twot or args.naves or args.semantic or args.strongs_sim

        if not build_any:
            # Default: build all
            args.all = True

        if args.all or args.cross_refs:
            kg.build_cross_ref_edges()

        if args.all or args.twot:
            kg.build_twot_family_edges()

        if args.all or args.naves:
            kg.build_nave_topic_edges()

        if args.all or args.strongs_sim:
            kg.build_strongs_similarity_edges(threshold=args.threshold)

        if args.all or args.semantic:
            kg.build_semantic_similarity_edges(threshold=args.threshold)

        print_stats(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
