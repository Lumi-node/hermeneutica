from typing import List, Dict, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from .. import db
from ..embeddings import embed_query, format_pgvector, MODEL_NAME as PRINCIPLE_EMBED_MODEL
import asyncio

router = APIRouter(prefix="/explore")

# Response Models
class ThemeTraceVerse(BaseModel):
    verse_id: int
    book_name: str
    abbreviation: str
    book_order: int
    testament: str
    genre: str
    chapter_number: int
    verse_number: int
    text_preview: str

    model_config = ConfigDict(from_attributes=True)


class ThemeTraceResponse(BaseModel):
    topic: str
    verse_count: int
    verses: List[ThemeTraceVerse]
    books_covered: int
    ot_count: int
    nt_count: int

    model_config = ConfigDict(from_attributes=True)


class PathEdge(BaseModel):
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    edge_type: str
    weight: float
    source_label: str = ""
    target_label: str = ""


class ShortestPathResponse(BaseModel):
    found: bool
    path: List[PathEdge]
    depth: int
    from_label: str
    to_label: str


class PrincipleResult(BaseModel):
    principle_id: int
    principle_text: str
    book_name: str
    chapter_number: int
    genre: str
    themes: List[str]
    teaching_type: str
    similarity: float
    ethics_scores: Dict[str, float]

    model_config = ConfigDict(from_attributes=True)


# Helper to parse themes from various formats
def parse_themes(themes: Any) -> List[str]:
    if isinstance(themes, list):
        return themes
    if isinstance(themes, str):
        if themes.startswith('[') and themes.endswith(']'):
            try:
                import json
                parsed = json.loads(themes)
                return parsed if isinstance(parsed, list) else [parsed]
            except:
                pass
        return [t.strip() for t in themes.split(',') if t.strip()]
    return [str(themes)] if themes else []


@router.get("/theme-search")
async def theme_search(q: str, limit: int = 10) -> List[str]:
    """
    Search for Nave's topics by prefix.
    Returns a list of topic strings matching the prefix.
    """
    query = """
        SELECT DISTINCT topic 
        FROM nave_topics 
        WHERE LOWER(topic) LIKE LOWER($1 || '%') 
        ORDER BY topic 
        LIMIT $2
    """
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(query, q, limit)
        return [row["topic"] for row in rows]


@router.get("/theme-trace")
async def theme_trace(topic: str, limit: int = 200) -> ThemeTraceResponse:
    """
    Find all verses for a Nave's topic, ordered chronologically.
    Returns detailed information about the topic's distribution across the Bible.
    """
    async with db.pool.acquire() as conn:
        # Check the topic exists (match across all subtopics)
        topic_check = await conn.fetchrow(
            "SELECT topic FROM nave_topics WHERE LOWER(topic) = LOWER($1) LIMIT 1",
            topic
        )
        if not topic_check:
            raise HTTPException(status_code=404, detail="Topic not found")

        actual_topic = topic_check["topic"]

        # Fetch verses across ALL subtopics of this topic
        verses_query = """
            SELECT DISTINCT ON (v.id)
                v.id as verse_id,
                b.name as book_name,
                b.abbreviation,
                b.book_order,
                b.testament,
                b.genre,
                ch.chapter_number,
                v.verse_number,
                LEFT(v.text, 150) as text_preview
            FROM nave_topic_verses ntv
            JOIN nave_topics nt ON nt.id = ntv.topic_id
            JOIN verses v ON v.id = ntv.verse_id AND v.translation_id = 1
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            WHERE LOWER(nt.topic) = LOWER($1)
            ORDER BY v.id
            LIMIT $2
        """
        verse_rows = await conn.fetch(verses_query, topic, limit)
        # Re-sort chronologically after DISTINCT ON
        verses = sorted(
            [ThemeTraceVerse(**dict(row)) for row in verse_rows],
            key=lambda v: (v.book_order, v.chapter_number, v.verse_number)
        )

        # Compute stats
        verse_count = len(verses)
        books_covered = len(set(v.book_name for v in verses))
        ot_count = len([v for v in verses if v.testament == "OT"])
        nt_count = len([v for v in verses if v.testament == "NT"])

        return ThemeTraceResponse(
            topic=actual_topic,
            verse_count=verse_count,
            verses=verses,
            books_covered=books_covered,
            ot_count=ot_count,
            nt_count=nt_count
        )


