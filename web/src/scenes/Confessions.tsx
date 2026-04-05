import { useState, useEffect } from 'react';
import { apiFetch } from '@/api/client';

interface ConfessionSummary {
  id: number;
  name: string;
  abbreviation: string;
  confession_type: string;
  tradition: string;
  year: number;
  authors: string | null;
  item_count: number;
  proof_text_count: number;
}

interface ProofText {
  proof_group: string;
  osis_ref: string;
  verse_id: number | null;
  verse_text: string | null;
  book_name: string | null;
  chapter_number: number | null;
  verse_number: number | null;
}

interface ConfessionItem {
  id: number;
  item_number: number;
  item_type: string;
  title: string | null;
  question_text: string | null;
  answer_text: string | null;
  answer_with_proofs: string | null;
  sort_order: number;
  proof_texts: ProofText[];
  children: ConfessionItem[];
}

interface ConfessionDetail {
  id: number;
  name: string;
  abbreviation: string;
  confession_type: string;
  tradition: string;
  year: number;
  authors: string | null;
  items: ConfessionItem[];
}

const TYPE_LABELS: Record<string, string> = {
  confession: 'Confession',
  catechism: 'Catechism',
  canon: 'Canon',
};

const TRADITION_COLORS: Record<string, string> = {
  reformed: 'text-accent-green',
  presbyterian: 'text-accent-blue',
};

