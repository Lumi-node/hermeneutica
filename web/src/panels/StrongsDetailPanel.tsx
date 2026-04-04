import { useState, useEffect } from 'react';
import { apiFetch } from '@/api/client';
import { useSceneStore } from '@/stores/sceneStore';

interface StrongsDetailResponse {
  strongs_id: number;
  strongs_number: string;
  language: string;
  original_word: string;
  transliteration: string;
  pronunciation: string | null;
  root_definition: string;
  detailed_definition: string;
  kjv_usage: string | null;
  part_of_speech: string | null;
  root_strongs: string | null;
  usage_count: number;
  sample_verses: { verse_id: number; reference: string; english_gloss: string; text_preview: string }[];
}

export function StrongsDetailPanel() {
  const { selectedNodeId, selectedNodeType } = useSceneStore();
  const [detail, setDetail] = useState<StrongsDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showFull, setShowFull] = useState(false);

  useEffect(() => {
    if (selectedNodeType !== 'strongs' || !selectedNodeId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    apiFetch<StrongsDetailResponse>(`/strongs/${selectedNodeId}`)
      .then((data) => { if (!cancelled) setDetail(data); })
      .catch(() => { if (!cancelled) setDetail(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [selectedNodeId, selectedNodeType]);

  if (selectedNodeType !== 'strongs' || !selectedNodeId) return null;
  if (loading) return <div className="p-3 text-gray-400 text-xs">Loading...</div>;
  if (!detail) return <div className="p-3 text-gray-500 text-xs">Word not found</div>;

  const isHebrew = detail.language === 'heb';

  return (
    <div className="p-3 space-y-3 overflow-y-auto max-h-full text-xs">
      {/* Header */}
      <div>
        <div className="flex items-baseline gap-2 mb-1">
          <span className={`text-2xl ${isHebrew ? 'text-amber-300' : 'text-blue-300'}`}>
            {detail.original_word}
          </span>
          <span className={`text-[9px] px-1.5 py-0.5 rounded ${
            isHebrew ? 'bg-amber-500/15 text-amber-400' : 'bg-blue-500/15 text-blue-400'
          }`}>
            {isHebrew ? 'Hebrew' : 'Greek'}
          </span>
        </div>
        <div className="text-sm text-gray-300">{detail.transliteration}</div>
        {detail.pronunciation && (
          <div className="text-[10px] text-gray-500 italic">{detail.pronunciation}</div>
        )}
        <div className="text-[10px] text-gray-600 mt-1">{detail.strongs_number}</div>
      </div>

      {/* Quick stats */}
      <div className="flex gap-2">
        {detail.part_of_speech && (
          <span className="text-[9px] bg-white/5 text-gray-400 px-1.5 py-0.5 rounded">{detail.part_of_speech}</span>
        )}
        <span className="text-[9px] bg-white/5 text-gray-400 px-1.5 py-0.5 rounded">
          Used {detail.usage_count} times
        </span>
        {detail.root_strongs && (
          <span className="text-[9px] bg-white/5 text-gray-400 px-1.5 py-0.5 rounded">
            Root: {detail.root_strongs}
          </span>
        )}
      </div>

      {/* Definition */}
      <div>
        <SectionLabel>Definition</SectionLabel>
        <p className="text-gray-300 leading-relaxed">{detail.root_definition}</p>
      </div>

      {/* Full definition (collapsible) */}
      {detail.detailed_definition && detail.detailed_definition !== detail.root_definition && (
        <div>
          <button
            onClick={() => setShowFull(!showFull)}
            className="text-[10px] text-accent-blue hover:text-white transition"
          >
            {showFull ? 'Hide' : 'Show'} full BDB/Thayer definition
          </button>
          {showFull && (
            <p className="mt-1.5 text-[10px] text-gray-500 leading-relaxed max-h-32 overflow-y-auto">
              {detail.detailed_definition}
            </p>
          )}
        </div>
      )}

      {/* KJV usage */}
      {detail.kjv_usage && (
        <div>
          <SectionLabel>KJV Translations</SectionLabel>
          <p className="text-[10px] text-gray-500 leading-relaxed">{detail.kjv_usage}</p>
        </div>
      )}

      {/* Sample verses */}
      {detail.sample_verses && detail.sample_verses.length > 0 && (
        <div>
          <SectionLabel>Used in ({detail.sample_verses.length} samples)</SectionLabel>
          <div className="space-y-1.5 max-h-36 overflow-y-auto">
            {detail.sample_verses.map((sv) => (
              <div key={sv.verse_id} className="group">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-[10px] font-medium text-accent-blue">{sv.reference}</span>
                  <span className="text-[10px] text-accent-gold">"{sv.english_gloss}"</span>
                </div>
                <p className="text-[10px] text-gray-600 truncate group-hover:whitespace-normal">
                  {sv.text_preview}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-1">{children}</div>;
}
