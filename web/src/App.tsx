import { Canvas } from '@react-three/fiber';
import { useSceneStore } from '@/stores/sceneStore';
import { useUIStore } from '@/stores/uiStore';
import { ScriptureGalaxy } from '@/scenes/ScriptureGalaxy';
import { GraphExplorer } from '@/scenes/GraphExplorer';
import { WordConstellation } from '@/scenes/WordConstellation';
import { CrossRefMatrix } from '@/scenes/CrossRefMatrix';
import { FilterPanel } from '@/panels/FilterPanel';
import { VerseDetailPanel } from '@/panels/VerseDetailPanel';
import { SearchPanel } from '@/panels/SearchPanel';
import { ToolBar } from '@/panels/ToolBar';
import { GalaxyLegend } from '@/panels/LegendPanel';
import type { SceneId } from '@/types/scene';

const SCENES: { id: SceneId; label: string }[] = [
  { id: 'galaxy', label: 'Scripture Galaxy' },
  { id: 'graph', label: 'Knowledge Graph' },
  { id: 'words', label: 'Word Study' },
  { id: 'crossref', label: 'Cross-References' },
];

export default function App() {
  const { activeScene, setActiveScene, selectedNodeId, selectNode } = useSceneStore();
  const { isLoading, loadingMessage, toggleSearchPanel, searchPanelOpen, toggleFilterPanel, filterPanelOpen } = useUIStore();

  return (
    <div className="h-screen w-screen flex flex-col bg-bg-primary text-white overflow-hidden">
      {/* Top bar */}
      <header className="h-10 flex items-center px-3 bg-bg-secondary border-b border-white/5 flex-shrink-0 z-30">
        <div className="flex items-center gap-1 mr-4">
          <span className="text-sm font-semibold tracking-wide text-accent-gold">Hermeneutica</span>
        </div>
        <nav className="flex gap-0.5">
          {SCENES.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setActiveScene(id)}
              className={`text-[11px] px-2.5 py-1 rounded transition ${
                activeScene === id
                  ? 'bg-white/10 text-white'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
        <div className="flex-1" />
        <button
          onClick={toggleFilterPanel}
          className={`text-[11px] px-2 py-1 rounded mr-1 transition ${
            filterPanelOpen ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'
          }`}
        >
          Filters
        </button>
        <button
          onClick={toggleSearchPanel}
          className={`text-[11px] px-2 py-1 rounded transition ${
            searchPanelOpen ? 'bg-accent-blue/20 text-accent-blue' : 'text-gray-500 hover:text-white'
          }`}
        >
          Search
        </button>
      </header>

      {/* Main area — canvas fills everything, panels overlay */}
      <div className="flex-1 relative overflow-hidden">
        {/* Full-bleed 3D Canvas */}
        <Canvas
          className="!absolute inset-0"
          camera={{ position: [0, 0, 80], fov: 60 }}
          gl={{ antialias: true, alpha: false }}
          onCreated={({ gl }) => { gl.setClearColor('#0a0a0f'); }}
        >
          {activeScene === 'galaxy' && <ScriptureGalaxy />}
          {activeScene === 'graph' && <GraphExplorer />}
          {activeScene === 'words' && <WordConstellation />}
          {activeScene === 'crossref' && <CrossRefMatrix />}
        </Canvas>

        {/* === Overlay panels (all absolute, don't affect canvas size) === */}

        {/* Left: Filter panel */}
        <FilterPanel />

        {/* Right: Detail panel (overlay, not flex-push) */}
        {selectedNodeId && (
          <div className="absolute top-0 right-0 bottom-10 w-64 bg-bg-panel/95 backdrop-blur-sm border-l border-white/10 z-20 overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 border-b border-white/5 flex-shrink-0">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider">Detail</span>
              <button onClick={() => selectNode(null, null)} className="text-gray-500 hover:text-white text-xs">✕</button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <VerseDetailPanel />
            </div>
          </div>
        )}

        {/* Bottom-right: Color legend */}
        <GalaxyLegend />

        {/* Bottom: Explore toolbar */}
        <ToolBar />

        {/* Search overlay */}
        <SearchPanel />

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/80 z-40">
            <div className="text-center">
              <div className="w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-gray-400">{loadingMessage}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
