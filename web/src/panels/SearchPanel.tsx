import { useState, useCallback, useRef, useEffect } from 'react';
import { apiFetch } from '@/api/client';
import { useSceneStore } from '@/stores/sceneStore';
import { useUIStore } from '@/stores/uiStore';

interface SearchResult {
  verse_id: number;
  book_name: string;
  chapter_number: number;
  verse_number: number;
  text: string;
  similarity: number;
  x: number;
  y: number;
  z: number;
}

export function SearchPanel() {
  const { searchPanelOpen, toggleSearchPanel } = useUIStore();
  const { selectNode, setCameraTarget } = useSceneStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 3) { setResults([]); return; }
    setLoading(true);
    try {
      const data = await apiFetch<SearchResult[]>('/search/verses', { q, limit: '20' });
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(query), 300);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, doSearch]);

  if (!searchPanelOpen) return null;

  const selectAndClose = (r: SearchResult) => {
    selectNode('verse', r.verse_id);
    if (r.x !== undefined) setCameraTarget([r.x, r.y, r.z]);
    // Close on mobile so the user sees the detail panel; keep open on desktop
    if (typeof window !== 'undefined' && window.innerWidth < 640) {
      toggleSearchPanel();
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      <div
        onClick={toggleSearchPanel}
        className="sm:hidden absolute inset-0 bg-black/50 z-40"
        aria-hidden="true"
      />
      <div className="absolute left-2 right-2 top-2 sm:left-auto sm:top-12 sm:right-4 sm:w-80 bg-bg-panel/95 backdrop-blur-sm border border-white/10 rounded-lg shadow-xl z-50 max-h-[80vh] flex flex-col">
        <div className="p-3 flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Semantic search..."
            className="flex-1 bg-bg-secondary text-white text-sm rounded px-3 py-2 border border-white/10 focus:border-accent-blue outline-none min-h-[40px]"
            autoFocus
          />
          <button
            onClick={toggleSearchPanel}
            className="sm:hidden text-gray-400 hover:text-white text-sm px-3 py-2 rounded bg-white/5 min-h-[40px]"
            aria-label="Close search"
          >
            ✕
          </button>
        </div>
        {loading && <div className="px-3 pb-2 text-xs text-gray-500">Searching...</div>}
        {results.length > 0 && (
          <div className="flex-1 overflow-y-auto border-t border-white/5">
            {results.map((r) => (
              <button
                key={r.verse_id}
                onClick={() => selectAndClose(r)}
                className="w-full text-left px-3 py-2.5 sm:py-2 hover:bg-white/5 transition min-h-[44px] sm:min-h-0"
              >
                <div className="flex justify-between items-baseline">
                  <span className="text-xs text-accent-blue font-medium">
                    {r.book_name} {r.chapter_number}:{r.verse_number}
                  </span>
                  <span className="text-[10px] text-gray-600">
                    {(r.similarity * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-gray-400 truncate mt-0.5">{r.text}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
