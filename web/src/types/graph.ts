export type NodeType = 'verse' | 'theme' | 'strongs';

export type EdgeType =
  | 'cross_ref'
  | 'twot_family'
  | 'nave_topic'
  | 'nave_shared'
  | 'semantic_sim'
  | 'strongs_sim';

export interface GraphNode {
  id: string; // "{type}_{db_id}"
  nodeType: NodeType;
  dbId: number;
  label: string;
  metadata: Record<string, unknown>;
  // Layout positions (assigned by force layout)
  x?: number;
  y?: number;
  z?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  edgeType: EdgeType;
  weight: number;
}

export interface Neighborhood {
  centerId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  truncated: boolean;
}
