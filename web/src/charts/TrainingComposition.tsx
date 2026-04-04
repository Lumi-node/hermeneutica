interface CategoryData {
  count: number;
  pct: number;
}

interface CompositionData {
  version: string;
  total: number;
  categories: Record<string, CategoryData>;
}

interface TrainingCompositionProps {
  data: CompositionData[];
}

const CATEGORY_COLORS: Record<string, string> = {
  behavioral:     '#50C878',
  classification: '#4A90D9',
  analysis:       '#E8A838',
  concept:        '#7B68EE',
};

const CATEGORY_LABELS: Record<string, string> = {
  behavioral:     'Behavioral (Fruits)',
  classification: 'Binary Classification',
  analysis:       'Verse Analysis',
  concept:        'Concept / Word Studies',
};

function PieChart({ composition, size = 140 }: { composition: CompositionData; size?: number }) {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.4;
  const categories = Object.entries(composition.categories).filter(([, v]) => v.count > 0);

  let startAngle = -Math.PI / 2;
  const slices = categories.map(([key, val]) => {
    const sweep = (val.pct / 100) * 2 * Math.PI;
    const endAngle = startAngle + sweep;
    const largeArc = sweep > Math.PI ? 1 : 0;

    const x1 = cx + Math.cos(startAngle) * radius;
    const y1 = cy + Math.sin(startAngle) * radius;
    const x2 = cx + Math.cos(endAngle) * radius;
    const y2 = cy + Math.sin(endAngle) * radius;

    const d = `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;

    const result = { key, d, color: CATEGORY_COLORS[key] ?? '#666' };
    startAngle = endAngle;
    return result;
  });

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size}>
        {slices.map((s) => (
          <path key={s.key} d={s.d} fill={s.color} stroke="#0a0a0f" strokeWidth={1.5} />
        ))}
        <text x={cx} y={cy - 6} textAnchor="middle" className="fill-white text-sm font-semibold">
          {composition.version}
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" className="fill-gray-500 text-[10px]">
          {composition.total.toLocaleString()}
        </text>
      </svg>
    </div>
  );
}

export function TrainingComposition({ data }: TrainingCompositionProps) {
  return (
    <div>
      <div className="flex gap-8 justify-center">
        {data.map((d) => (
          <PieChart key={d.version} composition={d} />
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 justify-center mt-4 flex-wrap">
        {Object.entries(CATEGORY_COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-1.5 text-xs">
            <div className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-gray-400">{CATEGORY_LABELS[key] ?? key}</span>
          </div>
        ))}
      </div>

      {/* Detail table */}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-500 border-b border-white/5">
              <th className="text-left py-1.5 font-medium">Category</th>
              {data.map((d) => (
                <th key={d.version} className="text-right py-1.5 font-medium px-3">{d.version}</th>
              ))}
              {data.length === 2 && <th className="text-right py-1.5 font-medium px-3">Change</th>}
            </tr>
          </thead>
          <tbody>
            {Object.keys(CATEGORY_COLORS).map((cat) => (
              <tr key={cat} className="border-b border-white/5">
                <td className="py-1.5 text-gray-300">{CATEGORY_LABELS[cat]}</td>
                {data.map((d) => {
                  const val = d.categories[cat];
                  return (
                    <td key={d.version} className="text-right py-1.5 px-3 text-gray-400">
                      {val ? `${val.count} (${val.pct}%)` : '—'}
                    </td>
                  );
                })}
                {data.length === 2 && (() => {
                  const a = data[0].categories[cat]?.pct ?? 0;
                  const b = data[1].categories[cat]?.pct ?? 0;
                  const delta = b - a;
                  return (
                    <td className={`text-right py-1.5 px-3 ${delta > 0 ? 'text-green-400' : delta < 0 ? 'text-red-400' : 'text-gray-600'}`}>
                      {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
                    </td>
                  );
                })()}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
