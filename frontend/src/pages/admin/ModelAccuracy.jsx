import React, { useEffect, useState } from 'react';
import { TrendingUp, Target, BarChart2, Award, AlertTriangle } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine
} from 'recharts';

function MetricCard({ label, value, sub, color = 'text-white', icon: Icon, iconColor = 'text-blue-400' }) {
  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
        <Icon className={`w-4 h-4 ${iconColor}`} />
      </div>
      <p className={`text-2xl font-bold font-mono-num ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function ModelAccuracy() {
  const [champion, setChampion] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const { data } = await supabase
        .from('model_registry')
        .select('*')
        .eq('status', 'champion')
        .order('trained_at', { ascending: false })
        .limit(1);
      setChampion(data?.[0] || null);
      setLoading(false);
    }
    load();
  }, []);

  // Mock rolling accuracy for chart (would come from signal_outcomes in real system)
  const mockRolling = Array.from({ length: 30 }, (_, i) => ({
    day: `D-${30-i}`,
    accuracy: 52 + Math.random() * 12,
    sharpe: 0.8 + Math.random() * 0.8,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="glass-card p-2.5 text-xs">
        <p className="text-slate-400 mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color }}>{p.name}: {p.value.toFixed(1)}{p.name === 'Accuracy' ? '%' : ''}</p>
        ))}
      </div>
    );
  };

  return (
    <div className="bg-mesh min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <BarChart2 className="w-6 h-6 text-violet-400" />
            <span>Model Accuracy</span>
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Champion model performance · rolling 30/60/90-day metrics</p>
        </div>

        {/* Champion badge */}
        {champion && (
          <div className="glass-card p-4 mb-5 flex items-center space-x-3 border-violet-500/20">
            <div className="w-10 h-10 rounded-xl bg-violet-500/15 flex items-center justify-center">
              <Award className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Champion Model</p>
              <p className="text-xs text-slate-400">
                {champion.model_type || 'LightGBM Quantile'} · Trained {champion.trained_at ? new Date(champion.trained_at).toLocaleDateString('en-IN') : 'unknown'}
              </p>
            </div>
            <div className="ml-auto px-3 py-1 bg-violet-500/15 rounded-full text-xs text-violet-400 border border-violet-500/20">
              Champion
            </div>
          </div>
        )}

        {/* Metrics grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Directional Accuracy"
            value={champion ? `${(champion.backtest_accuracy * 100).toFixed(1)}%` : '—'}
            sub="Walk-forward backtest"
            color={champion?.backtest_accuracy > 0.55 ? 'text-emerald-400' : 'text-amber-400'}
            icon={Target}
            iconColor="text-emerald-400"
          />
          <MetricCard
            label="Sharpe Ratio"
            value={champion ? champion.backtest_sharpe?.toFixed(2) : '—'}
            sub="Annualised"
            color={champion?.backtest_sharpe > 1 ? 'text-emerald-400' : 'text-amber-400'}
            icon={TrendingUp}
            iconColor="text-blue-400"
          />
          <MetricCard
            label="Training Samples"
            value={champion?.training_samples?.toLocaleString() ?? '—'}
            sub="Across Nifty 500"
            icon={BarChart2}
            iconColor="text-violet-400"
          />
          <MetricCard
            label="Features Used"
            value={champion?.num_features ?? '30'}
            sub="See §8.2 for feature list"
            icon={Award}
            iconColor="text-amber-400"
          />
        </div>

        {/* Rolling accuracy chart */}
        <div className="glass-card p-5 mb-5">
          <h2 className="text-sm font-semibold text-slate-200 mb-4">Rolling Directional Accuracy (30-day window)</h2>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockRolling} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                <CartesianGrid stroke="rgba(51,65,85,0.3)" strokeDasharray="3 3" />
                <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#64748b' }} interval={4} />
                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} domain={[40, 80]} tickFormatter={v => `${v}%`} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={50} stroke="rgba(100,116,139,0.5)" strokeDasharray="4 4" label={{ value: '50% (random)', fill: '#64748b', fontSize: 10 }} />
                <Line dataKey="accuracy" name="Accuracy" stroke="#60a5fa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Note: chart shows mock data until outcome tracking is fully operational (T+5 close tracking required).
          </p>
        </div>

        {/* Feature drift warning */}
        <div className="glass-card p-5">
          <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Feature Drift Monitor</span>
          </h2>
          {champion ? (
            <p className="text-sm text-slate-400">
              Population Stability Index (PSI) monitoring will be active once the model has served signals for 30+ days.
              PSI &gt; 0.2 on any feature will trigger a drift flag here.
            </p>
          ) : (
            <p className="text-sm text-slate-500">
              No champion model found in <code className="text-slate-300">model_registry</code> table.
              Run the training pipeline to create one.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
