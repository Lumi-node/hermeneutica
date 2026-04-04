import { useState, useEffect, useRef } from 'react';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { apiFetch } from '@/api/client';

type Tab = 'crossrefs' | 'topics' | 'ethics' | 'words';

const TABS: { id: Tab; label: string; desc: string }[] = [
  { id: 'crossrefs', label: 'Cross-References', desc: '66x66 books — how densely each book references every other' },
  { id: 'topics', label: 'Topic Distribution', desc: '66 books x top themes — which books discuss which themes most' },
  { id: 'ethics', label: 'Ethics Landscape', desc: '66 books x 5 ethical dimensions — moral reasoning by book' },
  { id: 'words', label: 'Word Frequency', desc: '66 books x top Hebrew/Greek words — key concepts by book' },
];

export function CrossRefMatrix() {
  const [activeTab, setActiveTab] = useState<Tab>('crossrefs');

  return (
    <div className="h-full overflow-auto bg-bg-primary">
      {/* Tab bar */}
      <div className="sticky top-0 bg-bg-secondary/95 backdrop-blur-sm border-b border-white/5 z-10 px-6 pt-4 pb-0">
        <h1 className="text-lg font-semibold text-white mb-3">Biblical Analytics</h1>
        <div className="flex gap-1">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`text-xs px-3 py-2 rounded-t transition border-b-2 ${
                activeTab === tab.id
                  ? 'bg-bg-panel text-white border-accent-blue'
                  : 'text-gray-500 hover:text-gray-300 border-transparent'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <p className="text-xs text-gray-500 mb-4">{TABS.find(t => t.id === activeTab)?.desc}</p>
        {activeTab === 'crossrefs' && <CrossRefHeatmap />}
        {activeTab === 'topics' && <TopicHeatmap />}
        {activeTab === 'ethics' && <EthicsHeatmap />}
        {activeTab === 'words' && <WordHeatmap />}
      </div>
    </div>
  );
}

// ============================================================
// 1. Cross-Reference Density (existing)
// ============================================================
function CrossRefHeatmap() {
  const { bookMatrix, loadBookMatrix } = useDataStore();
  const { setLoading } = useUIStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!bookMatrix) {
      setLoading(true, 'Loading cross-reference matrix...');
      loadBookMatrix().catch(console.error).finally(() => setLoading(false));
    }
  }, [bookMatrix, loadBookMatrix, setLoading]);

  useEffect(() => {
    if (!bookMatrix || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const size = 66, cellSize = 8, w = size * cellSize;
    canvas.width = w; canvas.height = w;

    const grid = new Float64Array(size * size);
    let maxCount = 1;
    for (const entry of bookMatrix) {
      const idx = (entry.source - 1) * size + (entry.target - 1);
      grid[idx] = entry.count;
      if (entry.count > maxCount) maxCount = entry.count;
    }

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const val = grid[r * size + c];
        const norm = val > 0 ? Math.log(val + 1) / Math.log(maxCount + 1) : 0;
        ctx.fillStyle = `hsl(${240 - norm * 200}, ${norm > 0 ? 75 : 0}%, ${norm > 0 ? 15 + norm * 55 : 6}%)`;
        ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
      }
    }
    // OT/NT boundary
    ctx.strokeStyle = 'rgba(255,255,255,0.25)'; ctx.lineWidth = 1.5;
    const nt = 39 * cellSize;
    ctx.beginPath(); ctx.moveTo(nt, 0); ctx.lineTo(nt, w); ctx.moveTo(0, nt); ctx.lineTo(w, nt); ctx.stroke();
  }, [bookMatrix]);

  return (
    <HeatmapFrame canvasRef={canvasRef} size={528}
      yLabels={['Gen', 'Josh', 'Job', 'Isa', 'Mal', 'Matt', 'Acts', 'Rom', 'Rev']}
      xLabels={['Gen', 'Josh', 'Job', 'Isa', 'Mal', 'Matt', 'Acts', 'Rom', 'Rev']}
      footer="432,944 total cross-references across 66 books"
    />
  );
}

// ============================================================
// 2. Topic Distribution
// ============================================================
interface TopicData {
  books: { id: number; name: string; abbreviation: string; book_order: number; testament: string }[];
  topics: string[];
  matrix: number[][];
  max_value: number;
}

function TopicHeatmap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [data, setData] = useState<TopicData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiFetch<TopicData>('/explore/heatmap/topics', { top_n: '25' })
      .then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rows = data.books.length, cols = data.topics.length;
    const cellW = 20, cellH = 8;
    canvas.width = cols * cellW; canvas.height = rows * cellH;

    const maxVal = data.max_value || 1;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = data.matrix[r]?.[c] || 0;
        const norm = val > 0 ? Math.log(val + 1) / Math.log(maxVal + 1) : 0;
        ctx.fillStyle = `hsl(${30 + norm * 60}, ${norm > 0 ? 80 : 0}%, ${norm > 0 ? 10 + norm * 55 : 5}%)`;
        ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
      }
    }
    // OT/NT line
    ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.lineWidth = 1;
    const ntY = 39 * cellH;
    ctx.beginPath(); ctx.moveTo(0, ntY); ctx.lineTo(canvas.width, ntY); ctx.stroke();
  }, [data]);

  if (loading) return <div className="text-xs text-gray-500">Loading topic distribution...</div>;
  if (!data) return null;

  return (
    <div className="flex gap-2">
      {/* Book labels (Y axis) */}
      <div className="flex flex-col text-[7px] text-gray-500 pt-0.5" style={{ height: data.books.length * 8 }}>
        {data.books.map((b, i) => (
          <div key={b.id} style={{ height: 8, lineHeight: '8px' }} className={`${i === 39 ? 'border-t border-white/20' : ''} ${b.testament === 'OT' ? 'text-amber-500/60' : 'text-blue-400/60'}`}>
            {i % 3 === 0 ? b.abbreviation : ''}
          </div>
        ))}
      </div>

      <div>
        {/* Topic labels (X axis, rotated) */}
        <div className="flex mb-1" style={{ height: 80 }}>
          {data.topics.map((t, i) => (
            <div key={i} style={{ width: 20, height: 80 }} className="relative">
              <span className="absolute bottom-0 left-1/2 -translate-x-1/2 origin-bottom-left -rotate-45 text-[7px] text-gray-500 whitespace-nowrap">
                {t.length > 12 ? t.slice(0, 12) + '..' : t}
              </span>
            </div>
          ))}
        </div>

        <canvas
          ref={canvasRef}
          className="border border-white/5 rounded"
          style={{ width: data.topics.length * 20, height: data.books.length * 8, imageRendering: 'pixelated' }}
        />

        <div className="text-[9px] text-gray-600 mt-2">
          {data.topics.length} most common Nave's topics across {data.books.length} books. Warm = more verses.
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 3. Ethics Landscape
// ============================================================
interface EthicsData {
  books: { id: number; name: string; abbreviation: string; book_order: number; testament: string }[];
  ethics_subsets: string[];
  matrix: number[][];
  classified_chapters: number;
}

const ETHICS_HUE: Record<string, number> = {
  commonsense: 200, deontology: 35, justice: 130, virtue: 280, utilitarianism: 15,
};

function EthicsHeatmap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [data, setData] = useState<EthicsData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiFetch<EthicsData>('/explore/heatmap/ethics')
      .then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rows = data.books.length, cols = data.ethics_subsets.length;
    const cellW = 60, cellH = 8;
    canvas.width = cols * cellW; canvas.height = rows * cellH;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = data.matrix[r]?.[c] || 0;
        const subset = data.ethics_subsets[c];
        const hue = ETHICS_HUE[subset] ?? 200;
        ctx.fillStyle = val > 0
          ? `hsl(${hue}, ${60 + val * 30}%, ${10 + val * 50}%)`
          : `hsl(0, 0%, 5%)`;
        ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
      }
    }
    // OT/NT line
    ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, 39 * cellH); ctx.lineTo(canvas.width, 39 * cellH); ctx.stroke();
  }, [data]);

  if (loading) return <div className="text-xs text-gray-500">Loading ethics landscape...</div>;
  if (!data) return null;

  return (
    <div className="flex gap-2">
      <div className="flex flex-col text-[7px] text-gray-500 pt-6" style={{ height: data.books.length * 8 }}>
        {data.books.map((b, i) => (
          <div key={b.id} style={{ height: 8, lineHeight: '8px' }} className={b.testament === 'OT' ? 'text-amber-500/60' : 'text-blue-400/60'}>
            {i % 3 === 0 ? b.abbreviation : ''}
          </div>
        ))}
      </div>

      <div>
        {/* Column headers */}
        <div className="flex mb-1">
          {data.ethics_subsets.map(s => (
            <div key={s} style={{ width: 60 }} className="text-center text-[9px] text-gray-400 capitalize">
              {s.slice(0, 7)}
            </div>
          ))}
        </div>

        <canvas
          ref={canvasRef}
          className="border border-white/5 rounded"
          style={{ width: data.ethics_subsets.length * 60, height: data.books.length * 8, imageRendering: 'pixelated' }}
        />

        <div className="text-[9px] text-gray-600 mt-2">
          Average ethics relevance score per book. {data.classified_chapters} chapters classified.
          Black = no data for that book. Each column uses its own color hue.
        </div>

        {/* Legend */}
        <div className="flex gap-3 mt-2">
          {data.ethics_subsets.map(s => (
            <div key={s} className="flex items-center gap-1">
              <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: `hsl(${ETHICS_HUE[s] ?? 200}, 70%, 45%)` }} />
              <span className="text-[8px] text-gray-500 capitalize">{s}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 4. Word Frequency
// ============================================================
interface WordData {
  books: { id: number; name: string; abbreviation: string; book_order: number; testament: string }[];
  words: { strongs_number: string; transliteration: string; language: string; short_def: string }[];
  matrix: number[][];
  max_value: number;
}

function WordHeatmap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [data, setData] = useState<WordData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiFetch<WordData>('/explore/heatmap/words', { top_n: '30' })
      .then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!data || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rows = data.books.length, cols = data.words.length;
    const cellW = 18, cellH = 8;
    canvas.width = cols * cellW; canvas.height = rows * cellH;

    const maxVal = data.max_value || 1;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = data.matrix[r]?.[c] || 0;
        const norm = val > 0 ? Math.log(val + 1) / Math.log(maxVal + 1) : 0;
        const isHeb = data.words[c]?.language === 'heb';
        const hue = isHeb ? 35 : 210; // gold for Hebrew, blue for Greek
        ctx.fillStyle = norm > 0
          ? `hsl(${hue}, ${60 + norm * 30}%, ${8 + norm * 55}%)`
          : `hsl(0, 0%, 4%)`;
        ctx.fillRect(c * cellW, r * cellH, cellW, cellH);
      }
    }
    // OT/NT line
    ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, 39 * cellH); ctx.lineTo(canvas.width, 39 * cellH); ctx.stroke();
  }, [data]);

  if (loading) return <div className="text-xs text-gray-500">Loading word frequency...</div>;
  if (!data) return null;

  return (
    <div className="flex gap-2">
      <div className="flex flex-col text-[7px] text-gray-500 pt-16" style={{ height: data.books.length * 8 }}>
        {data.books.map((b, i) => (
          <div key={b.id} style={{ height: 8, lineHeight: '8px' }} className={b.testament === 'OT' ? 'text-amber-500/60' : 'text-blue-400/60'}>
            {i % 3 === 0 ? b.abbreviation : ''}
          </div>
        ))}
      </div>

      <div>
        {/* Word labels (rotated) */}
        <div className="flex mb-1" style={{ height: 60 }}>
          {data.words.map((w, i) => (
            <div key={i} style={{ width: 18, height: 60 }} className="relative">
              <span className={`absolute bottom-0 left-1/2 -translate-x-1/2 origin-bottom-left -rotate-55 text-[6px] whitespace-nowrap ${
                w.language === 'heb' ? 'text-amber-500/70' : 'text-blue-400/70'
              }`}>
                {w.transliteration}
              </span>
            </div>
          ))}
        </div>

        <canvas
          ref={canvasRef}
          className="border border-white/5 rounded"
          style={{ width: data.words.length * 18, height: data.books.length * 8, imageRendering: 'pixelated' }}
        />

        <div className="text-[9px] text-gray-600 mt-2">
          Top {data.words.length} most-used Strong's words. Gold = Hebrew (OT), Blue = Greek (NT).
        </div>
      </div>
    </div>
  );
}

// ============================================================
// Shared heatmap frame
// ============================================================
function HeatmapFrame({ canvasRef, size, yLabels, xLabels, footer }: {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  size: number;
  yLabels: string[];
  xLabels: string[];
  footer: string;
}) {
  return (
    <div>
      <div className="flex gap-1">
        <div className="flex flex-col justify-between text-[8px] text-gray-500 py-0.5" style={{ height: size }}>
          {yLabels.map(l => <span key={l}>{l}</span>)}
        </div>
        <canvas
          ref={canvasRef}
          className="border border-white/5 rounded"
          style={{ width: size, height: size, imageRendering: 'pixelated' }}
        />
      </div>
      <div className="flex justify-between text-[8px] text-gray-500 mt-1 ml-8" style={{ width: size }}>
        {xLabels.map(l => <span key={l}>{l}</span>)}
      </div>
      <div className="text-[9px] text-gray-600 mt-3">{footer}</div>
    </div>
  );
}
