import { useState, useCallback } from 'react';
import { apiFetch } from '@/api/client';
import { EDGE_TYPE_COLORS } from '@/lib/colors';

interface PathEdge {
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  edge_type: string;
  weight: number;
  source_label: string;
  target_label: string;
}

interface PathResponse {
  found: boolean;
  path: PathEdge[];
  depth: number;
  from_label: string;
  to_label: string;
}

const EDGE_NAMES: Record<string, string> = {
  cross_ref: 'cross-reference',
  twot_family: 'word family',
  nave_topic: 'topic link',
  nave_shared: 'shared topic',
  semantic_sim: 'similar meaning',
  strongs_sim: 'similar word',
};

export function ShortestPath() {
  const [fromId, setFromId] = useState('');
  const [toId, setToId] = useState('');
  const [fromType, setFromType] = useState('verse');
  const [toType, setToType] = useState('verse');
  const [result, setResult] = useState<PathResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const findPath = useCallback(async () => {
    if (!fromId || !toId) return;
    setLoading(true);
    setError('');
    try {
      const data = await apiFetch<PathResponse>('/explore/shortest-path', {
        from_type: fromType,
        from_id: fromId,
        to_type: toType,
        to_id: toId,
        max_depth: '5',
      });
      setResult(data);
      if (!data.found) setError('No path found within 5 hops');
    } catch {
      setError('Failed to find path');
      setResult(null);
    }
    setLoading(false);
  }, [fromId, toId, fromType, toType]);

  // Build the visual path chain
  const pathNodes = result?.found ? buildPathChain(result.path) : [];

  return (
    <div className="p-3">
      {/* Input row */}
      <div className="flex items-end gap-2 mb-3">
        <div className="flex-1">
          <label className="text-[10px] text-gray-500 block mb-1">From</label>
          <div className="flex gap-1">
            <select value={fromType} onChange={(e) => setFromType(e.target.value)}
              className="bg-bg-secondary text-white text-xs rounded px-1 py-1.5 border border-white/10 w-20">
              <option value="verse">Verse</option>
              <option value="theme">Theme</option>
              <option value="strongs">Strong's</option>
            </select>
            <input type="number" value={fromId} onChange={(e) => setFromId(e.target.value)}
              placeholder="ID" className="flex-1 bg-bg-secondary text-white text-xs rounded px-2 py-1.5 border border-white/10 outline-none" />
          </div>
        </div>

        <span className="text-gray-600 text-xs pb-1.5">→</span>

        <div className="flex-1">
          <label className="text-[10px] text-gray-500 block mb-1">To</label>
          <div className="flex gap-1">
            <select value={toType} onChange={(e) => setToType(e.target.value)}
              className="bg-bg-secondary text-white text-xs rounded px-1 py-1.5 border border-white/10 w-20">
              <option value="verse">Verse</option>
              <option value="theme">Theme</option>
              <option value="strongs">Strong's</option>
            </select>
            <input type="number" value={toId} onChange={(e) => setToId(e.target.value)}
              placeholder="ID" className="flex-1 bg-bg-secondary text-white text-xs rounded px-2 py-1.5 border border-white/10 outline-none" />
          </div>
        </div>

        <button onClick={findPath} disabled={loading || !fromId || !toId}
          className="bg-accent-blue text-white text-xs px-4 py-1.5 rounded hover:bg-accent-blue/80 disabled:opacity-40 transition">
          {loading ? '...' : 'Find'}
        </button>
      </div>

      <div className="text-[10px] text-gray-600 mb-2">
        Tip: Genesis 1:1 = verse 1, John 1:1 = verse 21242. Find how they connect!
      </div>

      {error && <div className="text-xs text-red-400 mb-2">{error}</div>}

      {/* Path visualization */}
      {result?.found && pathNodes.length > 0 && (
        <div>
          <div className="text-xs text-gray-400 mb-2">
            Path found: {result.depth} hop{result.depth > 1 ? 's' : ''}
          </div>

          <div className="space-y-0">
            {pathNodes.map((node, i) => (
              <div key={i}>
                {/* Node */}
                <div className="flex items-center gap-2 py-1">
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                    node.type === 'theme' ? 'bg-accent-green' : node.type === 'strongs' ? 'bg-accent-gold' : 'bg-accent-blue'
                  }`} />
                  <span className="text-xs text-white">{node.label}</span>
                  <span className="text-[10px] text-gray-600">{node.type} #{node.id}</span>
                </div>
                {/* Edge (if not last) */}
                {node.edgeToNext && (
                  <div className="flex items-center gap-2 py-0.5 ml-1">
                    <div className="w-0.5 h-4 ml-[3px]" style={{ backgroundColor: EDGE_TYPE_COLORS[node.edgeToNext.edge_type] || '#666' }} />
                    <span className="text-[10px]" style={{ color: EDGE_TYPE_COLORS[node.edgeToNext.edge_type] || '#666' }}>
                      {EDGE_NAMES[node.edgeToNext.edge_type] || node.edgeToNext.edge_type}
                    </span>
                    <span className="text-[10px] text-gray-600">
                      (weight: {node.edgeToNext.weight.toFixed(2)})
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface PathNode {
  type: string;
  id: number;
  label: string;
  edgeToNext?: { edge_type: string; weight: number };
}

function buildPathChain(edges: PathEdge[]): PathNode[] {
  if (edges.length === 0) return [];
  const nodes: PathNode[] = [];

  // First node
  nodes.push({
    type: edges[0].source_type,
    id: edges[0].source_id,
    label: edges[0].source_label || `${edges[0].source_type} #${edges[0].source_id}`,
    edgeToNext: { edge_type: edges[0].edge_type, weight: edges[0].weight },
  });

  for (let i = 0; i < edges.length; i++) {
    const e = edges[i];
    const isLast = i === edges.length - 1;
    nodes.push({
      type: e.target_type,
      id: e.target_id,
      label: e.target_label || `${e.target_type} #${e.target_id}`,
      edgeToNext: isLast ? undefined : { edge_type: edges[i + 1].edge_type, weight: edges[i + 1].weight },
    });
  }

  return nodes;
}
