from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Set

from .. import db
from .. import config
from ..models.graph import Neighborhood, GraphEdge, GraphNode, GraphStats


router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/neighborhood/{node_type}/{node_id}", response_model=Neighborhood)
async def get_neighborhood(
    node_type: str,
    node_id: int,
    hops: int = Query(1, ge=1, le=config.NEIGHBORHOOD_MAX_HOPS),
    max_nodes: int = Query(200, ge=1, le=config.NEIGHBORHOOD_MAX_NODES),
    edge_types: str = Query(None),
    min_weight: float = Query(0.0, ge=0.0)
):
    valid_node_types = {"verse", "chapter", "principle", "strongs", "theme"}
    if node_type not in valid_node_types:
        raise HTTPException(status_code=400, detail="Invalid node_type")

    pool = await db.get_pool()

    # Parse edge_types parameter
    if edge_types:
        edge_type_list = [et.strip() for et in edge_types.split(",") if et.strip()]
    else:
        all_types = await pool.fetch("SELECT DISTINCT edge_type FROM knowledge_edges")
        edge_type_list = [row["edge_type"] for row in all_types]

    if not edge_type_list:
        return Neighborhood(
            center_node_type=node_type,
            center_node_id=node_id,
            nodes=[],
            edges=[],
            hop_count=0,
            node_count=0,
            edge_count=0
        )

    # Recursive CTE to fetch neighborhood
    query = """
        WITH RECURSIVE neighborhood AS (
            SELECT source_type, source_id, target_type, target_id, edge_type, weight, 1 AS hop
            FROM knowledge_edges
            WHERE (source_type = $1 AND source_id = $2) OR (target_type = $1 AND target_id = $2)
              AND edge_type = ANY($3::text[])
              AND weight >= $4
            UNION
            SELECT ke.source_type, ke.source_id, ke.target_type, ke.target_id, ke.edge_type, ke.weight, n.hop + 1
            FROM knowledge_edges ke
            JOIN neighborhood n ON (ke.source_type = n.target_type AND ke.source_id = n.target_id)
                                OR (ke.target_type = n.source_type AND ke.target_id = n.source_id)
            WHERE n.hop < $5
              AND ke.edge_type = ANY($3::text[])
              AND ke.weight >= $4
        )
        SELECT DISTINCT source_type, source_id, target_type, target_id, edge_type, weight
        FROM neighborhood
        LIMIT $6
    """

    edge_rows = await pool.fetch(query, node_type, node_id, edge_type_list, min_weight, hops, max_nodes)

    edges: List[GraphEdge] = []
    nodes_set: Set[tuple] = set()

    for row in edge_rows:
        edges.append(GraphEdge(
            source_type=row["source_type"],
            source_id=row["source_id"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            edge_type=row["edge_type"],
            weight=row["weight"]
        ))
        nodes_set.add((row["source_type"], row["source_id"]))
        nodes_set.add((row["target_type"], row["target_id"]))

    # Batch-fetch labels for all node types
    nodes: List[GraphNode] = []
    nodes_by_type: Dict[str, List[int]] = {}

    for n_type, n_id in nodes_set:
        if n_type not in nodes_by_type:
            nodes_by_type[n_type] = []
        nodes_by_type[n_type].append(n_id)

    # Fetch labels per node type
    for n_type, ids in nodes_by_type.items():
        if n_type == "verse":
            label_query = "SELECT id, SUBSTRING(text FROM 1 FOR 60) as label FROM verses WHERE id = ANY($1)"
        elif n_type == "theme":
            label_query = "SELECT id, theme_name as label FROM theme_nodes WHERE id = ANY($1)"
        elif n_type == "strongs":
            label_query = "SELECT id, strongs_number as label FROM strongs_entries WHERE id = ANY($1)"
        elif n_type == "principle":
            label_query = "SELECT id, principle_text as label FROM distilled_principles WHERE id = ANY($1)"
        elif n_type == "chapter":
            label_query = """
                SELECT ch.id, CONCAT(b.name, ' ', ch.chapter_number) as label
                FROM chapters ch
                JOIN books b ON b.id = ch.book_id
                WHERE ch.id = ANY($1)
            """
        else:
            continue

        label_rows = await pool.fetch(label_query, ids)
        for row in label_rows:
            nodes.append(GraphNode(
                node_type=n_type,
                node_id=row["id"],
                label=row["label"]
            ))

    hop_count = hops if edges else 0

    return Neighborhood(
        center_node_type=node_type,
        center_node_id=node_id,
        nodes=nodes,
        edges=edges,
        hop_count=hop_count,
        node_count=len(nodes),
        edge_count=len(edges)
    )


@router.get("/stats", response_model=List[GraphStats])
async def get_graph_stats():
    pool = await db.get_pool()
    query = """
        SELECT edge_type, COUNT(*) as count
        FROM knowledge_edges
        GROUP BY edge_type
        ORDER BY count DESC
    """

    rows = await pool.fetch(query)
    return [GraphStats(edge_type=row["edge_type"], count=row["count"]) for row in rows]