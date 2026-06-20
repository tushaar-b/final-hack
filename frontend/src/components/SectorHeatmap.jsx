import React from 'react';

const SECTORS = [
  { name: 'IT', change: 1.2 },
  { name: 'Banking', change: -0.4 },
  { name: 'FMCG', change: 0.8 },
  { name: 'Pharma', change: 2.1 },
  { name: 'Auto', change: -1.3 },
  { name: 'Energy', change: 0.3 },
  { name: 'Metal', change: -2.0 },
  { name: 'Realty', change: 1.5 },
  { name: 'Infra', change: -0.7 },
  { name: 'Media', change: 0.1 },
  { name: 'Telecom', change: 0.9 },
  { name: 'CPSE', change: -0.2 },
  { name: 'MNC', change: 0.6 },
];

function HeatCell({ name, change }) {
  const cls =
    change > 0 ? 'heatmap-cell-positive' :
    change < 0 ? 'heatmap-cell-negative' :
    'heatmap-cell-neutral';

  const intensity = Math.min(Math.abs(change) / 3, 1);
  const alpha = 0.1 + intensity * 0.25;

  return (
    <div
      className={`${cls} rounded-lg p-2.5 text-center transition-all hover:scale-105 cursor-default`}
      style={{
        background: change > 0
          ? `rgba(16, 185, 129, ${alpha})`
          : change < 0
          ? `rgba(244, 63, 94, ${alpha})`
          : `rgba(51, 65, 85, 0.2)`,
      }}
    >
      <p className="text-xs font-medium text-slate-300">{name}</p>
      <p className={`text-sm font-bold font-mono-num ${change > 0 ? 'text-positive' : change < 0 ? 'text-negative' : 'text-neutral'}`}>
        {change >= 0 ? '+' : ''}{change.toFixed(1)}%
      </p>
    </div>
  );
}

export default function SectorHeatmap({ sectors }) {
  const data = sectors || SECTORS;
  return (
    <div>
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Sector Returns (1D)</p>
      <div className="grid grid-cols-3 gap-1.5">
        {data.map((s) => (
          <HeatCell key={s.name} name={s.name} change={s.change} />
        ))}
      </div>
    </div>
  );
}
