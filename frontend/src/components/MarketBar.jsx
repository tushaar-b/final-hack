import React from 'react';
import { TrendingUp, TrendingDown, Activity, AlertTriangle, Clock } from 'lucide-react';

function StatItem({ label, value, sub, valueClass = '' }) {
  return (
    <div>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-0.5">{label}</p>
      <p className={`text-sm font-semibold font-mono-num ${valueClass || 'text-white'}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

export default function MarketBar({ market }) {
  if (!market) return null;

  const regimeClass =
    market.regime === 'NORMAL' ? 'regime-normal' :
    market.regime === 'HIGH_VOLATILITY' ? 'regime-high-vol' :
    'regime-low-vol';

  const regimeLabel =
    market.regime === 'NORMAL' ? 'Normal' :
    market.regime === 'HIGH_VOLATILITY' ? 'High Vol' : 'Low Vol';

  const niftyChange = market.nifty_change_pct;

  // Calculate Market Open/Closed based on IST (UTC+5:30)
  // Market hours: Mon-Fri, 09:15 to 15:30 IST
  const now = new Date();
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
  const istDate = new Date(utc + (5.5 * 60 * 60 * 1000));
  const day = istDate.getDay();
  const hours = istDate.getHours();
  const minutes = istDate.getMinutes();

  const isWeekend = day === 0 || day === 6;
  const isMarketHours = !isWeekend && 
    (hours > 9 || (hours === 9 && minutes >= 15)) && 
    (hours < 15 || (hours === 15 && minutes <= 30));
    
  const marketStatus = isMarketHours ? 'MARKET OPEN' : 'MARKET CLOSED';
  const statusClasses = isMarketHours 
    ? 'bg-emerald-500/10 text-[var(--color-buy)] border border-emerald-500/20' 
    : 'bg-rose-500/10 text-[var(--color-sell)] border border-rose-500/20';

  return (
    <div className="glass-card px-5 py-3 flex items-center justify-between gap-6 flex-wrap">
      {/* Left: Live indicator */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="live-dot" />
          <span className="font-label normal-case">
            EOD · as of {market.trade_date || 'today'}
          </span>
        </div>
        <div className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-widest ${statusClasses}`}>
          {marketStatus}
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center space-x-6 flex-wrap gap-y-2">
        <StatItem
          label="Nifty 50"
          value={market.nifty_50 ? market.nifty_50.toLocaleString('en-IN') : '—'}
          valueClass={niftyChange >= 0 ? 'text-emerald-400' : niftyChange < 0 ? 'text-rose-400' : 'text-white'}
        />
        <StatItem
          label="India VIX"
          value={market.india_vix?.toFixed(2)}
          valueClass={
            market.india_vix > 25 ? 'text-rose-400' :
            market.india_vix < 12 ? 'text-amber-400' : 'text-white'
          }
        />
        {market.usd_inr && (
          <StatItem label="USD/INR" value={market.usd_inr?.toFixed(2)} />
        )}
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-0.5">Regime</p>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${regimeClass}`}>
            {regimeLabel}
          </span>
        </div>
        {market.india_vix >= 22 && (
          <div className="flex items-center space-x-1.5 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span className="text-xs text-rose-400 font-medium">VIX Circuit Breaker — No new BUY signals</span>
          </div>
        )}
      </div>

      {/* Pipeline freshness */}
      {market.pipeline_stale && (
        <div className="flex items-center space-x-1.5 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-xs text-amber-400">Stale data — pipeline may not have run today</span>
        </div>
      )}
    </div>
  );
}
