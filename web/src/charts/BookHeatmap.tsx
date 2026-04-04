import { useRef, useEffect } from 'react';
import { Html } from '@react-three/drei';
import type { BookMatrixEntry } from '@/types/crossref';

interface BookHeatmapProps {
  matrix: BookMatrixEntry[];
}

export function BookHeatmap({ matrix }: BookHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const size = 66;
    const cellSize = 6;
    const w = size * cellSize;
    canvas.width = w;
    canvas.height = w;

    // Build density grid
    const grid = new Float64Array(size * size);
    let maxCount = 1;
    for (const entry of matrix) {
      const idx = (entry.source - 1) * size + (entry.target - 1);
      grid[idx] = entry.count;
      if (entry.count > maxCount) maxCount = entry.count;
    }

    // Draw
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const val = grid[r * size + c];
        const norm = val > 0 ? Math.log(val + 1) / Math.log(maxCount + 1) : 0;
        const h = 240 - norm * 180; // blue → yellow
        const s = norm > 0 ? 70 : 0;
        const l = norm > 0 ? 20 + norm * 50 : 8;
        ctx.fillStyle = `hsl(${h}, ${s}%, ${l}%)`;
        ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
      }
    }

    // Grid lines for testament boundary (OT/NT at book 40)
    ctx.strokeStyle = 'rgba(255,255,255,0.3)';
    ctx.lineWidth = 1;
    const ntStart = 39 * cellSize;
    ctx.beginPath();
    ctx.moveTo(ntStart, 0);
    ctx.lineTo(ntStart, w);
    ctx.moveTo(0, ntStart);
    ctx.lineTo(w, ntStart);
    ctx.stroke();
  }, [matrix]);

  return (
    <Html center position={[0, 0, 0]} style={{ pointerEvents: 'auto' }}>
      <div className="bg-bg-panel/95 p-4 rounded-lg border border-white/10">
        <h3 className="text-white text-sm font-medium mb-2">
          Cross-Reference Density (66 x 66 books)
        </h3>
        <div className="flex gap-2">
          <div className="text-[9px] text-gray-400 flex flex-col justify-between" style={{ height: 396 }}>
            <span>Gen</span>
            <span>Mal</span>
            <span>Matt</span>
            <span>Rev</span>
          </div>
          <canvas
            ref={canvasRef}
            className="border border-white/5"
            style={{ width: 396, height: 396, imageRendering: 'pixelated' }}
          />
        </div>
        <div className="flex justify-between text-[9px] text-gray-400 mt-1 ml-8">
          <span>Gen</span>
          <span>Mal</span>
          <span>Matt</span>
          <span>Rev</span>
        </div>
      </div>
    </Html>
  );
}
