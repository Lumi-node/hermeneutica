import { useState } from 'react';

interface FruitsSeries {
  condition: string;
  scores: Record<string, number>;
}

interface FruitsRadarProps {
  fruits: string[];
  labels: Record<string, string>;
  alignmentProblems: Record<string, string>;
  series: FruitsSeries[];
  maxScore: number;
  size?: number;
}

const CONDITION_COLORS: Record<string, { fill: string; stroke: string; label: string }> = {
  A_vanilla:  { fill: 'rgba(148,163,184,0.15)', stroke: '#94A3B8', label: 'Vanilla Baseline' },
  E_lora:     { fill: 'rgba(74,144,217,0.15)',  stroke: '#4A90D9', label: 'LoRA (latest)' },
};

// Fallback palette for unknown conditions
const FALLBACK_COLORS = [
  { fill: 'rgba(232,168,56,0.15)',  stroke: '#E8A838' },
  { fill: 'rgba(80,200,120,0.15)',  stroke: '#50C878' },
  { fill: 'rgba(123,104,238,0.15)', stroke: '#7B68EE' },
  { fill: 'rgba(255,107,107,0.15)', stroke: '#FF6B6B' },
];

export function FruitsRadar({ fruits, labels, alignmentProblems, series, maxScore, size = 380 }: FruitsRadarProps) {
  const [hoveredFruit, setHoveredFruit] = useState<string | null>(null);

  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.34;
  const n = fruits.length;
  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2;

  const getColor = (condition: string, idx: number) =>
    CONDITION_COLORS[condition] ?? { ...FALLBACK_COLORS[idx % FALLBACK_COLORS.length], label: condition };

  const polarToCart = (angle: number, r: number) => ({
    x: cx + Math.cos(angle) * r,
    y: cy + Math.sin(angle) * r,
  });

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="mx-auto">
        {/* Grid rings */}
        {[1, 2, 3, 4, 5].map((level) => (
          <circle
            key={level}
            cx={cx} cy={cy} r={(level / maxScore) * radius}
            fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={0.5}
          />
        ))}

        {/* Grid ring labels */}
        {[1, 2, 3, 4, 5].map((level) => (
          <text
            key={level}
            x={cx + 4} y={cy - (level / maxScore) * radius + 2}
            className="fill-gray-600 text-[9px]"
          >
            {level}
          </text>
        ))}

        {/* Axes */}
        {fruits.map((_, i) => {
          const angle = startAngle + i * angleStep;
          const end = polarToCart(angle, radius);
          return (
            <line
              key={i}
              x1={cx} y1={cy} x2={end.x} y2={end.y}
              stroke="rgba(255,255,255,0.12)" strokeWidth={0.5}
            />
          );
        })}

        {/* Data polygons */}
        {series.map((s, si) => {
          const color = getColor(s.condition, si);
          const points = fruits.map((fruit, i) => {
            const val = s.scores[fruit] ?? 0;
            const angle = startAngle + i * angleStep;
            const r = (val / maxScore) * radius;
            const p = polarToCart(angle, r);
            return `${p.x},${p.y}`;
          }).join(' ');

          return (
            <polygon
              key={s.condition}
              points={points}
              fill={color.fill}
              stroke={color.stroke}
              strokeWidth={1.5}
              opacity={0.9}
            />
          );
        })}

        {/* Data points */}
        {series.map((s, si) => {
          const color = getColor(s.condition, si);
          return fruits.map((fruit, i) => {
            const val = s.scores[fruit] ?? 0;
            const angle = startAngle + i * angleStep;
            const r = (val / maxScore) * radius;
            const p = polarToCart(angle, r);
            return (
              <circle
                key={`${s.condition}-${fruit}`}
                cx={p.x} cy={p.y} r={3}
                fill={color.stroke}
                className="cursor-pointer"
              />
            );
          });
        })}

        {/* Axis labels */}
        {fruits.map((fruit, i) => {
          const angle = startAngle + i * angleStep;
          const labelR = radius + 28;
          const p = polarToCart(angle, labelR);
          const isHovered = hoveredFruit === fruit;

          return (
            <g
              key={fruit}
              onMouseEnter={() => setHoveredFruit(fruit)}
              onMouseLeave={() => setHoveredFruit(null)}
              className="cursor-pointer"
            >
              <text
                x={p.x} y={p.y - 6}
                textAnchor="middle" dominantBaseline="middle"
                className={`text-[10px] font-medium transition-colors ${
                  isHovered ? 'fill-white' : 'fill-gray-300'
                }`}
              >
                {labels[fruit] ?? fruit}
              </text>
              <text
                x={p.x} y={p.y + 6}
                textAnchor="middle" dominantBaseline="middle"
                className={`text-[8px] transition-colors ${
                  isHovered ? 'fill-gray-300' : 'fill-gray-600'
                }`}
              >
                {alignmentProblems[fruit] ?? ''}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex gap-6 mt-2">
        {series.map((s, si) => {
          const color = getColor(s.condition, si);
          const avg = Object.values(s.scores).reduce((a, b) => a + b, 0) / fruits.length;
          return (
            <div key={s.condition} className="flex items-center gap-2 text-xs">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color.stroke }} />
              <span className="text-gray-300">{color.label}</span>
              <span className="text-gray-500">({avg.toFixed(2)})</span>
            </div>
          );
        })}
      </div>

      {/* Hover detail */}
      {hoveredFruit && (
        <div className="mt-3 text-center">
          <div className="text-sm text-white font-medium">
            {labels[hoveredFruit]} — {alignmentProblems[hoveredFruit]}
          </div>
          <div className="flex gap-4 justify-center mt-1">
            {series.map((s, si) => {
              const color = getColor(s.condition, si);
              const val = s.scores[hoveredFruit] ?? 0;
              return (
                <span key={s.condition} className="text-xs" style={{ color: color.stroke }}>
                  {color.label}: {val.toFixed(2)}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
