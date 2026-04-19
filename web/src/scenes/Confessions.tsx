import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '@/api/client';
import { useSceneStore } from '@/stores/sceneStore';

// Types
interface ConfessionSummary {
  id: number; name: string; abbreviation: string; confession_type: string;
  tradition: string; year: number; authors: string | null;
  item_count: number; proof_text_count: number;
}

interface ProofText {
  proof_group: string; osis_ref: string; verse_id: number | null;
  verse_text: string | null; book_name: string | null;
  chapter_number: number | null; verse_number: number | null;
}

interface ConfessionItem {
  id: number; item_number: number; item_type: string; title: string | null;
  question_text: string | null; answer_text: string | null;
  answer_with_proofs: string | null; sort_order: number;
  proof_texts: ProofText[]; children: ConfessionItem[];
}

interface ConfessionDetail {
  id: number; name: string; abbreviation: string; confession_type: string;
  tradition: string; year: number; authors: string | null; items: ConfessionItem[];
}

const TRADITION_COLORS: Record<string, string> = {
  reformed: 'bg-emerald-500/15 text-emerald-400',
  presbyterian: 'bg-blue-500/15 text-blue-400',
};

const TYPE_LABELS: Record<string, string> = {
  confession: 'Confession', catechism: 'Catechism', canon: 'Canon',
};

