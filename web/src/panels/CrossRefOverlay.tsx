import { useState, useCallback } from 'react';
import { apiFetch } from '@/api/client';
import { useDataStore } from '@/stores/dataStore';
import type { CrossRefArc } from '@/types/crossref';

const PRESETS = [
  { id: 'ot_to_nt', label: 'OT Promises → NT', color: '#FFD700', icon: '✦', total: '~55K' },
  { id: 'nt_to_ot', label: 'NT Quoting OT', color: '#87CEEB', icon: '↩', total: '~39K' },
  { id: 'prophets_to_gospels', label: 'Prophets → Gospels', color: '#FF8C00', icon: '🔥', total: '~8K' },
  { id: 'psalms_to_nt', label: 'Psalms → NT', color: '#DDA0DD', icon: '♪', total: '~5K' },
  { id: 'torah_to_nt', label: 'Torah → NT', color: '#CD853F', icon: '📜', total: '~12K' },
  { id: 'intra_ot', label: 'Within OT', color: '#DAA520', icon: '⟷', total: '~170K' },
  { id: 'intra_nt', label: 'Within NT', color: '#6495ED', icon: '⟷', total: '~25K' },
] as const;

interface OverlayArc {
  source_verse_id: number;
  target_verse_id: number;
  source_x: number; source_y: number; source_z: number;
  target_x: number; target_y: number; target_z: number;
  relevance_score: number;
  source_book: string;
  target_book: string;
}

interface OverlayResponse {
  preset: string;
  arc_count: number;
  arcs: OverlayArc[];
  description: string;
}

interface Props {
  onArcsLoaded: (arcs: CrossRefArc[], color: string) => void;
  onClear: () => void;
}

export function CrossRefOverlayControls({ onArcsLoaded, onClear }: Props) {
  const versePoints = useDataStore(s => s.versePoints);
  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(true);
  const [loading, setLoading] = useState(false);
  const [description, setDescription] = useState('');
  const [loadedCount, setLoadedCount] = useState(0);

  const loadPreset = useCallback(async (presetId: string, all: boolean) => {
    const preset = PRESETS.find(p => p.id === presetId);
    if (!preset) return;

    if (activePreset === presetId && showAll === all) {
      setActivePreset(null);
      setDescription('');
      setLoadedCount(0);
      onClear();
      return;
    }

    setLoading(true);
    setActivePreset(presetId);
    setShowAll(all);
    try {
      const data = await apiFetch<OverlayResponse>('/explore/crossref-overlay', {
        preset: presetId,
        limit: all ? '60000' : '500',
        min_relevance: '0',
      });
      setDescription(data.description);
      setLoadedCount(data.arc_count);

      // Center coords to match Galaxy
      const SCALE = 10;
      let cx = 0, cy = 0, cz = 0;
      if (versePoints) {
        const p = versePoints.positions;
        const n = versePoints.count;
        for (let i = 0; i < n; i++) {
          cx += p[i * 3]; cy += p[i * 3 + 1]; cz += p[i * 3 + 2];
        }
        cx /= n; cy /= n; cz /= n;
      }

      const arcs: CrossRefArc[] = data.arcs.map(a => ({
        sourceVerseId: a.source_verse_id,
        targetVerseId: a.target_verse_id,
        sourceX: (a.source_x - cx) * SCALE,
        sourceY: (a.source_y - cy) * SCALE,
        sourceZ: (a.source_z - cz) * SCALE,
        targetX: (a.target_x - cx) * SCALE,
        targetY: (a.target_y - cy) * SCALE,
        targetZ: (a.target_z - cz) * SCALE,
        relevanceScore: a.relevance_score,
      }));
      onArcsLoaded(arcs, preset.color);
    } catch (e) {
      console.error('Failed to load overlay:', e);
    }
    setLoading(false);
  }, [activePreset, showAll, onArcsLoaded, onClear, versePoints]);

  return (
    <div className="space-y-1.5">
      <div className="text-[9px] text-gray-500 uppercase tracking-wider">
        Cross-Reference Threads
      </div>

      {/* Preset buttons */}
      {PRESETS.map((preset) => (
        <div key={preset.id}>
          <button
            onClick={() => loadPreset(preset.id, showAll)}
            disabled={loading}
            className={`w-full flex items-center gap-1.5 text-left px-2 py-1 rounded transition text-[10px] ${
              activePreset === preset.id
                ? 'bg-white/10'
                : 'hover:bg-white/5'
            }`}
            style={{ color: activePreset === preset.id ? preset.color : undefined }}
          >
            <span className="text-[11px]">{preset.icon}</span>
            <span className={`flex-1 ${activePreset === preset.id ? '' : 'text-gray-400'}`}>
              {preset.label}
            </span>
          </button>

          {/* Show All toggle — only for active preset */}
          {activePreset === preset.id && !loading && (
            <div className="ml-6 mt-0.5 mb-1">
              <button
                onClick={() => loadPreset(preset.id, !showAll)}
                className="text-[9px] text-gray-500 hover:text-white transition"
              >
                {showAll ? `Showing all ${loadedCount.toLocaleString()}` : `Top 500 of ${preset.total}`}
                {' — '}
                <span className="underline">{showAll ? 'show top only' : 'show all'}</span>
              </button>
            </div>
          )}
        </div>
      ))}

      {loading && <div className="text-[9px] text-gray-500">Loading...</div>}

      {description && (
        <p className="text-[8px] text-gray-600 leading-relaxed italic">{description}</p>
      )}
    </div>
  );
}
