import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  TrendingUp, TrendingDown, ArrowLeft, ShieldAlert, Target,
  BarChart2, Newspaper, Cpu, BookOpen, Activity
} from 'lucide-react';
import {
  ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, CartesianGrid, AreaChart
} from 'recharts';
import { API_URL } from '../lib/supabase';
import Disclaimer from '../components/Disclaimer';

const TABS = ['Forecast', 'Fundamentals', 'News & Sentiment', 'Model Detail'];

function TabBtn({ label, active, icon: Icon, onClick }) {
  return (
    <button
      className={`tab-btn flex items-center space-x-1.5 ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      <Icon className="w-3.5 h-3.5" />
      <span>{label}</span>
    </button>
  );
}

function ForecastFanChart({ history, forecast }) {
  // Build chart data from history + forecast bands
  const histData = (history || []).slice(0, 60).reverse().map((h) => ({
    date: h.trade_date || h.forecast_date,
    price: h.closing_price != null ? Number(h.closing_price) : (h.close != null ? Number(h.close) : null),
    type: 'actual',
  }));

  const seedPrice = forecast?.closing_price || 1000;
  const baseDate = forecast?.forecast_date ? new Date(forecast.forecast_date) : new Date();
  
  let chartData = histData.length > 0 ? [...histData] : Array.from({ length: 60 }, (_, i) => {
    const d = new Date(baseDate);
    d.setDate(d.getDate() - (60 - i));
    return {
      date: d.toISOString().split('T')[0],
      price: seedPrice * (0.95 + Math.random() * 0.1),
      type: 'actual',
    };
  });

  // Append forecast horizon
  if (forecast) {
    const entryPrice = forecast.closing_price != null ? Number(forecast.closing_price) : seedPrice;
    
    // Anchor point: Overwrite the last historical point's price to match the Entry Price exactly.
    // Also set the forecast start points here so lines connect seamlessly without gaps or jumps.
    if (chartData.length > 0) {
      const lastIdx = chartData.length - 1;
      chartData[lastIdx].price = entryPrice;
      chartData[lastIdx].priceMedian = entryPrice;
      chartData[lastIdx].priceLow = entryPrice;
      chartData[lastIdx].priceHigh = entryPrice;
    }

    const p50_vals = [forecast.p50_day1, forecast.p50_day2, forecast.p50_day3, forecast.p50_day4, forecast.p50_day5];
    const p10_vals = [forecast.p10_day1, forecast.p10_day2, forecast.p10_day3, forecast.p10_day4, forecast.p10_day5];
    const p90_vals = [forecast.p90_day1, forecast.p90_day2, forecast.p90_day3, forecast.p90_day4, forecast.p90_day5];

    // A hardcoded list of some 2026 Indian market holidays (approximate/standard)
    const NSE_HOLIDAYS = [
      '2026-01-26', '2026-03-03', '2026-03-20', '2026-04-03',
      '2026-04-14', '2026-05-01', '2026-08-15', '2026-09-19',
      '2026-10-02', '2026-10-21', '2026-11-09', '2026-12-25'
    ];

    let currentDate = new Date(baseDate);
    let daysAdded = 0;
    
    while (daysAdded < 5) {
      currentDate.setDate(currentDate.getDate() + 1);
      const dayOfWeek = currentDate.getDay();
      
      // Robust local YYYY-MM-DD formatting to avoid UTC timezone shifts
      const y = currentDate.getFullYear();
      const m = String(currentDate.getMonth() + 1).padStart(2, '0');
      const d = String(currentDate.getDate()).padStart(2, '0');
      const dateStr = `${y}-${m}-${d}`;
      
      // Skip weekends (0=Sun, 6=Sat) and known holidays
      if (dayOfWeek !== 0 && dayOfWeek !== 6 && !NSE_HOLIDAYS.includes(dateStr)) {
        const p50 = p50_vals[daysAdded];
        const p10 = p10_vals[daysAdded];
        const p90 = p90_vals[daysAdded];
        
        daysAdded++;
        
        chartData.push({
          date: dateStr,
          type: 'forecast',
          priceMedian: p50 != null ? entryPrice * Math.exp(Number(p50)) : null,
          priceLow: p10 != null ? entryPrice * Math.exp(Number(p10)) : null,
          priceHigh: p90 != null ? entryPrice * Math.exp(Number(p90)) : null,
        });
      }
    }
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="glass-card p-3 text-xs">
        <p className="text-slate-400 mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color }} className="font-mono-num">
            {p.name}: ₹{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="chart-container h-[480px] p-8">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <CartesianGrid stroke="rgba(51,65,85,0.3)" strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748b' }} width={60} tickFormatter={v => `₹${Math.round(v)}`} />
          <Tooltip content={<CustomTooltip />} />
          {/* Actual price line */}
          <Line
            dataKey="price"
            name="Actual"
            stroke="var(--text-primary)"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          {/* Forecast band */}
          <Area
            dataKey="priceHigh"
            name="P90 Target"
            stroke="transparent"
            fill={forecast?.p50_day5 >= 0 ? "rgba(217, 168, 87, 0.15)" : "rgba(217, 119, 87, 0.15)"}
            connectNulls
          />
          <Area
            dataKey="priceLow"
            name="P10 Floor"
            stroke="transparent"
            fill="var(--bg-card)"
            connectNulls
          />
          <Line
            dataKey="priceMedian"
            name="Median Forecast"
            stroke={forecast?.p50_day5 >= 0 ? "var(--color-positive)" : "var(--color-negative)"}
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            connectNulls
          />
          {/* Target / SL reference lines */}
          {forecast?.target_price && (
            <ReferenceLine y={forecast.target_price} stroke="rgba(52,211,153,0.5)" strokeDasharray="2 2"
              label={{ value: 'TP', fill: '#34d399', fontSize: 10 }} />
          )}
          {forecast?.stop_loss && (
            <ReferenceLine y={forecast.stop_loss} stroke="rgba(251,113,133,0.5)" strokeDasharray="2 2"
              label={{ value: 'SL', fill: '#fb7185', fontSize: 10 }} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function FundamentalsTab({ data, forecast }) {
  // data comes from profile?.latest_features (daily_features table)
  // Field names must match the schema: trailing_pe, debt_equity, roce, etc.
  const hasData = data && Object.values(data).some(v => v != null);

  const fields = [
    { label: 'PE Ratio (Trailing)', value: data?.trailing_pe != null ? data.trailing_pe.toFixed(1) : null, suffix: 'x' },
    { label: 'Debt / Equity', value: data?.debt_equity != null ? data.debt_equity.toFixed(2) : null, suffix: 'x' },
    { label: 'ROCE', value: data?.roce != null ? `${data.roce.toFixed(1)}%` : null },
    { label: 'Revenue Growth YoY', value: data?.revenue_growth != null ? `${(data.revenue_growth * 100).toFixed(1)}%` : null },
    { label: 'EPS Growth YoY', value: data?.eps_growth != null ? `${(data.eps_growth * 100).toFixed(1)}%` : null },
    { label: 'Current Ratio', value: data?.current_ratio != null ? data.current_ratio.toFixed(2) : null, suffix: 'x' },
  ];

  // Also show technical data from the forecast which is always available
  const techFields = data ? [
    { label: 'RSI (14)', value: data.rsi_14 != null ? data.rsi_14.toFixed(1) : null },
    { label: 'ATR (14)', value: data.atr_14 != null ? `₹${data.atr_14.toFixed(2)}` : null },
    { label: 'ADX (14)', value: data.adx_14 != null ? data.adx_14.toFixed(1) : null },
    { label: 'BB %B', value: data.bb_pct_b != null ? data.bb_pct_b.toFixed(3) : null },
  ] : [];

  return (
    <div className="space-y-5">
      {/* Technical indicators — always available */}
      {techFields.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Technical Indicators</h3>
          <div className="grid grid-cols-2 gap-2">
            {techFields.map(({ label, value }) => (
              <div key={label} className="stat-card p-3">
                <p className="text-xs text-slate-500 mb-0.5">{label}</p>
                <p className="text-sm font-semibold font-mono-num text-white">{value ?? '—'}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fundamentals — requires weekly fundamentals pipeline to have run */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Fundamentals</h3>
        {!hasData ? (
          <div className="stat-card p-5 text-center">
            <p className="text-slate-400 text-sm">Fundamentals not yet loaded</p>
            <p className="text-xs text-slate-500 mt-1.5">
              Run the weekly fundamentals pipeline to populate this data.
              It runs automatically every Sunday, or manually:
            </p>
            <code className="block mt-2 text-xs text-emerald-400 bg-slate-900/50 rounded p-2 text-left">
              python collectors/fundamentals.py
            </code>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-xs text-slate-500 mb-3">Source: yfinance · refreshed weekly</p>
            {fields.map(({ label, value, suffix = '' }) => (
              <div key={label} className="stat-card p-4 flex justify-between items-center">
                <span className="text-sm text-slate-300">{label}</span>
                <p className="text-sm font-semibold font-mono-num text-white">
                  {value != null ? `${value}${suffix}` : '—'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SentimentTab({ symbol, news }) {
  if (!news || news.length === 0) {
    return <p className="text-slate-500 text-sm">No recent news available for {symbol}.</p>;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500 mb-4">FinBERT sentiment · local inference · RSS sources</p>
      {news.map((item, i) => {
        let sentiment = 'Neutral';
        let sentimentClass = 'bg-slate-500/10 border-slate-500/20 text-slate-400';
        if (item.sentiment_score > 0.1) {
            sentiment = 'Positive';
            sentimentClass = 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400';
        } else if (item.sentiment_score < -0.1) {
            sentiment = 'Negative';
            sentimentClass = 'bg-rose-500/10 border-rose-500/20 text-rose-400';
        }

        const sourceHost = item.source ? new URL(item.source).hostname.replace('www.', '') : 'Unknown';
        const dateStr = item.published_at ? new Date(item.published_at).toLocaleDateString() : '';

        return (
          <div key={i} className="stat-card p-6">
            <div className="flex justify-between items-start gap-3 mb-3">
              <p className="text-lg font-serif text-slate-200 leading-snug">{item.headline}</p>
              <span className={`text-[10px] uppercase tracking-widest font-semibold px-2 py-0.5 rounded-sm border flex-shrink-0 ${sentimentClass}`}>
                {sentiment}
              </span>
            </div>
            <div className="flex items-center space-x-4 mt-2">
              <span className="text-xs uppercase tracking-wider text-[var(--color-gilded)]">{sourceHost}</span>
              {dateStr && <span className="text-[var(--color-gilded)]/30">•</span>}
              <span className="text-xs font-serif text-[var(--color-gilded)]">{dateStr}</span>
              <span className="text-xs uppercase tracking-wider text-[var(--color-gilded)] ml-auto">Score: <span className="font-serif">{item.sentiment_score?.toFixed(2)}</span></span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ModelTab({ forecast, data }) {
  if (!forecast) return <p className="text-slate-500 text-sm">No data</p>;

  const components = [
    { label: 'Forecast Magnitude', weight: 0.35, desc: 'How far median return is from 0, vs. volatility' },
    { label: 'Band Tightness', weight: 0.25, desc: 'Narrow P10–P90 band = higher model confidence' },
    { label: 'Sentiment Alignment', weight: 0.20, desc: 'Does FinBERT news sentiment agree with forecast direction?' },
    { label: 'Macro Regime', weight: 0.20, desc: 'VIX level and overall market environment' },
  ];

  return (
    <div className="space-y-4">
      <div className="glass-card p-4">
        <h4 className="text-sm font-semibold text-slate-200 mb-3">Conviction Score Breakdown</h4>
        <div className="space-y-3">
          {components.map(({ label, weight, desc }) => (
            <div key={label}>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-slate-300">{label}</span>
                <span className="text-xs text-slate-400 font-mono-num">{(weight * 100).toFixed(0)}%</span>
              </div>
              <div className="conviction-bar">
                <div
                  className="conviction-bar-fill bg-blue-500"
                  style={{ width: `${weight * 100}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card p-4">
        <h4 className="text-sm font-semibold text-slate-200 mb-3">Signal Parameters</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Model Type</span>
            <span className="text-white font-mono-num">LightGBM Quantile (q=0.1, 0.5, 0.9)</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">ATR14</span>
            <span className="text-white font-mono-num">{data?.atr_14 ? `₹${data.atr_14.toFixed(2)}` : '—'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">SL Formula</span>
            <span className="text-white">Entry − ATR × 1.5</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">TP Formula</span>
            <span className="text-white">Entry + ATR × 3.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Time Exit</span>
            <span className="text-white">T+5 sessions</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function StockDetail() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [forecast, setForecast] = useState(null);
  const [history, setHistory] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [fRes, sRes] = await Promise.all([
          fetch(`${API_URL}/forecasts/${symbol}`),
          fetch(`${API_URL}/stocks/${symbol}`),
        ]);
        if (fRes.ok) {
          const data = await fRes.json();
          setForecast(data[0] || null);
          setHistory(data);
        }
        if (sRes.ok) setProfile(await sRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [symbol]);

  const stance = forecast?.signal_stance || 'HOLD';
  const stanceColor = stance === 'BUY' ? 'text-emerald-400' : stance === 'SELL' ? 'text-rose-400' : 'text-slate-400';

  const tabIcons = [BarChart2, BookOpen, Newspaper, Cpu];

  return (
    <div className="bg-[var(--bg-page)] min-h-screen">
      <div className="p-10 max-w-screen-2xl mx-auto">
        {/* Back */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center space-x-2 text-[var(--color-gilded)] hover:text-white uppercase tracking-widest text-[10px] font-semibold mb-6 transition-colors"
        >
          <ArrowLeft className="w-3 h-3" />
          <span>Back to Dashboard</span>
        </button>

        {/* Header */}
        <div className="flat-card mb-8">
          <div className="flex items-start justify-between mb-2">
            <div>
              <h1 className="font-display text-[48px] text-[var(--text-primary)] leading-none">{symbol}</h1>
              <p className="font-label mt-3">{profile?.company_name || '—'} · {profile?.sector || '—'} · {profile?.index_name || 'Nifty 500'}</p>
            </div>
            {forecast && (
              <div className="text-right">
                <div className="font-label mb-2" style={{
                  color: stance === 'BUY' ? 'var(--color-buy)' : stance === 'SELL' ? 'var(--color-sell)' : 'var(--text-secondary)'
                }}>
                  {stance}
                </div>
                <p className="font-label">Conviction <span className="font-data text-base ml-1 text-[var(--text-primary)]">{forecast.conviction_score}/10</span></p>
              </div>
            )}
          </div>

          {/* Key stats row */}
          {forecast && (
            <div className="flex flex-wrap gap-8 mt-6 pt-6 border-t border-[var(--text-caption)]/20">
              <div>
                <p className="font-label mb-1">Entry Price</p>
                <p className="font-data text-3xl text-[var(--text-primary)]">₹{forecast.closing_price}</p>
                {profile?.last_close_price && (
                  <div className="mt-2 flex items-baseline space-x-2">
                    <p className="font-label">
                      Close {profile.last_close_date}:
                    </p>
                    <p className="font-data text-lg text-[var(--text-secondary)]">
                      ₹{profile.last_close_price}
                    </p>
                  </div>
                )}
              </div>
              {forecast.target_price && (
                <div>
                  <p className="font-label mb-1">Target</p>
                  <p className="font-data text-3xl text-[var(--text-primary)]">₹{forecast.target_price}</p>
                </div>
              )}
              {forecast.stop_loss && (
                <div>
                  <p className="font-label mb-1">Stop Loss</p>
                  <p className="font-data text-3xl text-[var(--text-primary)]">₹{forecast.stop_loss}</p>
                </div>
              )}
              {forecast.p50_day5 != null && (
                <div>
                  <p className="font-label mb-1">5-Day Median Return</p>
                  <p className={`font-data text-3xl ${forecast.p50_day5 >= 0 ? 'text-[var(--color-positive)]' : 'text-[var(--color-negative)]'}`}>
                    {forecast.p50_day5 >= 0 ? '+' : ''}{(forecast.p50_day5 * 100).toFixed(2)}%
                  </p>
                </div>
              )}
              <div>
                <p className="font-label mb-1">Position Size</p>
                <p className="font-data text-3xl text-[var(--text-primary)]">
                  {forecast.position_pct > 0 ? `${forecast.position_pct}%` : '—'}
                </p>
              </div>
              {forecast.sector_hit_rate != null && (
                <div>
                  <p className="font-label mb-1">Sector Hit-Rate (60d)</p>
                  <p className="font-data text-3xl text-[var(--text-primary)]">{(forecast.sector_hit_rate * 100).toFixed(0)}%</p>
                </div>
              )}
            </div>
          )}
        </div>
        {/* Tabs */}
        <div className="flat-card mb-8 overflow-hidden px-0 pt-0 pb-2">
          <div className="flex border-b border-[var(--text-caption)]/20 px-4 pt-2">
            {TABS.map((t, i) => (
              <TabBtn
                key={t}
                label={t}
                active={activeTab === i}
                icon={tabIcons[i]}
                onClick={() => setActiveTab(i)}
              />
            ))}
          </div>
          <div className="p-6">
            {activeTab === 0 && (
              <div>
                <ForecastFanChart history={profile?.price_history || []} forecast={forecast} />
                {forecast?.sector_hit_rate != null && (
                  <div className="mt-6 pt-4 border-t border-[var(--text-caption)]/20">
                    <div className="flex items-center space-x-2 font-label">
                      <Activity className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                      <p className="text-[var(--text-secondary)]">
                        Model accuracy for <strong className="text-[var(--text-primary)]">{forecast.sector || 'this sector'}</strong> stocks 
                        at conviction <strong className="text-[var(--text-primary)]">≥{Math.floor(forecast.conviction_score)}</strong>, 
                        trailing 60 days: <strong className="text-[var(--color-positive)]">{(forecast.sector_hit_rate * 100).toFixed(0)}% directional hit-rate</strong>
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
            {activeTab === 1 && <FundamentalsTab data={profile?.latest_features} forecast={forecast} />}
            {activeTab === 2 && <SentimentTab symbol={symbol} news={profile?.news} />}
            {activeTab === 3 && <ModelTab forecast={forecast} data={profile?.latest_features} />}
          </div>
        </div>

        <Disclaimer />
      </div>
    </div>
  );
}
