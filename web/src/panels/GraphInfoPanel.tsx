import { useMemo } from 'react';
import { EDGE_TYPE_COLORS } from '@/lib/colors';

interface ApiNode {
  node_type: string;
  node_id: number;
  label: string;
}
interface ApiEdge {
  source_type: string;
  source_id: number;
  target_type: string;
  target_id: number;
  edge_type: string;
  weight: number;
}

const EDGE_DESCRIPTIONS: Record<string, string> = {
  cross_ref: 'Scripture cross-reference — scholars agree these passages reference each other',
  twot_family: 'Same Hebrew word root (TWOT) — these words share etymological origin',
  nave_topic: 'Nave\'s Topical Bible — this verse is categorized under this theme',
  nave_shared: 'Shared topic — these verses appear under the same Nave\'s topic',
  semantic_sim: 'Semantic similarity — AI embeddings show these have similar meaning (>85%)',
  strongs_sim: 'Lexicon similarity — these Hebrew/Greek words have similar definitions',
};

const EDGE_SHORT: Record<string, string> = {
  cross_ref: 'Cross-reference',
  twot_family: 'Word family',
  nave_topic: 'Topic link',
  nave_shared: 'Shared topic',
  semantic_sim: 'Semantic match',
  strongs_sim: 'Word similarity',
};

interface GraphInfoPanelProps {
  nodes: ApiNode[];
  edges: ApiEdge[];
  centerType: string | null;
  centerId: number | null;
  hoveredNode: ApiNode | null;
  hoveredEdges: ApiEdge[];
}

export function GraphInfoPanel({ nodes, edges, centerType, centerId, hoveredNode, hoveredEdges }: GraphInfoPanelProps) {
  // Edge type breakdown
  const edgeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of edges) {
      counts[e.edge_type] = (counts[e.edge_type] || 0) + 1;
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [edges]);

  // Node type breakdown
  const nodeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const n of nodes) {
      counts[n.node_type] = (counts[n.node_type] || 0) + 1;
    }
    return counts;
  }, [nodes]);

  if (nodes.length === 0) {
    return (
      <div className="p-4 text-gray-500 text-xs">
        Click a verse in the Galaxy view, then switch to Knowledge Graph to explore its connections.
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3 overflow-y-auto max-h-full text-xs">
      {/* Center node info */}
      <div className="border-b border-white/5 pb-2">
        <h4 className="text-gray-400 uppercase tracking-wider text-[10px] mb-1">Exploring</h4>
        <div className="text-white font-medium">
          {centerType === 'theme' ? '🏷️' : centerType === 'strongs' ? '📖' : '📜'}{' '}
          {centerType} #{centerId}
        </div>
      </div>

      {/* Network summary */}
      <div>
        <h4 className="text-gray-400 uppercase tracking-wider text-[10px] mb-1">Network</h4>
        <div className="text-gray-300">
          {nodes.length} nodes · {edges.length} connections
        </div>
        <div className="flex gap-3 mt-1 text-[10px] text-gray-500">
          {nodeCounts.verse && <span>{nodeCounts.verse} verses</span>}
          {nodeCounts.theme && <span>{nodeCounts.theme} themes</span>}
          {nodeCounts.strongs && <span>{nodeCounts.strongs} words</span>}
        </div>
      </div>

      {/* Edge type legend with counts */}
      <div>
        <h4 className="text-gray-400 uppercase tracking-wider text-[10px] mb-2">Connection Types</h4>
        <div className="space-y-1.5">
          {edgeCounts.map(([type, count]) => (
            <div key={type} className="group">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-0.5 rounded flex-shrink-0"
                  style={{ backgroundColor: EDGE_TYPE_COLORS[type] || '#666' }}
                />
                <span className="text-gray-300">{EDGE_SHORT[type] || type}</span>
                <span className="text-gray-600 ml-auto">{count}</span>
              </div>
              <p className="text-[10px] text-gray-600 ml-5 hidden group-hover:block">
                {EDGE_DESCRIPTIONS[type]}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Hovered node detail */}
      {hoveredNode && (
        <div className="border-t border-white/5 pt-2">
          <h4 className="text-gray-400 uppercase tracking-wider text-[10px] mb-1">Hovered</h4>
          <div className="text-white text-xs">{hoveredNode.label}</div>
          <div className="text-[10px] text-gray-500 mt-0.5">
            {hoveredNode.node_type} #{hoveredNode.node_id}
          </div>
          {hoveredEdges.length > 0 && (
            <div className="mt-1.5 space-y-0.5">
              <div className="text-[10px] text-gray-500">{hoveredEdges.length} connections:</div>
              {hoveredEdges.slice(0, 5).map((e, i) => (
                <div key={i} className="flex items-center gap-1.5 text-[10px]">
                  <div
                    className="w-2 h-0.5 rounded flex-shrink-0"
                    style={{ backgroundColor: EDGE_TYPE_COLORS[e.edge_type] || '#666' }}
                  />
                  <span className="text-gray-400">{EDGE_SHORT[e.edge_type]}</span>
                  <span className="text-gray-600">w={e.weight.toFixed(2)}</span>
                </div>
              ))}
              {hoveredEdges.length > 5 && (
                <div className="text-[10px] text-gray-600">+{hoveredEdges.length - 5} more</div>
              )}
            </div>
          )}
        </div>
      )}

      {/* How to read hint */}
      <div className="border-t border-white/5 pt-2 text-[10px] text-gray-600 space-y-1">
        <p><strong className="text-gray-500">Line colors</strong> show connection type (hover legend above)</p>
        <p><strong className="text-gray-500">Green nodes</strong> = themes/topics</p>
        <p><strong className="text-gray-500">Blue nodes</strong> = verses</p>
        <p><strong className="text-gray-500">Gold nodes</strong> = Hebrew/Greek words</p>
      </div>
    </div>
  );
}