@router.get("/shortest-path")
async def shortest_path(
    from_type: str,
    from_id: int,
    to_type: str,
    to_id: int,
    max_depth: int = 6
) -> ShortestPathResponse:
    """
    Find the shortest path between two nodes using BFS.
    Supports verse, theme_node, strongs_entry, chapter, and book node types.
    """
    valid_types = {"verse", "theme_node", "strongs_entry", "chapter", "book"}
    if from_type not in valid_types or to_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid node type")

    from_key = f"{from_type}_{from_id}"
    to_key = f"{to_type}_{to_id}"

    if from_key == to_key:
        # Same node
        label = await _fetch_node_label(from_type, from_id)
        return ShortestPathResponse(
            found=True,
            path=[],
            depth=0,
            from_label=label,
            to_label=label
        )

    async with db.pool.acquire() as conn:
        visited = {from_key}
        queue = [(from_key, [])]  # (current_key, path_of_edges)

        for depth in range(1, max_depth + 1):
            next_queue = []

            for current_key, path in queue:
                node_type, node_id_str = current_key.split("_", 1)
                node_id = int(node_id_str)

                # Fetch edges connected to this node
                edges = await conn.fetch(
                    """
                    SELECT source_type, source_id, target_type, target_id, edge_type, weight
                    FROM knowledge_edges
                    WHERE (source_type = $1 AND source_id = $2)
                       OR (target_type = $1 AND target_id = $2)
                    ORDER BY weight DESC
                    LIMIT 50
                    """,
                    node_type, node_id
                )

                for edge in edges:
                    # Determine the other end of the edge
                    if edge["source_type"] == node_type and edge["source_id"] == node_id:
                        other_type = edge["target_type"]
                        other_id = edge["target_id"]
                        is_reverse = False
                    else:
                        other_type = edge["source_type"]
                        other_id = edge["source_id"]
                        is_reverse = True

                    other_key = f"{other_type}_{other_id}"

                    # Create PathEdge
                    path_edge = PathEdge(
                        source_type=edge["source_type"],
                        source_id=edge["source_id"],
                        target_type=edge["target_type"],
                        target_id=edge["target_id"],
                        edge_type=edge["edge_type"],
                        weight=edge["weight"]
                    )

                    if is_reverse:
                        path_edge.source_type, path_edge.target_type = path_edge.target_type, path_edge.source_type
                        path_edge.source_id, path_edge.target_id = path_edge.target_id, path_edge.source_id

                    # Check if we reached the target
                    if other_key == to_key:
                        full_path = path + [path_edge]
                        # Fetch labels for all nodes in the path
                        all_node_ids = {}
                        for pe in full_path:
                            all_node_ids.setdefault(pe.source_type, set()).add(pe.source_id)
                            all_node_ids.setdefault(pe.target_type, set()).add(pe.target_id)

                        labels_map = await _batch_fetch_labels(conn, all_node_ids)

                        for pe in full_path:
                            pe.source_label = labels_map.get(f"{pe.source_type}_{pe.source_id}", "")
                            pe.target_label = labels_map.get(f"{pe.target_type}_{pe.target_id}", "")

                        from_label = labels_map.get(from_key, "")
                        to_label = labels_map.get(to_key, "")

                        return ShortestPathResponse(
                            found=True,
                            path=full_path,
                            depth=depth,
                            from_label=from_label,
                            to_label=to_label
                        )

                    # Add to next level if not visited
                    if other_key not in visited:
                        visited.add(other_key)
                        next_queue.append((other_key, path + [path_edge]))

            queue = next_queue
            if not queue:
                break

        # Path not found
        from_label = await _fetch_node_label(from_type, from_id)
        to_label = await _fetch_node_label(to_type, to_id)
        return ShortestPathResponse(
            found=False,
            path=[],
            depth=max_depth,
            from_label=from_label,
            to_label=to_label
        )


