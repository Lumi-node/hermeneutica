import { useState } from 'react';
import { ThemeTracer } from './tools/ThemeTracer';
import { ShortestPath } from './tools/ShortestPath';
import { PrincipleSearch } from './tools/PrincipleSearch';

const TOOLS = [
  { id: 'theme-tracer', label: 'Theme Tracer', icon: '🔍', description: 'Trace a theme from Genesis to Revelation' },
  { id: 'shortest-path', label: 'Shortest Path', icon: '⛓', description: 'Find the connection between any two verses' },
  { id: 'principles', label: 'Principle Search', icon: '📖', description: 'Search distilled moral principles' },
] as const;

type ToolId = typeof TOOLS[number]['id'];

export function ToolBar() {
  const [activeTool, setActiveTool] = useState<ToolId | null>(null);
  const [expanded, setExpanded] = useState(false);

  const contentHeight = expanded ? 'max-h-[70vh]' : 'max-h-[45vh]';

  return (
    <div className="absolute bottom-0 left-0 right-0 z-30 flex flex-col">
      {/* Tool content area */}
      {activeTool && (
        <div className={`bg-bg-panel/95 backdrop-blur-sm border-t border-white/10 ${contentHeight} flex flex-col`}>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 flex-shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-sm">{TOOLS.find(t => t.id === activeTool)?.icon}</span>
              <span className="text-xs text-white font-medium">{TOOLS.find(t => t.id === activeTool)?.label}</span>
              <span className="text-[10px] text-gray-500 hidden sm:inline">{TOOLS.find(t => t.id === activeTool)?.description}</span>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setExpanded(!expanded)}
                className="text-gray-500 hover:text-white text-xs px-2 py-0.5 rounded hover:bg-white/5"
                title={expanded ? 'Shrink' : 'Expand'}
              >
                {expanded ? '▼' : '▲'}
              </button>
              <button
                onClick={() => setActiveTool(null)}
                className="text-gray-500 hover:text-white text-xs px-2 py-0.5 rounded hover:bg-white/5"
              >
                ✕
              </button>
            </div>
          </div>
          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTool === 'theme-tracer' && <ThemeTracer />}
            {activeTool === 'shortest-path' && <ShortestPath />}
            {activeTool === 'principles' && <PrincipleSearch />}
          </div>
        </div>
      )}

      {/* Tool tab bar */}
      <div className="bg-bg-secondary border-t border-white/5 flex items-center px-2 h-9 flex-shrink-0">
        <span className="text-[10px] text-gray-600 mr-3 uppercase tracking-wider">Explore</span>
        {TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => {
              if (activeTool === tool.id) {
                setActiveTool(null);
              } else {
                setActiveTool(tool.id);
              }
            }}
            className={`text-xs px-3 py-1.5 rounded mr-1 transition ${
              activeTool === tool.id
                ? 'bg-accent-blue/20 text-accent-blue'
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
            }`}
          >
            <span className="mr-1">{tool.icon}</span>
            {tool.label}
          </button>
        ))}
      </div>
    </div>
  );
}
