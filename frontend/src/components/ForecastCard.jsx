import React from 'react';
import { TrendingUp, TrendingDown, Clock, ShieldAlert, Target, Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function ConvictionBar({ score }) {
  const pct = (score / 10) * 100;
  const color =
    score >= 8 ? '#10b981' :
    score >= 6 ? '#3b82f6' :
    score >= 4 ? '#fbbf24' : '#64748b';
  return (
    <div className="conviction-bar">
      <div
        className="conviction-bar-fill"
        style={{ width: `${pct}%`, background: color }}
      />
    </div>
  );
}

function MiniSparkline({ data, color }) {
  if (!data || data.length < 2) return null;
  const vals = data.map(Number).filter(v => !isNaN(v));
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const w = 80, h = 32;
  const pts = vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  });
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="opacity-70">
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function ForecastCard({ forecast, index = 0 }) {
  const navigate = useNavigate();
  const f = forecast;
  const stance = f.signal_stance || 'HOLD';

  const stanceColor = stance === 'BUY' ? 'emerald' : stance === 'SELL' ? 'rose' : 'slate';
  const cardClass = stance === 'BUY' ? 'buy-card' : stance === 'SELL' ? 'sell-card' : '';

  const medianReturn = f.p50_day5;
  const returnPct = medianReturn != null ? (medianReturn * 100).toFixed(2) : null;
  const bandLow = f.p10_day5 != null ? (f.p10_day5 * 100).toFixed(1) : null;
  const bandHigh = f.p90_day5 != null ? (f.p90_day5 * 100).toFixed(1) : null;

  const positionPct = f.position_pct != null ? f.position_pct : (f.conviction_score >= 8 ? 4 : f.conviction_score >= 6 ? 2 : 0);

  return (
    <div
      className={`flat-card animate-fade-in-up animate-delay-${Math.min(index + 1, 6)}`}
      onClick={() => navigate(`/stock/${f.symbol}`)}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-display text-[18px] text-[var(--text-primary)]">{f.symbol}</h3>
          <p className="font-label mt-1">{f.universe?.sector || '—'} · {f.forecast_date}</p>
        </div>
        <div className="flex flex-col items-end space-y-1">
          <span className="font-label" style={{
            color: stance === 'BUY' ? 'var(--color-buy)' : stance === 'SELL' ? 'var(--color-sell)' : 'var(--text-secondary)'
          }}>
            {stance}
          </span>
        </div>
      </div>

      {/* Conviction */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1.5">
          <span className="font-label">Conviction</span>
          <span className="font-data text-sm text-[var(--text-primary)]">{f.conviction_score}/10</span>
        </div>
        <ConvictionBar score={f.conviction_score} />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <span className="font-label block mb-1">Entry Price</span>
          <span className="font-data text-lg text-[var(--text-primary)]">₹{f.closing_price}</span>
        </div>
        <div>
          <span className="font-label block mb-1">Position</span>
          <span className="font-data text-lg text-[var(--text-primary)]">{positionPct > 0 ? `${positionPct}%` : '—'}</span>
        </div>
      </div>

      {/* Return forecast band */}
      {returnPct && (
        <div className="mb-4">
          <span className="font-label block mb-1.5">5-Day Return Forecast</span>
          <div className="flex items-baseline space-x-2">
            <span className={`font-data text-xl ${parseFloat(returnPct) >= 0 ? 'text-[var(--color-positive)]' : 'text-[var(--color-negative)]'}`}>
              {parseFloat(returnPct) >= 0 ? '+' : ''}{returnPct}%
            </span>
            {bandLow && bandHigh && (
              <span className="font-data text-xs text-[var(--text-secondary)]">
                [{parseFloat(bandLow) >= 0 ? '+' : ''}{bandLow}% to {parseFloat(bandHigh) >= 0 ? '+' : ''}{bandHigh}%]
              </span>
            )}
          </div>
        </div>
      )}

      {/* TP / SL */}
      {(stance === 'BUY' || stance === 'SELL') && f.target_price && f.stop_loss && (
        <div className="flex justify-between mb-4">
          <div className="flex items-center space-x-1">
            <span className="font-label">Target:</span>
            <span className="font-data text-sm text-[var(--text-primary)]">₹{f.target_price}</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="font-label">Stop:</span>
            <span className="font-data text-sm text-[var(--text-primary)]">₹{f.stop_loss}</span>
          </div>
        </div>
      )}

      {/* Accuracy footnote */}
      {f.sector_hit_rate != null && (
        <div className="flex items-center justify-between border-t border-[var(--text-caption)]/20 pt-3">
          <span className="font-label">Sector hit-rate (60d)</span>
          <span className="font-data text-sm text-[var(--text-primary)]">{(f.sector_hit_rate * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
}