async def _fetch_node_label(node_type: str, node_id: int) -> str:
    """Fetch a single node's label."""
    async with db.pool.acquire() as conn:
        result = await _batch_fetch_labels(conn, {node_type: {node_id}})
        return result.get(f"{node_type}_{node_id}", "")


async def _batch_fetch_labels(conn, node_ids: Dict[str, set]) -> Dict[str, str]:
    """Fetch labels for multiple node types and IDs."""
    labels_map = {}

    # Fetch in batches by type
    if "verse" in node_ids:
        verses = await conn.fetch(
            "SELECT id, LEFT(text, 80) as text FROM verses WHERE id = ANY($1)",
            list(node_ids["verse"])
        )
        for v in verses:
            labels_map[f"verse_{v['id']}"] = v["text"]

    if "theme_node" in node_ids:
        themes = await conn.fetch(
            "SELECT id, theme_name FROM theme_nodes WHERE id = ANY($1)",
            list(node_ids["theme_node"])
        )
        for t in themes:
            labels_map[f"theme_node_{t['id']}"] = t["theme_name"] or f"theme_{t['id']}"

    if "strongs_entry" in node_ids:
        strongs = await conn.fetch(
            "SELECT id, (strongs_number || ': ' || LEFT(root_definition, 60)) as text FROM strongs_entries WHERE id = ANY($1)",
            list(node_ids["strongs_entry"])
        )
        for s in strongs:
            labels_map[f"strongs_entry_{s['id']}"] = s["text"]

    if "chapter" in node_ids:
        chapters = await conn.fetch(
            "SELECT id, (chapter_number::text) as text FROM chapters WHERE id = ANY($1)",
            list(node_ids["chapter"])
        )
        for c in chapters:
            labels_map[f"chapter_{c['id']}"] = c["text"]

    if "book" in node_ids:
        books = await conn.fetch(
            "SELECT id, name as text FROM books WHERE id = ANY($1)",
            list(node_ids["book"])
        )
        for b in books:
            labels_map[f"book_{b['id']}"] = b["text"]

    return labels_map