export function Confessions() {
  const [confessions, setConfessions] = useState<ConfessionSummary[]>([]);
  const [selected, setSelected] = useState<ConfessionDetail | null>(null);
  const [selectedItem, setSelectedItem] = useState<ConfessionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const setActiveScene = useSceneStore(s => s.setActiveScene);
  const selectNode = useSceneStore(s => s.selectNode);

  useEffect(() => {
    apiFetch<ConfessionSummary[]>('/confessions')
      .then(setConfessions).catch(console.error).finally(() => setLoading(false));
  }, []);

  const loadConfession = useCallback(async (id: number) => {
    setLoading(true);
    setSelectedItem(null);
    try {
      const data = await apiFetch<ConfessionDetail>(`/confessions/${id}`);
      setSelected(data);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  // Search
  useEffect(() => {
    if (searchQuery.length < 3) { setSearchResults([]); return; }
    const t = setTimeout(async () => {
      try {
        const data = await apiFetch<any[]>('/confessions/search', { q: searchQuery, limit: '20' });
        setSearchResults(data);
      } catch { setSearchResults([]); }
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

  const jumpToVerse = (verseId: number) => {
    selectNode('verse', verseId);
    setActiveScene('galaxy');
  };

  // Not viewing a confession — show the landing
  if (!selected) {
    return (
      <div className="h-full overflow-y-auto bg-bg-primary">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
          <h1 className="text-xl sm:text-2xl font-bold text-white mb-1">Creeds & Confessions</h1>
          <p className="text-xs sm:text-sm text-gray-500 mb-6">
            6 historic Reformed confessions and catechisms — 736 items with 10,094 proof-text links to Scripture.
            Explore how the church has systematically interpreted the Bible.
          </p>

          {/* Search */}
          <div className="relative mb-6">
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search all confessions... (justification, election, sacraments, prayer)"
              className="w-full bg-white/5 text-white text-sm rounded-lg px-4 py-2.5 border border-white/10 focus:border-accent-blue outline-none" />
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-panel rounded-lg border border-white/10 max-h-60 overflow-y-auto z-20">
                {searchResults.map((r: any) => (
                  <button key={r.id} onClick={() => { loadConfession(r.confession_id); setSearchQuery(''); setSearchResults([]); }}
                    className="w-full text-left px-4 py-2.5 hover:bg-white/5 transition border-b border-white/5 last:border-0">
                    <div className="flex items-baseline gap-2">
                      <span className="text-[10px] font-medium text-accent-blue">{r.abbreviation}</span>
                      <span className="text-xs text-gray-300">{r.item_type === 'question' ? `Q. ${r.item_number}` : r.title || `§${r.item_number}`}</span>
                    </div>
                    <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2">{r.answer_preview || r.question_preview}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Confession cards */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {confessions.map(c => (
              <button key={c.id} onClick={() => loadConfession(c.id)}
                className="text-left bg-white/3 hover:bg-white/5 border border-white/5 hover:border-white/10 rounded-lg p-4 transition group">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-medium text-white group-hover:text-accent-gold transition">{c.name}</h3>
                  <span className="text-xs text-gray-600 flex-shrink-0 ml-2">{c.year}</span>
                </div>
                <div className="flex gap-1.5 mb-2 flex-wrap">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded ${TRADITION_COLORS[c.tradition] || 'bg-white/5 text-gray-400'}`}>{c.tradition}</span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{TYPE_LABELS[c.confession_type] || c.confession_type}</span>
                </div>
                <div className="text-[10px] text-gray-600">{c.item_count} items · {c.proof_text_count.toLocaleString()} proof texts</div>
              </button>
            ))}
          </div>

          {/* Era timeline */}
          <div className="mt-8 flex items-center gap-2 text-[10px] text-gray-600">
            <span className="text-gray-500">Timeline:</span>
            {confessions.sort((a, b) => a.year - b.year).map(c => (
              <button key={c.id} onClick={() => loadConfession(c.id)}
                className="bg-white/5 hover:bg-white/10 px-2 py-1 rounded transition">
                {c.year} {c.abbreviation}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Three-column confession reader
  return (
    <div className="h-full flex flex-col sm:flex-row bg-bg-primary overflow-hidden">

      {/* Mobile: horizontal pill bar for confession nav */}
      <div className="sm:hidden bg-bg-panel/80 border-b border-white/5 flex items-center gap-1 overflow-x-auto px-2 py-2 flex-shrink-0">
        <button
          onClick={() => setSelected(null)}
          className="text-xs text-gray-300 hover:text-white px-3 py-1.5 rounded bg-white/5 min-h-[36px] whitespace-nowrap flex-shrink-0"
        >
          ←
        </button>
        {confessions.map(c => (
          <button
            key={c.id}
            onClick={() => loadConfession(c.id)}
            className={`text-xs px-3 py-1.5 rounded whitespace-nowrap flex-shrink-0 min-h-[36px] transition ${
              selected.id === c.id ? 'bg-white/10 text-white' : 'text-gray-400 bg-white/5'
            }`}
          >
            {c.abbreviation}
          </button>
        ))}
      </div>

      {/* Desktop: Left confession nav */}
      <div className="hidden sm:block sm:w-40 flex-shrink-0 bg-bg-panel/80 border-r border-white/5 overflow-y-auto">
        <div className="p-2">
          <button onClick={() => setSelected(null)} className="text-[10px] text-gray-500 hover:text-white mb-2 block">← Back</button>
          {confessions.map(c => (
            <button key={c.id} onClick={() => loadConfession(c.id)}
              className={`w-full text-left px-2 py-1.5 rounded text-[11px] mb-0.5 transition ${
                selected.id === c.id ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
              }`}>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${selected.id === c.id ? 'bg-accent-gold' : 'bg-gray-700'}`} />
                {c.abbreviation}
              </div>
              <div className="text-[9px] text-gray-600 ml-3">{c.name}</div>
            </button>
          ))}
          <div className="mt-3 pt-2 border-t border-white/5">
            <div className="text-[8px] text-gray-600 uppercase tracking-wider mb-1">Era</div>
            {confessions.sort((a, b) => a.year - b.year).map(c => (
              <div key={c.id} className={`text-[9px] py-0.5 pl-2 border-l-2 ${
                selected.id === c.id ? 'border-accent-gold text-white' : 'border-gray-800 text-gray-600'
              }`}>
                {c.year} {c.abbreviation}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Center: Document reader */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6">
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">{selected.name}</h2>
            <div className="flex gap-2 mt-1 flex-wrap">
              <span className="text-[10px] text-gray-500">{selected.year}</span>
              <span className={`text-[9px] px-1.5 py-0.5 rounded ${TRADITION_COLORS[selected.tradition] || ''}`}>{selected.tradition}</span>
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400">{TYPE_LABELS[selected.confession_type]}</span>
              {selected.authors && <span className="text-[10px] text-gray-600">{selected.authors}</span>}
            </div>
          </div>

          {/* Items */}
          {selected.items.map(item => (
            <DocumentItem key={item.id} item={item} depth={0}
              confessionType={selected.confession_type}
              onSelectItem={setSelectedItem}
              selectedItemId={selectedItem?.id ?? null} />
          ))}
        </div>
      </div>

      {/* Right: Data panel — desktop only */}
      <div className="sm:w-80 flex-shrink-0 bg-bg-panel/80 border-l border-white/5 overflow-y-auto hidden sm:block">
        <div className="p-3">
          {selectedItem ? (
            <ProofTextData
              selectedItem={selectedItem}
              jumpToVerse={jumpToVerse}
            />
          ) : (
            <div className="text-xs text-gray-600 py-4">
              <p className="mb-2">Click a section or question to see its proof texts.</p>
              <p>Then click any verse to see <strong className="text-gray-400">why</strong> it supports the doctrine — word-level analysis, semantic similarity, and cross-confession citations.</p>
            </div>
          )}
        </div>
      </div>

      {/* Mobile proof-text bottom sheet */}
      {selectedItem && (
        <>
          <div
            onClick={() => setSelectedItem(null)}
            className="sm:hidden fixed inset-0 bg-black/60 z-40"
            aria-hidden="true"
          />
          <div className="sm:hidden fixed left-0 right-0 bottom-0 top-[30%] rounded-t-xl border-t border-white/10 bg-bg-panel/98 backdrop-blur-sm z-50 flex flex-col">
            {/* Grab handle */}
            <div className="flex justify-center pt-2 pb-1 flex-shrink-0">
              <div className="h-1 w-10 rounded-full bg-white/20" />
            </div>
            <div className="flex items-center justify-between px-3 pb-2 border-b border-white/5 flex-shrink-0">
              <span className="text-xs text-gray-400 uppercase tracking-wider">Proof Texts</span>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-gray-400 hover:text-white text-sm px-3 py-1.5 rounded bg-white/5 min-h-[36px]"
              >
                Done
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              <ProofTextData
                selectedItem={selectedItem}
                jumpToVerse={jumpToVerse}
              />
            </div>
          </div>
        </>
      )}

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/80 z-40">
          <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}

// Shared content for both desktop right-panel and mobile bottom-sheet
function ProofTextData({ selectedItem, jumpToVerse }: {
  selectedItem: ConfessionItem; jumpToVerse: (id: number) => void;
}) {
  return (
    <div className="space-y-3">
      <div>
        <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-1">Selected</div>
        <div className="text-xs text-white font-medium">
          {selectedItem.item_type === 'question' ? `Q. ${selectedItem.item_number}` :
           selectedItem.title || `§ ${selectedItem.item_number}`}
        </div>
      </div>

      {selectedItem.proof_texts.length > 0 && (
        <div>
          <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-2">
            Proof Texts ({selectedItem.proof_texts.length})
            <span className="text-gray-700 normal-case ml-1">— tap to analyze</span>
          </div>
          <ProofTextAccordion
            proofs={selectedItem.proof_texts}
            itemId={selectedItem.id}
            onJumpToVerse={jumpToVerse}
          />
        </div>
      )}
    </div>
  );
}

// Document item renderer
function DocumentItem({ item, depth, confessionType, onSelectItem, selectedItemId }: {
  item: ConfessionItem; depth: number; confessionType: string;
  onSelectItem: (item: ConfessionItem) => void; selectedItemId: number | null;
}) {
  const isHeading = item.item_type === 'chapter' || item.item_type === 'head';
  const isQuestion = item.item_type === 'question';
  const isBody = item.item_type === 'section' || item.item_type === 'article';
  const isSelected = selectedItemId === item.id;
  const hasProofs = item.proof_texts.length > 0;

  const headingLabel = item.item_type === 'head' ? 'Head' : item.item_type === 'chapter' ? 'Chapter' : '';

  return (
    <div className={depth > 0 ? 'ml-4' : 'mb-4'}>
      <div
        onClick={() => onSelectItem(item)}
        className={`cursor-pointer rounded-lg transition p-3 ${
          isSelected ? 'bg-accent-blue/10 ring-1 ring-accent-blue/20' : 'hover:bg-white/3'
        } ${isHeading ? 'mb-2' : 'mb-1'}`}
      >
        {isHeading && (
          <h3 className="text-sm font-semibold text-white mb-1">
            {confessionType !== 'catechism' && headingLabel && `${headingLabel} ${item.item_number}: `}
            {item.title}
          </h3>
        )}

        {isQuestion && (
          <div>
            <div className="text-xs text-accent-gold font-medium mb-1.5">
              Q. {item.item_number}. {item.question_text}
            </div>
            <p className="text-xs text-gray-300 leading-relaxed">
              <span className="text-gray-500 font-medium">A. </span>
              {renderTextWithProofMarkers(item.answer_text || '', item.proof_texts)}
            </p>
          </div>
        )}

        {isBody && (
          <div>
            <span className="text-[10px] text-gray-500 font-medium mr-1">
              {item.item_type === 'article' ? `Art. ${item.item_number}.` : `§${item.item_number}.`}
            </span>
            <span className="text-xs text-gray-300 leading-relaxed">
              {renderTextWithProofMarkers(item.answer_text || '', item.proof_texts)}
            </span>
          </div>
        )}

        {hasProofs && (
          <div className="flex gap-1 mt-1.5 flex-wrap">
            {getUniqueGroups(item.proof_texts).map(g => (
              <span key={g} className="text-[8px] bg-accent-blue/10 text-accent-blue/70 px-1 py-0.5 rounded cursor-help"
                title={item.proof_texts.filter(p => p.proof_group === g).map(p => p.osis_ref).join(', ')}>
                [{g}]
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Children */}
      {item.children.map(child => (
        <DocumentItem key={child.id} item={child} depth={depth + 1}
          confessionType={confessionType} onSelectItem={onSelectItem}
          selectedItemId={selectedItemId} />
      ))}
    </div>
  );
}

// Helpers
function groupProofs(proofs: ProofText[]): [string, ProofText[]][] {
  const groups = new Map<string, ProofText[]>();
  for (const p of proofs) {
    const list = groups.get(p.proof_group) || [];
    list.push(p);
    groups.set(p.proof_group, list);
  }
  return [...groups.entries()];
}

function getUniqueGroups(proofs: ProofText[]): string[] {
  return [...new Set(proofs.map(p => p.proof_group))].sort();
}

function renderTextWithProofMarkers(text: string, _proofs: ProofText[]): string {
  return text;
}

// Proof Text Accordion with deep analysis
interface AnalysisData {
  verse_id: number;
  reference: string;
  text: string;
  words: { position: number; original: string; transliteration: string; gloss: string; strongs: string; definition: string | null; part_of_speech: string | null; language: string | null }[];
  cross_citations: { abbreviation: string; confession_name: string; item_type: string; item_number: number; title: string | null; context: string | null }[];
  semantic_similarity: number | null;
}

function ProofTextAccordion({ proofs, itemId, onJumpToVerse }: {
  proofs: ProofText[]; itemId: number; onJumpToVerse: (id: number) => void;
}) {
  const [expandedVerse, setExpandedVerse] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  const toggleVerse = async (verseId: number | null) => {
    if (!verseId || expandedVerse === verseId) {
      setExpandedVerse(null);
      setAnalysis(null);
      return;
    }
    setExpandedVerse(verseId);
    setLoadingAnalysis(true);
    try {
      const data = await apiFetch<AnalysisData>(`/confessions/proof-analysis/${verseId}`, { item_id: String(itemId) });
      setAnalysis(data);
    } catch { setAnalysis(null); }
    setLoadingAnalysis(false);
  };

  const grouped = groupProofs(proofs);

  return (
    <div className="space-y-1">
      {grouped.map(([group, groupProofs]) => (
        <div key={group}>
          {group !== 'a' && grouped.length > 1 && (
            <div className="text-[8px] text-gray-600 mt-2 mb-0.5">Group {group}</div>
          )}
          {groupProofs.map((pt) => {
            const isExpanded = expandedVerse === pt.verse_id;
            return (
              <div key={pt.verse_id ?? pt.osis_ref} className={`rounded-lg transition ${isExpanded ? 'bg-white/5 ring-1 ring-accent-gold/20' : ''}`}>
                {/* Collapsed: reference + verse text */}
                <button
                  onClick={() => toggleVerse(pt.verse_id)}
                  className="w-full text-left p-2 hover:bg-white/3 rounded-lg transition"
                >
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] text-gray-600">{isExpanded ? '▾' : '▸'}</span>
                    <span className="text-[10px] font-medium text-accent-blue">
                      {pt.book_name ? `${pt.book_name} ${pt.chapter_number}:${pt.verse_number}` : pt.osis_ref}
                    </span>
                  </div>
                  {pt.verse_text && !isExpanded && (
                    <p className="text-[9px] text-gray-600 mt-0.5 ml-4 line-clamp-1">{pt.verse_text}</p>
                  )}
                </button>

                {/* Expanded: full analysis */}
                {isExpanded && (
                  <div className="px-2 pb-3 space-y-2.5">
                    {/* Full verse text */}
                    {pt.verse_text && (
                      <p className="text-[10px] text-gray-300 leading-relaxed pl-2 border-l-2 border-accent-gold/30 italic">
                        "{pt.verse_text}"
                      </p>
                    )}

                    {loadingAnalysis && (
                      <div className="flex items-center gap-2 text-[9px] text-gray-500">
                        <div className="w-3 h-3 border border-accent-blue border-t-transparent rounded-full animate-spin" />
                        Analyzing...
                      </div>
                    )}

                    {analysis && analysis.verse_id === pt.verse_id && (
                      <>
                        {/* Semantic similarity */}
                        {analysis.semantic_similarity !== null && (
                          <div>
                            <div className="text-[8px] text-gray-500 uppercase tracking-wider mb-1">Semantic Match</div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-accent-gold rounded-full" style={{ width: `${analysis.semantic_similarity * 100}%` }} />
                              </div>
                              <span className="text-[10px] text-accent-gold font-medium">{(analysis.semantic_similarity * 100).toFixed(0)}%</span>
                            </div>
                            <p className="text-[8px] text-gray-600 mt-0.5">
                              Cosine similarity between verse meaning and doctrine statement
                            </p>
                          </div>
                        )}

                        {/* Key words */}
                        {analysis.words.length > 0 && (
                          <div>
                            <div className="text-[8px] text-gray-500 uppercase tracking-wider mb-1">
                              Key Words ({analysis.words[0]?.language === 'heb' ? 'Hebrew' : 'Greek'})
                            </div>
                            <div className="space-y-1">
                              {analysis.words.filter(w => w.definition).slice(0, 6).map((w) => (
                                <div key={w.position} className="bg-white/3 rounded p-1.5">
                                  <div className="flex items-baseline gap-1.5">
                                    <span className="text-accent-gold text-[11px] font-mono">{w.original}</span>
                                    <span className="text-[9px] text-gray-500">({w.transliteration})</span>
                                    <span className="text-[9px] text-gray-400">"{w.gloss}"</span>
                                  </div>
                                  {w.strongs && <span className="text-[8px] text-gray-600">{w.strongs}</span>}
                                  {w.definition && (
                                    <p className="text-[8px] text-gray-500 mt-0.5 line-clamp-2">{w.definition}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Cross-confession citations */}
                        {analysis.cross_citations.length > 1 && (
                          <div>
                            <div className="text-[8px] text-gray-500 uppercase tracking-wider mb-1">
                              Also Cited By ({analysis.cross_citations.length - 1} others)
                            </div>
                            <div className="space-y-1">
                              {analysis.cross_citations
                                .filter(c => !(c.item_type === 'question' && c.item_number === itemId))
                                .slice(0, 5)
                                .map((c, i) => (
                                <div key={i} className="text-[9px]">
                                  <span className="text-accent-blue font-medium">{c.abbreviation}</span>
                                  <span className="text-gray-500 ml-1">
                                    {c.item_type === 'question' ? `Q.${c.item_number}` : c.title || `§${c.item_number}`}
                                  </span>
                                  {c.context && (
                                    <p className="text-[8px] text-gray-600 mt-0.5 line-clamp-1">{c.context}</p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-1">
                      {pt.verse_id && (
                        <button onClick={() => onJumpToVerse(pt.verse_id!)}
                          className="text-[9px] text-accent-blue hover:text-white bg-accent-blue/10 px-2 py-1 rounded transition">
                          View in Galaxy
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
