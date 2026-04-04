import { useState, useEffect } from 'react';
import { apiFetch } from '@/api/client';
import { useSceneStore } from '@/stores/sceneStore';
import { EthicsRadar } from '@/charts/EthicsRadar';

interface VerseDetailResponse {
  verse_id: number;
  book_name: string;
  book_abbreviation: string;
  chapter_number: number;
  verse_number: number;
  testament: string;
  text: string;
  word_alignments: {
    word_position: number;
    original_word: string;
    transliteration: string | null;
    english_gloss: string;
    strongs_number: string | null;
    morphology_code: string | null;
    root_definition: string | null;
  }[];
  cross_references: {
    target_verse_id: number;
    target_ref: string;
    relevance_score: number;
    text_preview: string | null;
  }[];
  nave_topics: { topic: string }[];
}

interface ClassificationResponse {
  chapter_id: number;
  book_name: string;
  chapter_number: number;
  genre: string;
  genre_confidence: number;
  themes: string[];
  teaching_type: string;
  ethics_scores: { ethics_subset: string; relevance_score: number }[];
  principles: { principle_text: string; principle_order: number }[];
}

// Convert dot-notation ref to readable format
function formatRef(ref: string): string {
  return ref
    .replace(/\./g, ' ')
    .replace(/(\d)\s(\d)/, '$1:$2')
    .replace(/^1 T /, '1 Thess ')
    .replace(/^2 T /, '2 Thess ')
    .replace(/^1 S /, '1 Sam ')
    .replace(/^2 S /, '2 Sam ')
    .replace(/^1 K /, '1 Kgs ')
    .replace(/^2 K /, '2 Kgs ')
    .replace(/^1 C /, '1 Chr ')
    .replace(/^2 C /, '2 Chr ')
    .replace(/^Mat /, 'Matt ')
    .replace(/^Mar /, 'Mark ')
    .replace(/^Joh /, 'John ')
    .replace(/^Luk /, 'Luke ')
    .replace(/^Rom /, 'Rom ')
    .replace(/^Rev /, 'Rev ')
    .replace(/^Gen /, 'Gen ')
    .replace(/^Exo /, 'Exod ')
    .replace(/^Lev /, 'Lev ')
    .replace(/^Deu /, 'Deut ')
    .replace(/^Psa /, 'Ps ')
    .replace(/^Pro /, 'Prov ')
    .replace(/^Isa /, 'Isa ')
    .replace(/^Jer /, 'Jer ')
    .replace(/^Eze /, 'Ezek ')
    .replace(/^Dan /, 'Dan ')
    .replace(/^Hos /, 'Hos ')
    .replace(/^Joe /, 'Joel ')
    .replace(/^Amo /, 'Amos ');
}

const TEACHING_LABELS: Record<string, string> = {
  explicit_command: 'Direct command',
  implicit_principle: 'Implicit principle',
  exemplar_narrative: 'By example',
  metaphorical_wisdom: 'Metaphor / wisdom',
};

