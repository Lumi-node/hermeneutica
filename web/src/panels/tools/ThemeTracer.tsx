import { useState, useEffect, useRef, useCallback } from 'react';
import { apiFetch } from '@/api/client';

interface ThemeVerse {
  verse_id: number;
  book_name: string;
  abbreviation: string;
  book_order: number;
  testament: string;
  genre: string;
  chapter_number: number;
  verse_number: number;
  text_preview: string;
}

interface ThemeTrace {
  topic: string;
  verse_count: number;
  verses: ThemeVerse[];
  books_covered: number;
  ot_count: number;
  nt_count: number;
}

export function ThemeTracer() {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [trace, setTrace] = useState<ThemeTrace | null>(null);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedVerse, setSelectedVerse] = useState<ThemeVerse | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (query.length < 2) { setSuggestions([]); return; }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await apiFetch<string[]>('/explore/theme-search', { q: query, limit: '8' });
        setSuggestions(data);
        setShowSuggestions(true);
      } catch { setSuggestions([]); }
    }, 200);
  }, [query]);

  const doTrace = useCallback(async (topic: string) => {
    setQuery(topic);
    setShowSuggestions(false);
    setSelectedVerse(null);
    setLoading(true);
    try {
      const data = await apiFetch<ThemeTrace>('/explore/theme-trace', { topic, limit: '500' });
      setTrace(data);
    } catch { setTrace(null); }
    setLoading(false);
  }, []);

  const bookGroups = trace ? groupByBook(trace.verses) : [];
  const maxBookCount = Math.max(1, ...bookGroups.map(g => g.count));

  return (
    <div className="p-4 h-full flex flex-col">
      {/* Search row */}
      <div className="flex gap-3 items-start mb-4 flex-shrink-0">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && query && doTrace(query)}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            placeholder="Type a theme: Love, Justice, Faith, Covenant, Mercy..."
            className="w-full bg-bg-secondary text-white text-sm rounded-lg px-4 py-2.5 border border-white/10 focus:border-accent-blue outline-none"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 bg-bg-panel border border-white/10 rounded-lg mt-1 z-50 shadow-xl">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => doTrace(s)}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white first:rounded-t-lg last:rounded-b-lg"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
        {/* Quick picks */}
        <div className="flex gap-1 flex-wrap">
          {['Love', 'Faith', 'Justice', 'Mercy', 'Covenant', 'Prayer'].map(t => (
            <button
              key={t}
              onClick={() => doTrace(t)}
              className="text-[11px] px-2.5 py-1.5 rounded-md bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition"
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <div className="w-4 h-4 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
          Tracing theme through scripture...
        </div>
      )}

      {trace && (
        <div className="flex-1 flex flex-col min-h-0">
          {/* Summary stats */}
          <div className="flex items-center gap-4 mb-3 flex-shrink-0">
            <h3 className="text-white font-semibold">{trace.topic}</h3>
            <div className="flex gap-3 text-xs text-gray-500">
              <span>{trace.verse_count} verses</span>
              <span>{trace.books_covered} books</span>
              <span className="text-amber-400/70">OT: {trace.ot_count}</span>
              <span className="text-blue-400/70">NT: {trace.nt_count}</span>
            </div>
          </div>

          {/* Timeline: Genesis → Revelation bar chart */}
          <div className="flex-shrink-0 mb-3">
            <div className="flex items-end gap-px h-16">
              {bookGroups.map((group) => {
                const height = Math.max(4, (group.count / maxBookCount) * 100);
                const isOT = group.testament === 'OT';
                return (
                  <div
                    key={group.bookName}
                    className="flex-1 min-w-[3px] relative group cursor-pointer"
                    onClick={() => {
                      const first = trace.verses.find(v => v.book_name === group.bookName);
                      if (first) setSelectedVerse(first);
                    }}
                  >
                    <div
                      className={`w-full rounded-t transition-all ${
                        isOT ? 'bg-amber-500/60 hover:bg-amber-400' : 'bg-blue-500/60 hover:bg-blue-400'
                      }`}
                      style={{ height: `${height}%` }}
                    />
                    {/* Tooltip */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                      <div className="bg-bg-panel border border-white/10 rounded px-2 py-1 text-[10px] text-white whitespace-nowrap shadow-lg">
                        <strong>{group.bookName}</strong>: {group.count} verse{group.count > 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            {/* Book labels at key points */}
            <div className="flex justify-between text-[9px] text-gray-600 mt-1 px-0.5">
              <span>Gen</span>
              <span className="text-amber-500/50">— OT —</span>
              <span>Mal</span>
              <span className="text-blue-500/50">— NT —</span>
              <span>Rev</span>
            </div>
          </div>

          {/* Verse list */}
          <div className="flex-1 overflow-y-auto min-h-0 space-y-1">
            {trace.verses.map((v) => (
              <div
                key={v.verse_id}
                onClick={() => setSelectedVerse(selectedVerse?.verse_id === v.verse_id ? null : v)}
                className={`flex gap-3 px-3 py-2 rounded-lg cursor-pointer transition ${
                  selectedVerse?.verse_id === v.verse_id
                    ? 'bg-white/10 ring-1 ring-accent-blue/30'
                    : 'hover:bg-white/5'
                }`}
              >
                {/* Reference badge */}
                <div className={`flex-shrink-0 w-20 text-right text-xs font-medium pt-0.5 ${
                  v.testament === 'OT' ? 'text-amber-400/80' : 'text-blue-400/80'
                }`}>
                  {v.abbreviation} {v.chapter_number}:{v.verse_number}
                </div>

                {/* Text */}
                <div className="flex-1 min-w-0">
                  <p className={`text-xs leading-relaxed ${
                    selectedVerse?.verse_id === v.verse_id ? 'text-gray-200' : 'text-gray-400'
                  }`}>
                    {v.text_preview}
                  </p>
                  {selectedVerse?.verse_id === v.verse_id && (
                    <div className="flex gap-2 mt-1.5 text-[10px] text-gray-600">
                      <span className="bg-white/5 px-1.5 py-0.5 rounded">{v.genre}</span>
                      <span className="bg-white/5 px-1.5 py-0.5 rounded">{v.book_name}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!trace && !loading && (
        <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
          Search a biblical theme to trace its path from Genesis to Revelation
        </div>
      )}
    </div>
  );
}

function groupByBook(verses: ThemeVerse[]) {
  const groups: { bookName: string; abbreviation: string; testament: string; count: number; bookOrder: number }[] = [];
  const map = new Map<string, typeof groups[number]>();
  for (const v of verses) {
    const existing = map.get(v.book_name);
    if (existing) {
      existing.count++;
    } else {
      const g = { bookName: v.book_name, abbreviation: v.abbreviation, testament: v.testament, count: 1, bookOrder: v.book_order };
      map.set(v.book_name, g);
      groups.push(g);
    }
  }
  return groups.sort((a, b) => a.bookOrder - b.bookOrder);
}
