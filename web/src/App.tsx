import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { useSceneStore } from '@/stores/sceneStore';
import { useUIStore } from '@/stores/uiStore';
import { Intro } from '@/scenes/Intro';
import { ScriptureGalaxy } from '@/scenes/ScriptureGalaxy';
import { GraphExplorer } from '@/scenes/GraphExplorer';
import { WordConstellation } from '@/scenes/WordConstellation';
import { CrossRefMatrix } from '@/scenes/CrossRefMatrix';
import { Journal } from '@/scenes/Journal';
import { Research } from '@/scenes/Research';
import { Confessions } from '@/scenes/Confessions';
import { FilterPanel } from '@/panels/FilterPanel';
import { VerseDetailPanel } from '@/panels/VerseDetailPanel';
import { StrongsDetailPanel } from '@/panels/StrongsDetailPanel';
import { SearchPanel } from '@/panels/SearchPanel';
import { ToolBar } from '@/panels/ToolBar';
import { GalaxyLegend } from '@/panels/LegendPanel';
import type { SceneId } from '@/types/scene';

const NAV_SCENES: { id: SceneId; label: string; short: string }[] = [
  { id: 'galaxy', label: 'Scripture Galaxy', short: 'Galaxy' },
  { id: 'graph', label: 'Knowledge Graph', short: 'Graph' },
  { id: 'words', label: 'Word Study', short: 'Words' },
  { id: 'crossref', label: 'Cross-References', short: 'Analytics' },
  { id: 'confessions', label: 'Creeds & Confessions', short: 'Creeds' },
  { id: 'research', label: 'Research', short: 'Research' },
  { id: 'journal', label: 'Journal', short: 'Journal' },
];

const is3DScene = (s: SceneId) => ['galaxy', 'graph', 'words'].includes(s);

export default function App() {
  const { activeScene, setActiveScene, selectedNodeId, selectedNodeType, selectNode } = useSceneStore();
  const { isLoading, loadingMessage, toggleSearchPanel, searchPanelOpen, toggleFilterPanel, filterPanelOpen } = useUIStore();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const show3D = is3DScene(activeScene);

  return (
    <div className="h-screen w-screen flex flex-col bg-bg-primary text-white overflow-hidden">
      {/* Top bar */}
      <header className="h-10 flex items-center px-2 sm:px-3 bg-bg-secondary border-b border-white/5 flex-shrink-0 z-30">
        <button
          onClick={() => setActiveScene('intro')}
          className="flex items-center gap-1 mr-2 sm:mr-4 hover:opacity-80 transition flex-shrink-0"
        >
          <span className="text-sm font-semibold tracking-wide text-accent-gold">Hermeneutica</span>
        </button>

        {/* Desktop nav */}
        <nav className="hidden sm:flex gap-0.5">
          {NAV_SCENES.map(({ id, label }) => (
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

        {/* Mobile nav toggle */}
        <button
          className="sm:hidden text-gray-400 hover:text-white text-xs px-2 py-1 rounded bg-white/5"
          onClick={() => setMobileNavOpen(!mobileNavOpen)}
        >
          {NAV_SCENES.find(s => s.id === activeScene)?.short ?? 'Menu'} ▾
        </button>

        <div className="flex-1" />
        {show3D && (
          <div className="flex gap-1">
            <button
              onClick={toggleFilterPanel}
              className={`text-[11px] px-2 py-1 rounded transition ${
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
          </div>
        )}
      </header>

      {/* Mobile nav dropdown */}
      {mobileNavOpen && (
        <div className="sm:hidden bg-bg-secondary border-b border-white/5 z-30 px-2 py-1 flex flex-wrap gap-1">
          {NAV_SCENES.map(({ id, short }) => (
            <button
              key={id}
              onClick={() => { setActiveScene(id); setMobileNavOpen(false); }}
              className={`text-[11px] px-3 py-1.5 rounded transition ${
                activeScene === id
                  ? 'bg-white/10 text-white'
                  : 'text-gray-500 hover:text-gray-300 bg-white/5'
              }`}
            >
              {short}
            </button>
          ))}
        </div>
      )}

      {/* Main area */}
      <div className="flex-1 relative overflow-hidden">
        {/* Non-3D pages */}
        {activeScene === 'intro' && <Intro />}
        {activeScene === 'crossref' && <CrossRefMatrix />}
        {activeScene === 'confessions' && <Confessions />}
        {activeScene === 'research' && <Research />}
        {activeScene === 'journal' && <Journal />}

        {/* 3D Canvas */}
        {show3D && (
          <>
            <Canvas
              className="!absolute inset-0"
              camera={{ position: [0, 0, 80], fov: 60 }}
              gl={{ antialias: true, alpha: false }}
              onCreated={({ gl }) => { gl.setClearColor('#0a0a0f'); }}
            >
              {activeScene === 'galaxy' && <ScriptureGalaxy />}
              {activeScene === 'graph' && <GraphExplorer />}
              {activeScene === 'words' && <WordConstellation />}
            </Canvas>

            {/* Filter panel — hidden on mobile by default */}
            <FilterPanel />

            {/* Detail panel — full width on mobile, side panel on desktop */}
            {selectedNodeId && (
              <div className="absolute top-0 right-0 bottom-10 w-full sm:w-64 bg-bg-panel/95 backdrop-blur-sm border-l border-white/10 z-20 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between px-3 py-2 border-b border-white/5 flex-shrink-0">
                  <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                    {selectedNodeType === 'strongs' ? 'Word Detail' : selectedNodeType === 'theme' ? 'Theme' : 'Verse Detail'}
                  </span>
                  <button onClick={() => selectNode(null, null)} className="text-gray-500 hover:text-white text-xs px-2 py-1 bg-white/5 rounded">✕ Close</button>
                </div>
                <div className="flex-1 overflow-y-auto">
                  {selectedNodeType === 'strongs' ? <StrongsDetailPanel /> : <VerseDetailPanel />}
                </div>
              </div>
            )}

            <GalaxyLegend />
            <ToolBar />
            <SearchPanel />

            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/80 z-40">
                <div className="text-center">
                  <div className="w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                  <p className="text-sm text-gray-400">{loadingMessage}</p>
                </div>
              </div>
            )}

            <div className="absolute bottom-11 left-2 z-10 text-[9px] text-gray-700 hover:text-gray-500 transition hidden sm:block">
              <a href="https://www.automate-capture.com" target="_blank" rel="noopener noreferrer">
                Made by Automate Capture, LLC
              </a>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
