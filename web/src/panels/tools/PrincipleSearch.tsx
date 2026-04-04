import { useState, useEffect, useRef } from 'react';
import { apiFetch } from '@/api/client';
import { ETHICS_COLORS } from '@/lib/colors';

interface PrincipleResult {
  principle_id: number;
  principle_text: string;
  book_name: string;
  chapter_number: number;
  genre: string;
  themes: string[];
  teaching_type: string;
  similarity: number;
  ethics_scores: Record<string, number>;
}

const TEACHING_ICONS: Record<string, string> = {
  explicit_command: 'Direct command',
  implicit_principle: 'Implicit principle',
  exemplar_narrative: 'By example',
  metaphorical_wisdom: 'Metaphor/wisdom',
};

export function PrincipleSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<PrincipleResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (query.length < 3) { setResults([]); return; }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await apiFetch<PrincipleResult[]>('/explore/principles', { q: query, limit: '20' });
        setResults(data);
      } catch { setResults([]); }
      setLoading(false);
    }, 400);
  }, [query]);

  return (
    <div className="p-3">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="What does the Bible teach about... forgiveness, anger, generosity..."
        className="w-full bg-bg-secondary text-white text-sm rounded px-3 py-2 border border-white/10 focus:border-accent-blue outline-none mb-3"
      />

      {loading && <div className="text-xs text-gray-500">Searching principles...</div>}

      {results.length > 0 && (
        <div className="space-y-2 max-h-44 overflow-y-auto">
          {results.map((p) => (
            <div
              key={p.principle_id}
              className="bg-bg-secondary/50 rounded-lg p-2.5 cursor-pointer hover:bg-white/5 transition"
              onClick={() => setExpanded(expanded === p.principle_id ? null : p.principle_id)}
            >
              {/* Principle text */}
              <p className="text-xs text-gray-200 leading-relaxed">{p.principle_text}</p>

              {/* Source */}
              <div className="flex items-center gap-2 mt-1.5 text-[10px]">
                <span className="text-accent-blue">{p.book_name} {p.chapter_number}</span>
                <span className="text-gray-600">|</span>
                <span className="text-gray-500">{p.genre}</span>
                <span className="text-gray-600">|</span>
                <span className="text-gray-500">{TEACHING_ICONS[p.teaching_type] || p.teaching_type}</span>
                {p.similarity > 0 && (
                  <>
                    <span className="text-gray-600">|</span>
                    <span className="text-gray-500">match: {(p.similarity * 100).toFixed(0)}%</span>
                  </>
                )}
              </div>

              {/* Themes */}
              {p.themes && p.themes.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {p.themes.map((t) => (
                    <span key={t} className="text-[9px] bg-accent-green/15 text-accent-green px-1.5 py-0.5 rounded">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {/* Expanded: ethics scores */}
              {expanded === p.principle_id && p.ethics_scores && (
                <div className="mt-2 pt-2 border-t border-white/5">
                  <div className="text-[10px] text-gray-500 mb-1">Ethics Relevance</div>
                  <div className="flex gap-3">
                    {Object.entries(p.ethics_scores).map(([subset, score]) => (
                      <div key={subset} className="text-center">
                        <div className="w-8 bg-bg-primary rounded-full overflow-hidden h-1.5 mb-0.5">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${score * 100}%`,
                              backgroundColor: ETHICS_COLORS[subset] || '#666',
                            }}
                          />
                        </div>
                        <div className="text-[8px] text-gray-600">{subset.slice(0, 4)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {query.length >= 3 && !loading && results.length === 0 && (
        <div className="text-xs text-gray-600">No principles found. Try broader terms like "love", "justice", "obedience".</div>
      )}
    </div>
  );
}