@router.get("/principles")
async def principles(q: str, limit: int = 20) -> List[PrincipleResult]:
    """
    Semantic search over distilled moral principles.

    Embeds the query with bge-small-en-v1.5 and ranks principles by cosine
    similarity against pre-computed principle_embeddings (pgvector HNSW).
    Falls back to trigram match if principle_embeddings is empty for the
    configured model, so the endpoint still returns something on a fresh DB.
    """
    # Embed the user query (CPU, ~20-40ms). Offloaded to a thread so the
    # async event loop isn't blocked by ONNX inference.
    try:
        vec = await asyncio.to_thread(embed_query, q)
        vec_str = format_pgvector(vec)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    semantic_query = """
        SELECT
            dp.id as principle_id,
            dp.principle_text,
            dp.principle_order,
            pc.id as classification_id,
            b.name as book_name,
            ch.chapter_number,
            pc.genre,
            pc.themes,
            pc.teaching_type,
            1 - (pe.embedding <=> $1::vector) as sim
        FROM principle_embeddings pe
        JOIN distilled_principles dp ON dp.id = pe.principle_id
        JOIN passage_classifications pc ON pc.id = dp.classification_id
        JOIN chapters ch ON ch.id = pc.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE pe.model_name = $2
        ORDER BY pe.embedding <=> $1::vector
        LIMIT $3
    """

    fallback_query = """
        SELECT
            dp.id as principle_id,
            dp.principle_text,
            dp.principle_order,
            pc.id as classification_id,
            b.name as book_name,
            ch.chapter_number,
            pc.genre,
            pc.themes,
            pc.teaching_type,
            similarity(dp.principle_text, $1) as sim
        FROM distilled_principles dp
        JOIN passage_classifications pc ON pc.id = dp.classification_id
        JOIN chapters ch ON ch.id = pc.chapter_id
        JOIN books b ON b.id = ch.book_id
        WHERE dp.principle_text % $1 OR dp.principle_text ILIKE '%' || $1 || '%'
        ORDER BY similarity(dp.principle_text, $1) DESC, dp.principle_order
        LIMIT $2
    """

    async with db.pool.acquire() as conn:
        rows = await conn.fetch(semantic_query, vec_str, PRINCIPLE_EMBED_MODEL, limit)

        # Fallback: if no embeddings exist for the configured model, use trigram
        # search on the raw query text so the endpoint keeps working.
        if not rows:
            rows = await conn.fetch(fallback_query, q, limit)

        # Batch fetch ethics scores by classification_id
        classification_ids = [row["classification_id"] for row in rows]
        ethics_map: Dict[int, Dict[str, float]] = {}
        if classification_ids:
            ethics_rows = await conn.fetch(
                "SELECT classification_id, ethics_subset, relevance_score "
                "FROM passage_ethics_scores WHERE classification_id = ANY($1)",
                classification_ids,
            )
            for er in ethics_rows:
                ethics_map.setdefault(er["classification_id"], {})[er["ethics_subset"]] = er["relevance_score"]

        results: List[PrincipleResult] = []
        for row in rows:
            results.append(PrincipleResult(
                principle_id=row["principle_id"],
                principle_text=row["principle_text"],
                book_name=row["book_name"],
                chapter_number=row["chapter_number"],
                genre=row["genre"],
                themes=parse_themes(row["themes"]),
                teaching_type=row["teaching_type"],
                similarity=float(row["sim"]),
                ethics_scores=ethics_map.get(row["classification_id"], {}),
            ))

        return results


# ============================================================
# Cross-Reference Overlays for Galaxy View
# ============================================================

class CrossRefOverlayArc(BaseModel):
    source_verse_id: int
    target_verse_id: int
    source_x: float
    source_y: float
    source_z: float
    target_x: float
    target_y: float
    target_z: float
    relevance_score: float
    source_book: str
    target_book: str

class CrossRefOverlayResponse(BaseModel):
    preset: str
    arc_count: int
    arcs: list[CrossRefOverlayArc]
    description: str