export function VerseDetailPanel() {
  const { selectedNodeId, selectedNodeType } = useSceneStore();
  const [detail, setDetail] = useState<VerseDetailResponse | null>(null);
  const [classification, setClassification] = useState<ClassificationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showInterlinear, setShowInterlinear] = useState(false);

  useEffect(() => {
    if (selectedNodeType !== 'verse' || !selectedNodeId) {
      setDetail(null);
      setClassification(null);
      return;
    }
    let cancelled = false;
    setLoading(true);

    // Fetch verse detail
    apiFetch<VerseDetailResponse>(`/verses/${selectedNodeId}`)
      .then((data) => { if (!cancelled) setDetail(data); })
      .catch(() => { if (!cancelled) setDetail(null); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [selectedNodeId, selectedNodeType]);

  // Fetch hermeneutics classification for this chapter
  useEffect(() => {
    if (!detail) { setClassification(null); return; }
    let cancelled = false;
    apiFetch<ClassificationResponse>(
      `/hermeneutics/by-ref/${encodeURIComponent(detail.book_name)}/${detail.chapter_number}`
    )
      .then((data) => { if (!cancelled) setClassification(data); })
      .catch(() => { if (!cancelled) setClassification(null); });
    return () => { cancelled = true; };
  }, [detail]);

  if (selectedNodeType !== 'verse' || !selectedNodeId) return null;
  if (loading) return <div className="p-3 text-gray-400 text-xs">Loading...</div>;
  if (!detail) return <div className="p-3 text-gray-500 text-xs">Verse not found</div>;

  const topics = detail.nave_topics ?? [];
  const words = detail.word_alignments ?? [];
  const xrefs = detail.cross_references ?? [];

  // Build ethics scores map for radar chart
  const ethicsMap: Record<string, number> = {};
  if (classification?.ethics_scores) {
    for (const s of classification.ethics_scores) {
      ethicsMap[s.ethics_subset] = s.relevance_score;
    }
  }

  return (
    <div className="p-3 space-y-3 overflow-y-auto max-h-full text-xs">
      {/* Verse header + text */}
      <div>
        <div className="flex items-baseline gap-2 mb-1">
          <h3 className="text-white font-semibold text-sm">
            {detail.book_name} {detail.chapter_number}:{detail.verse_number}
          </h3>
          <span className={`text-[9px] px-1.5 py-0.5 rounded ${
            detail.testament === 'OT' ? 'bg-amber-500/15 text-amber-400' : 'bg-blue-500/15 text-blue-400'
          }`}>
            {detail.testament}
          </span>
        </div>
        <p className="text-gray-300 text-xs leading-relaxed">{detail.text}</p>
      </div>

      {/* Topics */}
      {topics.length > 0 && (
        <div>
          <SectionLabel>Topics</SectionLabel>
          <div className="flex flex-wrap gap-1">
            {topics.map((t) => (
              <span key={t.topic} className="text-[10px] bg-accent-green/15 text-accent-green px-1.5 py-0.5 rounded">
                {t.topic}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Classification / Hermeneutics */}
      {classification && (
        <div className="bg-white/3 rounded-lg p-2.5 space-y-2">
          <SectionLabel>Chapter Classification</SectionLabel>
          <div className="flex flex-wrap gap-1.5">
            <Tag color="purple">{classification.genre.replace(/_/g, ' ')}</Tag>
            <Tag color="blue">{TEACHING_LABELS[classification.teaching_type] ?? classification.teaching_type}</Tag>
          </div>
          {classification.themes?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {classification.themes.map(t => (
                <span key={t} className="text-[9px] bg-white/5 text-gray-400 px-1.5 py-0.5 rounded">{t}</span>
              ))}
            </div>
          )}

          {/* Ethics radar */}
          {Object.keys(ethicsMap).length > 0 && (
            <div>
              <div className="text-[9px] text-gray-500 mb-1">Ethics Relevance</div>
              <EthicsRadar scores={ethicsMap} size={120} />
            </div>
          )}

          {/* Distilled principles */}
          {classification.principles?.length > 0 && (
            <div>
              <div className="text-[9px] text-gray-500 mb-1">Distilled Principles</div>
              <div className="space-y-1">
                {classification.principles.map((p, i) => (
                  <p key={i} className="text-[10px] text-gray-300 leading-relaxed pl-2 border-l border-accent-gold/30">
                    {p.principle_text}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Interlinear */}
      {words.length > 0 && (
        <div>
          <button
            onClick={() => setShowInterlinear(!showInterlinear)}
            className="text-[11px] text-accent-blue hover:text-white transition"
          >
            {showInterlinear ? 'Hide' : 'Show'} Interlinear ({words.length} words)
          </button>
          {showInterlinear && (
            <div className="mt-1.5 space-y-1.5 max-h-40 overflow-y-auto">
              {words.map((wa) => (
                <div key={wa.word_position} className="bg-white/3 rounded p-1.5">
                  <div className="flex items-baseline gap-2">
                    <span className="text-accent-gold font-mono text-[11px]">{wa.original_word}</span>
                    <span className="text-gray-500 text-[9px]">{wa.transliteration}</span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span className="text-gray-300 text-[10px]">{wa.english_gloss}</span>
                    {wa.strongs_number && (
                      <span className="text-gray-600 text-[9px]">{wa.strongs_number}</span>
                    )}
                  </div>
                  {wa.root_definition && (
                    <p className="text-gray-600 text-[8px] mt-0.5 truncate">{wa.root_definition}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Cross-references */}
      {xrefs.length > 0 && (
        <div>
          <SectionLabel>Cross-References ({xrefs.length})</SectionLabel>
          <div className="space-y-1.5 max-h-36 overflow-y-auto">
            {xrefs.map((cr, i) => (
              <div key={cr.target_verse_id} className="group">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-[10px] font-medium text-accent-blue">{formatRef(cr.target_ref)}</span>
                  {i === 0 && <span className="text-[8px] text-gray-600">strongest</span>}
                </div>
                <p className="text-[10px] text-gray-500 leading-relaxed truncate group-hover:whitespace-normal">
                  {cr.text_preview}
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

function Tag({ children, color }: { children: React.ReactNode; color: 'purple' | 'blue' | 'green' }) {
  const colors = {
    purple: 'bg-accent-purple/15 text-accent-purple',
    blue: 'bg-accent-blue/15 text-accent-blue',
    green: 'bg-accent-green/15 text-accent-green',
  };
  return <span className={`text-[9px] px-1.5 py-0.5 rounded ${colors[color]}`}>{children}</span>;
}
