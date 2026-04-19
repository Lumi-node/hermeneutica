import { useFilterStore } from '@/stores/filterStore';
import { useSceneStore } from '@/stores/sceneStore';
import { useUIStore } from '@/stores/uiStore';
import { BOOKS, GENRES, EDGE_TYPES } from '@/lib/constants';
import { CrossRefOverlayControls } from './CrossRefOverlay';

export function FilterPanel() {
  const { filterPanelOpen, toggleFilterPanel } = useUIStore();
  const { activeScene, colorBy, sizeBy, setColorBy, setSizeBy, setOverlay, clearOverlay } = useSceneStore();
  const {
    testamentFilter, setTestamentFilter,
    bookFilter, toggleBook, clearBookFilter,
    genreFilter, toggleGenre,
    edgeTypeFilter, toggleEdgeType,
    minWeight, setMinWeight,
    graphHops, setGraphHops,
  } = useFilterStore();

  if (!filterPanelOpen) return null;

  const isGalaxy = activeScene === 'galaxy';
  const isGraph = activeScene === 'graph';
  const isWords = activeScene === 'words';
  const isCrossRef = activeScene === 'crossref';

  return (
    <>
      {/* Mobile backdrop */}
      <div
        onClick={toggleFilterPanel}
        className="sm:hidden absolute inset-0 bg-black/50 z-20"
        aria-hidden="true"
      />
      <div className="absolute left-0 right-0 bottom-11 top-auto max-h-[70vh] rounded-t-xl border-t border-white/10 sm:top-0 sm:right-auto sm:bottom-10 sm:w-44 sm:max-h-none sm:rounded-none sm:border-t-0 sm:border-r bg-bg-panel/95 backdrop-blur-sm overflow-y-auto z-30 sm:z-20">
        {/* Mobile header with grab handle + close */}
        <div className="sm:hidden sticky top-0 bg-bg-panel/95 backdrop-blur-sm border-b border-white/5 z-10">
          <div className="flex justify-center pt-2 pb-1">
            <div className="h-1 w-10 rounded-full bg-white/20" />
          </div>
          <div className="flex items-center justify-between px-3 pb-2">
            <span className="text-xs text-gray-400 uppercase tracking-wider">Filters</span>
            <button
              onClick={toggleFilterPanel}
              className="text-gray-400 hover:text-white text-sm px-3 py-1.5 rounded bg-white/5 min-h-[36px]"
            >
              Done
            </button>
          </div>
        </div>
        <div className="p-3 space-y-4">
        {/* Scene label */}
        <div className="text-xs text-gray-600 uppercase tracking-widest font-medium border-b border-white/5 pb-2">
          {activeScene === 'galaxy' ? 'Galaxy' : activeScene === 'graph' ? 'Graph' : activeScene === 'words' ? 'Words' : 'Cross-Refs'} filters
        </div>

        {/* === GALAXY: Color/Size + Testament + Genre + Books === */}
        {isGalaxy && (
          <>
            <Section title="Encoding">
              <label className="text-xs text-gray-400 block mb-1">Color by</label>
              <select
                value={colorBy}
                onChange={(e) => setColorBy(e.target.value as typeof colorBy)}
                className="w-full bg-bg-secondary text-white text-xs rounded px-2 py-1 border border-white/10"
              >
                <option value="book">Book</option>
                <option value="testament">Testament</option>
                <option value="genre">Genre</option>
                <option value="ethics">Ethics Score</option>
              </select>
              <label className="text-xs text-gray-400 block mb-1 mt-2">Size by</label>
              <select
                value={sizeBy}
                onChange={(e) => setSizeBy(e.target.value as typeof sizeBy)}
                className="w-full bg-bg-secondary text-white text-xs rounded px-2 py-1 border border-white/10"
              >
                <option value="uniform">Uniform</option>
                <option value="crossrefs">Cross-Ref Count</option>
                <option value="ethics">Ethics Score</option>
              </select>
            </Section>

            <Section title="Testament">
              <TestamentToggle value={testamentFilter} onChange={setTestamentFilter} />
            </Section>

            <Section title="Genre">
              {GENRES.map((g) => (
                <Checkbox key={g} label={g} checked={genreFilter.includes(g)} onChange={() => toggleGenre(g)} />
              ))}
            </Section>

            <BookFilter bookFilter={bookFilter} toggleBook={toggleBook} clearBookFilter={clearBookFilter} />

            <CrossRefOverlayControls onArcsLoaded={setOverlay} onClear={clearOverlay} />
          </>
        )}

        {/* === GRAPH: Edge types, hops, weight === */}
        {isGraph && (
          <>
            <Section title="Edge Types">
              {EDGE_TYPES.map((et) => (
                <Checkbox
                  key={et}
                  label={et.replace(/_/g, ' ')}
                  checked={edgeTypeFilter.length === 0 || edgeTypeFilter.includes(et)}
                  onChange={() => toggleEdgeType(et)}
                />
              ))}
            </Section>

            <Section title="Graph Depth">
              <div className="flex gap-1">
                {[1, 2, 3].map((h) => (
                  <button
                    key={h}
                    onClick={() => setGraphHops(h)}
                    className={`text-xs px-3 py-1 rounded transition ${
                      graphHops === h ? 'bg-accent-purple text-white' : 'bg-bg-secondary text-gray-400 hover:text-white'
                    }`}
                  >
                    {h} hop{h > 1 ? 's' : ''}
                  </button>
                ))}
              </div>
            </Section>

            <Section title="Min Weight">
              <input
                type="range" min={0} max={1} step={0.05}
                value={minWeight}
                onChange={(e) => setMinWeight(parseFloat(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-gray-500">{minWeight.toFixed(2)}</span>
            </Section>

            <div className="text-[10px] text-gray-600 mt-2">
              Click a node to re-center the graph on it
            </div>
          </>
        )}

        {/* === WORDS: Testament (Hebrew=OT, Greek=NT) === */}
        {isWords && (
          <>
            <Section title="Language">
              <TestamentToggle value={testamentFilter} onChange={setTestamentFilter} />
              <div className="text-[10px] text-gray-600 mt-2">
                OT = Hebrew, NT = Greek
              </div>
            </Section>

            <div className="text-[10px] text-gray-600">
              Size = usage frequency across all verses
            </div>
          </>
        )}

        {/* === CROSS-REFS: minimal, heatmap is self-explanatory === */}
        {isCrossRef && (
          <div className="text-xs text-gray-500">
            66 x 66 book cross-reference density matrix. Brighter = more connections.
            <div className="mt-2 text-[10px] text-gray-600">
              OT→NT boundary shown as white lines.
            </div>
          </div>
        )}
        </div>
      </div>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2 font-medium">{title}</h4>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function TestamentToggle({ value, onChange }: { value: string; onChange: (v: 'all' | 'OT' | 'NT') => void }) {
  return (
    <div className="flex gap-1">
      {(['all', 'OT', 'NT'] as const).map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={`text-sm sm:text-xs px-4 sm:px-3 py-2 sm:py-1 rounded transition min-h-[40px] sm:min-h-0 ${
            value === t ? 'bg-accent-blue text-white' : 'bg-bg-secondary text-gray-300 sm:text-gray-400 hover:text-white'
          }`}
        >
          {t === 'all' ? 'All' : t}
        </button>
      ))}
    </div>
  );
}

function Checkbox({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label className="flex items-center gap-2 text-sm sm:text-xs text-gray-200 sm:text-gray-300 cursor-pointer hover:text-white py-1.5 sm:py-0 min-h-[36px] sm:min-h-0">
      <input type="checkbox" checked={checked} onChange={onChange} className="rounded border-gray-600 w-4 h-4 sm:w-3 sm:h-3" />
      {label}
    </label>
  );
}

function BookFilter({ bookFilter, toggleBook, clearBookFilter }: {
  bookFilter: number[]; toggleBook: (id: number) => void; clearBookFilter: () => void;
}) {
  return (
    <Section title={`Books${bookFilter.length > 0 ? ` (${bookFilter.length})` : ''}`}>
      {bookFilter.length > 0 && (
        <button onClick={clearBookFilter} className="text-xs sm:text-[10px] text-accent-red hover:text-white mb-1 py-1.5 sm:py-0">Clear</button>
      )}
      <div className="max-h-48 sm:max-h-40 overflow-y-auto grid grid-cols-2 sm:grid-cols-1 gap-x-2 gap-y-0.5">
        {BOOKS.map((b) => (
          <label key={b.id} className="flex items-center gap-2 sm:gap-1.5 text-xs sm:text-[10px] text-gray-300 sm:text-gray-400 cursor-pointer hover:text-white py-1 sm:py-0 min-h-[32px] sm:min-h-0">
            <input type="checkbox" checked={bookFilter.includes(b.id)} onChange={() => toggleBook(b.id)} className="rounded border-gray-600 w-4 h-4 sm:w-3 sm:h-3" />
            {b.abbreviation}
          </label>
        ))}
      </div>
    </Section>
  );
}
