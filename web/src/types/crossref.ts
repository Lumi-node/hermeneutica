export interface CrossRefArc {
  sourceVerseId: number;
  targetVerseId: number;
  sourceX: number;
  sourceY: number;
  sourceZ: number;
  targetX: number;
  targetY: number;
  targetZ: number;
  relevanceScore: number;
}

export interface BookMatrixEntry {
  source: number;
  target: number;
  count: number;
  avgRelevance: number;
}
