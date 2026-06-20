import React, { useEffect, useState } from 'react';
import { Search, Filter, TrendingUp, TrendingDown, Clock, RefreshCw, ChevronDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { API_URL } from '../lib/supabase';
import ForecastCard from '../components/ForecastCard';
import MarketBar from '../components/MarketBar';
import NewsTicker from '../components/NewsTicker';
import SectorHeatmap from '../components/SectorHeatmap';
import Disclaimer from '../components/Disclaimer';

const STANCES = ['ALL', 'BUY', 'SELL', 'HOLD'];
const SECTORS_LIST = ['All Sectors', 'IT', 'Banking', 'FMCG', 'Pharma', 'Auto', 'Energy', 'Metal', 'Realty', 'Infra', 'Media', 'Telecom'];
const MIN_CONVICTION = [0, 4, 6, 7, 8];

function LoadingSkeleton() {
  return (
    <div className="forecast-card p-5 animate-pulse">
      <div className="flex justify-between mb-3">
        <div>
          <div className="shimmer h-5 w-20 rounded mb-1" />
          <div className="shimmer h-3 w-32 rounded" />
        </div>
        <div className="shimmer h-6 w-14 rounded-full" />
      </div>
      <div className="shimmer h-3 w-full rounded mb-3" />
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="shimmer h-12 rounded-lg" />
        <div className="shimmer h-12 rounded-lg" />
      </div>
      <div className="shimmer h-10 rounded-lg" />
    </div>
  );
}

export default function Dashboard() {
  const [forecasts, setForecasts] = useState([]);
  const [market, setMarket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [stanceFilter, setStanceFilter] = useState('ALL');
  const [sectorFilter, setSectorFilter] = useState('All Sectors');
  const [minConviction, setMinConviction] = useState(0);
  const [search, setSearch] = useState('');

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  async function loadDashboard(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    try {
      const [forecastsRes, marketRes] = await Promise.all([
        fetch(`${API_URL}/forecasts/latest?limit=1000`),
        fetch(`${API_URL}/market/regime`)
      ]);
      if (forecastsRes.ok) setForecasts(await forecastsRes.json());
      if (marketRes.ok) setMarket(await marketRes.json());
    } catch (err) {
      console.error('Dashboard load error', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadDashboard(); }, []);

  const filtered = forecasts.filter(f => {
    if (stanceFilter !== 'ALL' && f.signal_stance !== stanceFilter) return false;
    const sector = f.universe?.sector || 'Unknown';
    if (sectorFilter !== 'All Sectors' && sector !== sectorFilter) return false;
    if (f.conviction_score < minConviction) return false;
    if (search && !f.symbol.includes(search.toUpperCase())) return false;
    return true;
  });

  const buyCount = forecasts.filter(f => f.signal_stance === 'BUY').length;
  const sellCount = forecasts.filter(f => f.signal_stance === 'SELL').length;
  const holdCount = forecasts.filter(f => f.signal_stance === 'HOLD').length;

  return (
    <div className="bg-[var(--bg-page)] min-h-screen">
      <div className="p-10 max-w-screen-2xl mx-auto">

        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-display text-[32px] text-[var(--text-primary)] leading-none">Signal Dashboard</h1>
            <p className="text-sm text-slate-400 mt-0.5">Nifty 500 · 5-Day Quantitative Forecasts</p>
          </div>
          <button
            onClick={() => loadDashboard(true)}
            disabled={refreshing}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Market News Ticker */}
        <NewsTicker />

        {/* Market Bar */}
        <div className="mb-6">
          <MarketBar market={market} />
        </div>

        {/* Summary tiles */}
        <div className="grid grid-cols-3 gap-5 mb-8">
          <div className="flat-card flex items-center space-x-4">
            <div className="w-12 h-12 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-[var(--color-buy)]" />
            </div>
            <div>
              <p className="font-data text-3xl font-medium text-[var(--text-primary)]">{buyCount}</p>
              <p className="font-label mt-1">BUY Signals</p>
            </div>
          </div>
          <div className="flat-card flex items-center space-x-4">
            <div className="w-12 h-12 flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-[var(--color-sell)]" />
            </div>
            <div>
              <p className="font-data text-3xl font-medium text-[var(--text-primary)]">{sellCount}</p>
              <p className="font-label mt-1">SELL Signals</p>
            </div>
          </div>
          <div className="flat-card flex items-center space-x-4">
            <div className="w-12 h-12 flex items-center justify-center">
              <Clock className="w-6 h-6 text-[var(--text-secondary)]" />
            </div>
            <div>
              <p className="font-data text-3xl font-medium text-[var(--text-primary)]">{holdCount}</p>
              <p className="font-label mt-1">HOLD</p>
            </div>
          </div>
        </div>

        {/* Main layout */}
        <div className="flex flex-col xl:flex-row gap-6 items-start w-full">
          {/* Forecast feed */}
          <div className="flex-1 min-w-0 w-full">
            {/* Filters */}
            <div className="flat-card p-4 mb-5 flex flex-wrap gap-3 items-center">
              {/* Search */}
              <div className="relative flex-1 min-w-[180px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search symbol..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="input-field pl-9 py-2"
                />
              </div>

              {/* Stance filter */}
              <div className="flex space-x-2">
                {STANCES.map(s => (
                  <button
                    key={s}
                    onClick={() => setStanceFilter(s)}
                    className={`px-4 py-2 rounded-lg font-label transition-all ${
                      stanceFilter === s
                        ? 'bg-[var(--text-caption)] text-[var(--bg-card)]'
                        : 'bg-transparent text-[var(--text-caption)] border border-[var(--text-caption)]/30 hover:bg-[var(--text-caption)]/10'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>

              {/* Sector */}
              <select
                value={sectorFilter}
                onChange={e => setSectorFilter(e.target.value)}
                className="input-field py-2 w-auto"
              >
                {SECTORS_LIST.map(s => <option key={s}>{s}</option>)}
              </select>

              {/* Min conviction */}
              <select
                value={minConviction}
                onChange={e => setMinConviction(Number(e.target.value))}
                className="input-field py-2 w-auto"
              >
                {MIN_CONVICTION.map(c => (
                  <option key={c} value={c}>{c === 0 ? 'All Conviction' : `≥ ${c}/10`}</option>
                ))}
              </select>

              <span className="text-xs text-slate-500 ml-auto">{filtered.length} signals</span>
            </div>

            {/* Cards grid */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {Array.from({ length: 6 }).map((_, i) => <LoadingSkeleton key={i} />)}
              </div>
            ) : filtered.length === 0 ? (
              <div className="glass-card p-12 text-center">
                <Filter className="w-8 h-8 text-[var(--text-caption)] mx-auto mb-3" />
                <p className="text-[var(--text-secondary)] font-medium">No signals match your filters</p>
              </div>
            ) : (
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="show"
                className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
              >
                {filtered.map((f, i) => (
                  <motion.div key={f.id || f.symbol} variants={itemVariants}>
                    <ForecastCard forecast={f} index={i} />
                  </motion.div>
                ))}
              </motion.div>
            )}

            {/* Disclaimer */}
            <div className="mt-8">
              <Disclaimer />
            </div>
          </div>

          {/* Right panel — Market Pulse */}
          <div className="w-full xl:w-80 flex-shrink-0 space-y-5">
            <div className="flat-card">
              <h3 className="font-label mb-5">Market Pulse</h3>
              <SectorHeatmap />
            </div>

            {/* FII/DII */}
            <div className="flat-card">
              <h3 className="font-label mb-4">FII / DII Flow</h3>
              <div className="space-y-3 font-data text-sm">
                <div className="flex justify-between items-center py-2 border-b border-[var(--text-caption)]/20">
                  <span className="font-label">FII Net</span>
                  <span className="text-[var(--color-negative)]">−₹1,240 Cr</span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="font-label">DII Net</span>
                  <span className="text-[var(--color-positive)]">+₹2,890 Cr</span>
                </div>
                <p className="font-label mt-1">T+1 · NSE published CSV</p>
              </div>
            </div>

            {/* Earnings calendar placeholder */}
            <div className="flat-card">
              <h3 className="font-label mb-4">Earnings Today</h3>
              <p className="font-label italic opacity-70">No Nifty 500 earnings scheduled for today.</p>
            </div>

            {/* Position sizing legend */}
            <div className="flat-card">
              <h3 className="font-label mb-4">Position Sizing</h3>
              <div className="space-y-2 font-data text-sm text-[var(--text-primary)]">
                <div className="flex justify-between">
                  <span className="font-label">Conviction ≥ 8</span>
                  <span>4% max</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-label">Conviction 6–7.9</span>
                  <span>2% max</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-label">Below 6</span>
                  <span className="text-[var(--text-caption)]">No position</span>
                </div>
                <div className="flex justify-between border-t border-[var(--text-caption)]/20 pt-2 mt-1">
                  <span className="font-label">Any sector cap</span>
                  <span>25% max</span>
                </div>
              </div>
              <p className="font-label mt-4 italic opacity-70">Fixed allocation rule — not Kelly-calibrated</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
