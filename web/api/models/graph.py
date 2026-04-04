from __future__ import annotations
from typing import List
from pydantic import BaseModel, ConfigDict


class GraphNodeLabel(BaseModel):
    node_type: str  # ("verse", "chapter", "principle", "strongs", "theme")
    node_id: int
    label: str
    model_config = ConfigDict(from_attributes=True)


class GraphEdge(BaseModel):
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    edge_type: str  # (cross_ref, shared_theme, shared_root, semantic_sim, principle_source, theme_member)
    weight: float
    model_config = ConfigDict(from_attributes=True)


class GraphNode(BaseModel):
    node_type: str
    node_id: int
    label: str
    model_config = ConfigDict(from_attributes=True)


class Neighborhood(BaseModel):
    center_node_type: str
    center_node_id: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    hop_count: int
    node_count: int
    edge_count: int
    model_config = ConfigDict(from_attributes=True)


class GraphStats(BaseModel):
    edge_type: str
    count: int
    model_config = ConfigDict(from_attributes=True)