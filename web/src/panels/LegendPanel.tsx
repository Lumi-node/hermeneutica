import { useState, useRef, useCallback } from 'react';
import { useSceneStore } from '@/stores/sceneStore';
import { bookColor, testamentColor, GENRE_COLORS } from '@/lib/colors';
import { BOOKS } from '@/lib/constants';

function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (v: number) => Math.round(v * 255).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

export function GalaxyLegend() {
  const { colorBy, activeScene } = useSceneStore();
  // Default closed on mobile, open on desktop
  const [open, setOpen] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth >= 640 : true,
  );
  const [pos, setPos] = useState({ x: 0, y: 0 }); // offset from default position
  const dragRef = useRef<{ startX: number; startY: number; origX: number; origY: number } | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragRef.current = { startX: e.clientX, startY: e.clientY, origX: pos.x, origY: pos.y };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [pos]);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragRef.current) return;
    setPos({
      x: dragRef.current.origX + (e.clientX - dragRef.current.startX),
      y: dragRef.current.origY + (e.clientY - dragRef.current.startY),
    });
  }, []);

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  if (activeScene !== 'galaxy') return null;

  return (
    <div
      ref={panelRef}
      className="absolute z-20"
      style={{ top: 8 + pos.y, right: 8 - pos.x }}
    >
      {/* Drag handle + collapse toggle */}
      <div
        className="flex items-center gap-1 bg-bg-panel/80 backdrop-blur-sm border border-white/10 rounded px-2 py-1 cursor-grab active:cursor-grabbing select-none"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        <span className="text-[10px] text-gray-500">⠿</span>
        <span className="text-[10px] text-gray-400 flex-1">Legend</span>
        <button
          onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
          className="text-[10px] text-gray-500 hover:text-white px-1"
        >
          {open ? '▴' : '▾'}
        </button>
      </div>

      {open && (
        <div className="mt-0.5 bg-bg-panel/90 backdrop-blur-sm border border-white/10 rounded-lg p-2.5 max-h-[55vh] overflow-y-auto w-36">
          <div className="text-[9px] text-gray-500 uppercase tracking-wider mb-1.5">
            Color: {colorBy}
          </div>
          {colorBy === 'book' && <BookLegend />}
          {colorBy === 'testament' && <TestamentLegend />}
          {colorBy === 'genre' && <GenreLegend />}
          {colorBy === 'ethics' && <EthicsGradientLegend />}
        </div>
      )}
    </div>
  );
}

function BookLegend() {
  const otBooks = BOOKS.filter(b => b.testament === 'OT');
  const ntBooks = BOOKS.filter(b => b.testament === 'NT');

  return (
    <div className="space-y-2">
      <div>
        <div className="text-[8px] text-amber-400/70 uppercase tracking-wider mb-0.5">Old Testament</div>
        <div className="grid grid-cols-2 gap-x-1 gap-y-px">
          {otBooks.map(b => <BookSwatch key={b.id} book={b} />)}
        </div>
      </div>
      <div>
        <div className="text-[8px] text-blue-400/70 uppercase tracking-wider mb-0.5">New Testament</div>
        <div className="grid grid-cols-2 gap-x-1 gap-y-px">
          {ntBooks.map(b => <BookSwatch key={b.id} book={b} />)}
        </div>
      </div>
    </div>
  );
}

function BookSwatch({ book }: { book: typeof BOOKS[number] }) {
  const [r, g, b] = bookColor(book.id);
  return (
    <div className="flex items-center gap-1">
      <div className="w-2 h-2 rounded-sm flex-shrink-0" style={{ backgroundColor: rgbToHex(r, g, b) }} />
      <span className="text-[8px] text-gray-400 truncate leading-tight">{book.abbreviation}</span>
    </div>
  );
}

function TestamentLegend() {
  const ot = testamentColor('OT');
  const nt = testamentColor('NT');
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: rgbToHex(...ot) }} />
        <span className="text-[10px] text-gray-300">Old Testament</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: rgbToHex(...nt) }} />
        <span className="text-[10px] text-gray-300">New Testament</span>
      </div>
    </div>
  );
}

function GenreLegend() {
  const genres = [
    { name: 'Law', desc: 'Gen–Deut' },
    { name: 'History', desc: 'Josh–Esth' },
    { name: 'Wisdom', desc: 'Job–Song' },
    { name: 'Prophecy', desc: 'Isa–Mal' },
    { name: 'Gospel', desc: 'Matt–John' },
    { name: 'Epistle', desc: 'Rom–Jude' },
    { name: 'Apocalyptic', desc: 'Rev' },
  ];
  return (
    <div className="space-y-1">
      {genres.map(g => {
        const rgb = GENRE_COLORS[g.name] ?? [0.5, 0.5, 0.5];
        return (
          <div key={g.name} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: rgbToHex(...rgb) }} />
            <span className="text-[9px] text-gray-300">{g.name}</span>
            <span className="text-[8px] text-gray-600 ml-auto">{g.desc}</span>
          </div>
        );
      })}
    </div>
  );
}

function EthicsGradientLegend() {
  return (
    <div className="space-y-1.5">
      <div className="text-[9px] text-gray-400">Max ethics score (5 dims)</div>
      <div className="h-2.5 rounded" style={{
        background: 'linear-gradient(to right, #334499, #5577aa, #88aacc, #bbcc88, #ddaa66)',
      }} />
      <div className="flex justify-between text-[8px] text-gray-500">
        <span>Low</span>
        <span>High</span>
      </div>
    </div>
  );
}