@router.get("/crossref-overlay")
async def crossref_overlay(
    preset: str = "ot_to_nt",
    min_relevance: float = 0.0,
    limit: int = 500,
) -> CrossRefOverlayResponse:
    """
    Get cross-reference arcs for Galaxy overlay.
    Presets:
      - ot_to_nt: OT verses referencing NT (prophecy→fulfillment)
      - nt_to_ot: NT verses referencing OT (NT quoting OT)
      - prophets_to_gospels: Prophecy books → Gospel books
      - psalms_to_nt: Psalms → New Testament
      - torah_to_nt: Torah (Gen-Deut) → New Testament
      - intra_ot: Within Old Testament
      - intra_nt: Within New Testament
    """
    preset_configs = {
        "ot_to_nt": {
            "where": "b1.testament = 'OT' AND b2.testament = 'NT'",
            "desc": "Old Testament → New Testament: Promises, prophecies, and types fulfilled in the New Covenant",
        },
        "nt_to_ot": {
            "where": "b1.testament = 'NT' AND b2.testament = 'OT'",
            "desc": "New Testament → Old Testament: NT authors quoting, referencing, and interpreting the OT",
        },
        "prophets_to_gospels": {
            "where": "b1.genre = 'Prophecy' AND b2.genre = 'Gospel'",
            "desc": "Prophetic books → Gospels: Messianic prophecies connected to their fulfillment in Jesus' life",
        },
        "psalms_to_nt": {
            "where": "b1.name = 'Psalms' AND b2.testament = 'NT'",
            "desc": "Psalms → New Testament: The prayer book of Israel echoing through the early church",
        },
        "torah_to_nt": {
            "where": "b1.genre = 'Law' AND b2.testament = 'NT'",
            "desc": "Torah → New Testament: The foundation of the Law reinterpreted in Christ",
        },
        "intra_ot": {
            "where": "b1.testament = 'OT' AND b2.testament = 'OT' AND b1.id != b2.id",
            "desc": "Within Old Testament: Internal OT connections across books",
        },
        "intra_nt": {
            "where": "b1.testament = 'NT' AND b2.testament = 'NT' AND b1.id != b2.id",
            "desc": "Within New Testament: How NT books reference each other",
        },
    }

    config = preset_configs.get(preset)
    if not config:
        raise HTTPException(status_code=400, detail=f"Unknown preset: {preset}. Available: {list(preset_configs.keys())}")

    async with db.pool.acquire() as conn:
        query = f"""
            SELECT cr.source_verse_id, cr.target_verse_id,
                   uv1.x as sx, uv1.y as sy, uv1.z as sz,
                   uv2.x as tx, uv2.y as ty, uv2.z as tz,
                   cr.relevance_score,
                   b1.abbreviation as source_book,
                   b2.abbreviation as target_book
            FROM cross_references cr
            JOIN verses v1 ON v1.id = cr.source_verse_id AND v1.translation_id = 1
            JOIN chapters ch1 ON ch1.id = v1.chapter_id
            JOIN books b1 ON b1.id = ch1.book_id
            JOIN verses v2 ON v2.id = cr.target_verse_id AND v2.translation_id = 1
            JOIN chapters ch2 ON ch2.id = v2.chapter_id
            JOIN books b2 ON b2.id = ch2.book_id
            JOIN umap_verse_coords uv1 ON uv1.verse_id = v1.id
            JOIN umap_verse_coords uv2 ON uv2.verse_id = v2.id
            WHERE {config['where']}
              AND cr.relevance_score >= $1
            ORDER BY cr.relevance_score DESC
            LIMIT $2
        """
        rows = await conn.fetch(query, min_relevance, limit)

        arcs = [CrossRefOverlayArc(
            source_verse_id=r["source_verse_id"],
            target_verse_id=r["target_verse_id"],
            source_x=float(r["sx"]), source_y=float(r["sy"]), source_z=float(r["sz"]),
            target_x=float(r["tx"]), target_y=float(r["ty"]), target_z=float(r["tz"]),
            relevance_score=float(r["relevance_score"]),
            source_book=r["source_book"],
            target_book=r["target_book"],
        ) for r in rows]

        return CrossRefOverlayResponse(
            preset=preset,
            arc_count=len(arcs),
            arcs=arcs,
            description=config["desc"],
        )


# ============================================================
# Analytics Heatmap Endpoints
# ============================================================

@router.get("/heatmap/topics")
async def topic_distribution_heatmap(top_n: int = 25):
    """66 books x top N topics — verse count per cell."""
    async with db.pool.acquire() as conn:
        # Top N topics
        topic_rows = await conn.fetch("""
            SELECT nt.topic, COUNT(DISTINCT ntv.verse_id) as total
            FROM nave_topics nt
            JOIN nave_topic_verses ntv ON ntv.topic_id = nt.id
            GROUP BY nt.topic ORDER BY total DESC LIMIT $1
        """, top_n)
        topics = [r["topic"] for r in topic_rows]

        # All books
        book_rows = await conn.fetch("SELECT id, name, abbreviation, book_order, testament FROM books ORDER BY book_order")
        books = [dict(r) for r in book_rows]

        # Batch: get all (book_id, topic, count) in one query
        data_rows = await conn.fetch("""
            SELECT ch.book_id, nt.topic, COUNT(DISTINCT ntv.verse_id) as cnt
            FROM nave_topic_verses ntv
            JOIN nave_topics nt ON nt.id = ntv.topic_id
            JOIN verses v ON v.id = ntv.verse_id
            JOIN chapters ch ON ch.id = v.chapter_id
            WHERE nt.topic = ANY($1::text[])
            GROUP BY ch.book_id, nt.topic
        """, topics)

        # Build lookup
        lookup: dict[tuple[int, str], int] = {}
        for r in data_rows:
            lookup[(r["book_id"], r["topic"])] = r["cnt"]

        # Build matrix
        max_val = 0
        matrix = []
        for b in book_rows:
            row = []
            for t in topics:
                v = lookup.get((b["id"], t), 0)
                row.append(v)
                if v > max_val:
                    max_val = v
            matrix.append(row)

        return {"books": books, "topics": topics, "matrix": matrix, "max_value": max_val}


