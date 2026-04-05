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
    apiFetch<ConfessionSummary[]>('/confessions/')
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

      {/* Left: Confession nav */}
      <div className="sm:w-40 flex-shrink-0 bg-bg-panel/80 border-r border-white/5 overflow-y-auto">
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

      {/* Right: Data panel */}
      <div className="sm:w-72 flex-shrink-0 bg-bg-panel/80 border-l border-white/5 overflow-y-auto hidden sm:block">
        <div className="p-3">
          {selectedItem ? (
            <div className="space-y-3">
              {/* Item info */}
              <div>
                <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-1">Selected</div>
                <div className="text-xs text-white font-medium">
                  {selectedItem.item_type === 'question' ? `Q. ${selectedItem.item_number}` :
                   selectedItem.title || `§ ${selectedItem.item_number}`}
                </div>
              </div>

              {/* Proof texts */}
              {selectedItem.proof_texts.length > 0 && (
                <div>
                  <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-2">
                    Proof Texts ({selectedItem.proof_texts.length})
                  </div>
                  <div className="space-y-2">
                    {groupProofs(selectedItem.proof_texts).map(([group, proofs]) => (
                      <div key={group}>
                        {group !== 'a' && <div className="text-[8px] text-gray-600 mb-0.5">Group {group}</div>}
                        {proofs.map((pt, i) => (
                          <div key={i} className="mb-2">
                            <button
                              onClick={() => pt.verse_id && jumpToVerse(pt.verse_id)}
                              className={`text-[10px] font-medium mb-0.5 block ${pt.verse_id ? 'text-accent-blue hover:text-white cursor-pointer' : 'text-gray-400'}`}>
                              {pt.book_name ? `${pt.book_name} ${pt.chapter_number}:${pt.verse_number}` : pt.osis_ref}
                            </button>
                            {pt.verse_text && (
                              <p className="text-[10px] text-gray-500 leading-relaxed pl-2 border-l border-accent-gold/20">
                                {pt.verse_text}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Cross-confession references (future) */}
              <div className="border-t border-white/5 pt-2">
                <div className="text-[9px] text-gray-600">
                  Click a verse reference to jump to its location in the Scripture Galaxy
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-gray-600 py-4">
              <p className="mb-2">Click a section or question in the document to see its proof texts here.</p>
              <p>Proof texts link each doctrinal statement to the specific Bible verses that support it.</p>
            </div>
          )}
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/80 z-40">
          <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
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
  const isChapter = item.item_type === 'chapter';
  const isQuestion = item.item_type === 'question';
  const isSelected = selectedItemId === item.id;
  const hasProofs = item.proof_texts.length > 0;

  return (
    <div className={depth > 0 ? 'ml-4' : 'mb-4'}>
      <div
        onClick={() => onSelectItem(item)}
        className={`cursor-pointer rounded-lg transition p-3 ${
          isSelected ? 'bg-accent-blue/10 ring-1 ring-accent-blue/20' : 'hover:bg-white/3'
        } ${isChapter ? 'mb-2' : 'mb-1'}`}
      >
        {isChapter && (
          <h3 className="text-sm font-semibold text-white mb-1">
            {confessionType !== 'catechism' && `Chapter ${item.item_number}: `}
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

        {item.item_type === 'section' && (
          <div>
            <span className="text-[10px] text-gray-500 font-medium mr-1">§{item.item_number}.</span>
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
  // For now, return raw text — future: parse [a], [b] markers and make them interactive
  return text;
}