export function Confessions() {
  const [confessions, setConfessions] = useState<ConfessionSummary[]>([]);
  const [selected, setSelected] = useState<ConfessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Load confession list
  useEffect(() => {
    apiFetch<ConfessionSummary[]>('/confessions/')
      .then(setConfessions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Load a specific confession
  const loadConfession = async (id: number) => {
    setLoading(true);
    try {
      const data = await apiFetch<ConfessionDetail>(`/confessions/${id}`);
      setSelected(data);
      setExpandedItems(new Set());
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

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

  const toggleExpand = (id: number) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const expandAll = () => {
    if (!selected) return;
    const all = new Set<number>();
    const collect = (items: ConfessionItem[]) => {
      for (const item of items) { all.add(item.id); collect(item.children); }
    };
    collect(selected.items);
    setExpandedItems(all);
  };

  return (
    <div className="h-full overflow-y-auto bg-bg-primary">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10">

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-white mb-1">Creeds & Confessions</h1>
          <p className="text-xs sm:text-sm text-gray-500">
            6 historic Reformed confessions and catechisms with 10,094 proof-text links to Scripture
          </p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search across all confessions... (e.g., justification, election, sacraments)"
            className="w-full bg-white/5 text-white text-sm rounded-lg px-4 py-2.5 border border-white/10 focus:border-accent-blue outline-none"
          />
          {searchResults.length > 0 && (
            <div className="mt-2 bg-bg-panel rounded-lg border border-white/10 max-h-60 overflow-y-auto">
              {searchResults.map((r: any) => (
                <button
                  key={r.id}
                  onClick={() => { loadConfession(r.confession_id); setSearchQuery(''); setSearchResults([]); }}
                  className="w-full text-left px-4 py-2 hover:bg-white/5 transition border-b border-white/5 last:border-0"
                >
                  <div className="flex items-baseline gap-2">
                    <span className="text-[10px] text-accent-blue font-medium">{r.abbreviation}</span>
                    <span className="text-[10px] text-gray-600">
                      {r.item_type === 'question' ? `Q. ${r.item_number}` : r.title || `${r.item_type} ${r.item_number}`}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 truncate mt-0.5">
                    {r.answer_preview || r.question_preview || r.title}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Confession list or detail */}
        {!selected ? (
          <div className="grid sm:grid-cols-2 gap-3">
            {confessions.map(c => (
              <button
                key={c.id}
                onClick={() => loadConfession(c.id)}
                className="text-left bg-white/3 hover:bg-white/5 border border-white/5 hover:border-white/10 rounded-lg p-4 transition"
              >
                <div className="flex items-baseline gap-2 mb-1">
                  <h3 className="text-sm font-medium text-white">{c.name}</h3>
                  <span className="text-[10px] text-gray-600">{c.year}</span>
                </div>
                <div className="flex gap-2 mb-2">
                  <span className="text-[9px] bg-white/5 text-gray-400 px-1.5 py-0.5 rounded">
                    {TYPE_LABELS[c.confession_type] || c.confession_type}
                  </span>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded bg-white/5 ${TRADITION_COLORS[c.tradition] || 'text-gray-400'}`}>
                    {c.tradition}
                  </span>
                </div>
                <div className="text-[10px] text-gray-600">
                  {c.item_count} items · {c.proof_text_count.toLocaleString()} proof texts
                </div>
                {c.authors && <div className="text-[10px] text-gray-600 mt-1">{c.authors}</div>}
              </button>
            ))}
          </div>
        ) : (
          <div>
            {/* Back + title */}
            <div className="flex items-center gap-3 mb-4">
              <button onClick={() => setSelected(null)} className="text-xs text-gray-500 hover:text-white transition">
                ← All Confessions
              </button>
              <div className="flex-1" />
              <button onClick={expandAll} className="text-[10px] text-gray-500 hover:text-white transition">
                Expand all
              </button>
              <button onClick={() => setExpandedItems(new Set())} className="text-[10px] text-gray-500 hover:text-white transition">
                Collapse all
              </button>
            </div>

            <div className="mb-6">
              <h2 className="text-lg font-semibold text-white">{selected.name}</h2>
              <div className="flex gap-2 mt-1 text-[10px]">
                <span className="text-gray-500">{selected.year}</span>
                <span className={`${TRADITION_COLORS[selected.tradition] || 'text-gray-400'}`}>{selected.tradition}</span>
                <span className="text-gray-600">{TYPE_LABELS[selected.confession_type] || selected.confession_type}</span>
                {selected.authors && <span className="text-gray-600">{selected.authors}</span>}
              </div>
            </div>

            {/* Items */}
            <div className="space-y-1">
              {selected.items.map(item => (
                <ItemView
                  key={item.id}
                  item={item}
                  expanded={expandedItems}
                  onToggle={toggleExpand}
                  depth={0}
                  confessionType={selected.confession_type}
                />
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="text-center py-8">
            <div className="w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        )}
      </div>
    </div>
  );
}

function ItemView({ item, expanded, onToggle, depth, confessionType }: {
  item: ConfessionItem;
  expanded: Set<number>;
  onToggle: (id: number) => void;
  depth: number;
  confessionType: string;
}) {
  const isExpanded = expanded.has(item.id);
  const hasChildren = item.children.length > 0;
  const hasProofs = item.proof_texts.length > 0;
  const isChapter = item.item_type === 'chapter';
  const isQuestion = item.item_type === 'question';

  return (
    <div className={depth > 0 ? 'ml-3 sm:ml-5' : ''}>
      <button
        onClick={() => onToggle(item.id)}
        className={`w-full text-left rounded-lg transition ${
          isChapter
            ? 'bg-white/3 hover:bg-white/5 p-3 mb-1'
            : 'hover:bg-white/3 p-2 sm:p-3'
        }`}
      >
        {/* Header */}
        <div className="flex items-start gap-2">
          {(hasChildren || hasProofs || item.answer_text) && (
            <span className="text-[10px] text-gray-600 mt-0.5 flex-shrink-0">
              {isExpanded ? '▾' : '▸'}
            </span>
          )}

          <div className="flex-1 min-w-0">
            {isChapter && (
              <div className="text-sm font-medium text-white">
                {confessionType === 'catechism' ? '' : `Chapter ${item.item_number}: `}
                {item.title}
              </div>
            )}

            {isQuestion && (
              <div>
                <div className="text-xs text-accent-gold font-medium mb-1">
                  Q. {item.item_number}: {item.question_text}
                </div>
                {!isExpanded && item.answer_text && (
                  <p className="text-[11px] text-gray-500 truncate">{item.answer_text}</p>
                )}
              </div>
            )}

            {item.item_type === 'section' && (
              <div>
                <span className="text-[10px] text-gray-600 mr-2">{item.item_number}.</span>
                {!isExpanded && item.answer_text && (
                  <span className="text-[11px] text-gray-500">{item.answer_text?.slice(0, 120)}...</span>
                )}
              </div>
            )}
          </div>

          {hasProofs && (
            <span className="text-[9px] text-gray-600 flex-shrink-0 bg-white/5 px-1.5 py-0.5 rounded">
              {item.proof_texts.length} refs
            </span>
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className={`${isChapter ? 'ml-4' : 'ml-5'} mb-2`}>
          {/* Full answer text */}
          {item.answer_text && (
            <p className="text-xs text-gray-300 leading-relaxed mb-2 pl-1 border-l-2 border-accent-gold/20">
              {item.answer_text}
            </p>
          )}

          {/* Proof texts grouped */}
          {hasProofs && (
            <ProofTextsView proofs={item.proof_texts} />
          )}

          {/* Children (sections under chapters) */}
          {hasChildren && (
            <div className="space-y-0.5 mt-1">
              {item.children.map(child => (
                <ItemView
                  key={child.id}
                  item={child}
                  expanded={expanded}
                  onToggle={onToggle}
                  depth={depth + 1}
                  confessionType={confessionType}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ProofTextsView({ proofs }: { proofs: ProofText[] }) {
  const [showVerses, setShowVerses] = useState(false);

  // Group by proof_group
  const groups = new Map<string, ProofText[]>();
  for (const p of proofs) {
    const list = groups.get(p.proof_group) || [];
    list.push(p);
    groups.set(p.proof_group, list);
  }

  return (
    <div className="mb-2">
      <button
        onClick={() => setShowVerses(!showVerses)}
        className="text-[10px] text-accent-blue hover:text-white transition mb-1"
      >
        {showVerses ? 'Hide' : 'Show'} {proofs.length} proof texts
      </button>

      {showVerses && (
        <div className="space-y-2 mt-1">
          {[...groups.entries()].map(([group, texts]) => (
            <div key={group} className="pl-2 border-l border-white/5">
              {group !== 'a' && <div className="text-[9px] text-gray-600 mb-0.5">Group {group}</div>}
              <div className="space-y-1">
                {texts.map((pt, i) => (
                  <div key={i} className="text-[10px]">
                    <span className="text-accent-blue font-medium">
                      {pt.book_name ? `${pt.book_name} ${pt.chapter_number}:${pt.verse_number}` : pt.osis_ref}
                    </span>
                    {pt.verse_text && (
                      <span className="text-gray-500 ml-1.5">{pt.verse_text}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