@router.get("/heatmap/ethics")
async def ethics_landscape_heatmap():
    """66 books x 5 ethics dimensions — average score per book."""
    subsets = ["commonsense", "deontology", "justice", "virtue", "utilitarianism"]

    async with db.pool.acquire() as conn:
        book_rows = await conn.fetch("SELECT id, name, abbreviation, book_order, testament FROM books ORDER BY book_order")
        books = [dict(r) for r in book_rows]

        classified = await conn.fetchval("SELECT COUNT(*) FROM passage_classifications") or 0

        # Get all scores in one query
        score_rows = await conn.fetch("""
            SELECT b.id as book_id, pes.ethics_subset, AVG(pes.relevance_score) as avg_score
            FROM passage_ethics_scores pes
            JOIN passage_classifications pc ON pc.id = pes.classification_id
            JOIN chapters ch ON ch.id = pc.chapter_id
            JOIN books b ON b.id = ch.book_id
            GROUP BY b.id, pes.ethics_subset
        """)

        # Build lookup
        lookup: dict[tuple[int, str], float] = {}
        for r in score_rows:
            lookup[(r["book_id"], r["ethics_subset"])] = float(r["avg_score"])

        matrix = []
        for b in book_rows:
            row = [round(lookup.get((b["id"], s), 0.0), 4) for s in subsets]
            matrix.append(row)

        return {"books": books, "ethics_subsets": subsets, "matrix": matrix, "classified_chapters": classified}


@router.get("/heatmap/words")
async def word_frequency_heatmap(top_n: int = 30):
    """66 books x top N Strong's words — usage count per cell."""
    async with db.pool.acquire() as conn:
        # Top N words
        word_rows = await conn.fetch("""
            SELECT se.strongs_number, se.transliteration, se.language,
                   LEFT(se.root_definition, 40) as short_def,
                   COUNT(*) as total
            FROM word_alignments wa
            JOIN strongs_entries se ON se.strongs_number = wa.strongs_number
            GROUP BY se.strongs_number, se.transliteration, se.language, se.root_definition
            ORDER BY total DESC LIMIT $1
        """, top_n)
        words = [{"strongs_number": w["strongs_number"], "transliteration": w["transliteration"] or "",
                   "language": w["language"], "short_def": w["short_def"] or ""} for w in word_rows]
        strongs_nums = [w["strongs_number"] for w in word_rows]

        book_rows = await conn.fetch("SELECT id, name, abbreviation, book_order, testament FROM books ORDER BY book_order")
        books = [dict(r) for r in book_rows]

        # Batch query all (book_id, strongs_number, count)
        data_rows = await conn.fetch("""
            SELECT b.id as book_id, wa.strongs_number, COUNT(*) as cnt
            FROM word_alignments wa
            JOIN verses v ON v.id = wa.verse_id
            JOIN chapters ch ON ch.id = v.chapter_id
            JOIN books b ON b.id = ch.book_id
            WHERE wa.strongs_number = ANY($1::text[])
            GROUP BY b.id, wa.strongs_number
        """, strongs_nums)

        lookup: dict[tuple[int, str], int] = {}
        for r in data_rows:
            lookup[(r["book_id"], r["strongs_number"])] = r["cnt"]

        max_val = 0
        matrix = []
        for b in book_rows:
            row = []
            for sn in strongs_nums:
                v = lookup.get((b["id"], sn), 0)
                row.append(v)
                if v > max_val:
                    max_val = v
            matrix.append(row)

        return {"books": books, "words": words, "matrix": matrix, "max_value": max_val}