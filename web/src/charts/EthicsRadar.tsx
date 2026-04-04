import { ETHICS_SUBSETS } from '@/lib/constants';
import { ETHICS_COLORS } from '@/lib/colors';

interface EthicsRadarProps {
  scores: Record<string, number>;
  size?: number;
}

export function EthicsRadar({ scores, size = 160 }: EthicsRadarProps) {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.38;
  const n = ETHICS_SUBSETS.length;

  const angleStep = (2 * Math.PI) / n;
  const startAngle = -Math.PI / 2;

  // Axis endpoints
  const axes = ETHICS_SUBSETS.map((_, i) => {
    const angle = startAngle + i * angleStep;
    return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius };
  });

  // Data polygon
  const points = ETHICS_SUBSETS.map((s, i) => {
    const val = scores[s] ?? 0;
    const angle = startAngle + i * angleStep;
    const r = val * radius;
    return `${cx + Math.cos(angle) * r},${cy + Math.sin(angle) * r}`;
  }).join(' ');

  return (
    <svg width={size} height={size} className="mx-auto">
      {/* Grid rings */}
      {[0.25, 0.5, 0.75, 1.0].map((r) => (
        <circle
          key={r}
          cx={cx} cy={cy} r={radius * r}
          fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={0.5}
        />
      ))}
      {/* Axes */}
      {axes.map((a, i) => (
        <line key={i} x1={cx} y1={cy} x2={a.x} y2={a.y} stroke="rgba(255,255,255,0.15)" strokeWidth={0.5} />
      ))}
      {/* Data polygon */}
      <polygon points={points} fill="rgba(74,144,217,0.25)" stroke="#4A90D9" strokeWidth={1.5} />
      {/* Data points */}
      {ETHICS_SUBSETS.map((s, i) => {
        const val = scores[s] ?? 0;
        const angle = startAngle + i * angleStep;
        const px = cx + Math.cos(angle) * val * radius;
        const py = cy + Math.sin(angle) * val * radius;
        return <circle key={s} cx={px} cy={py} r={3} fill={ETHICS_COLORS[s]} />;
      })}
      {/* Labels */}
      {ETHICS_SUBSETS.map((s, i) => {
        const angle = startAngle + i * angleStep;
        const lx = cx + Math.cos(angle) * (radius + 14);
        const ly = cy + Math.sin(angle) * (radius + 14);
        return (
          <text key={s} x={lx} y={ly} textAnchor="middle" dominantBaseline="middle"
            className="fill-gray-400 text-[8px]">
            {s.slice(0, 5)}
          </text>
        );
      })}
    </svg>
  );
}
