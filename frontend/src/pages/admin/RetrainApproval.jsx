import React, { useEffect, useState } from 'react';
import { Shield, CheckCircle, XCircle, TrendingUp, TrendingDown, AlertTriangle, RefreshCw } from 'lucide-react';
import { supabase } from '../../lib/supabase';

function ModelCompareRow({ label, champion, challenger, higherBetter = true }) {
  const champVal = champion != null ? champion : null;
  const challVal = challenger != null ? challenger : null;
  const challWins = challVal != null && champVal != null &&
    (higherBetter ? challVal > champVal : challVal < champVal);

  return (
    <div className="grid grid-cols-3 gap-3 py-2.5 border-b border-slate-700/30 items-center">
      <span className="text-xs text-slate-400">{label}</span>
      <div className="text-center">
        <span className="text-sm font-mono-num font-semibold text-white">
          {champVal != null ? (typeof champVal === 'number' ? champVal.toFixed(4) : champVal) : '—'}
        </span>
      </div>
      <div className="text-center">
        <span className={`text-sm font-mono-num font-semibold ${challWins ? 'text-emerald-400' : 'text-slate-300'}`}>
          {challVal != null ? (typeof challVal === 'number' ? challVal.toFixed(4) : challVal) : '—'}
          {challWins && ' ↑'}
        </span>
      </div>
    </div>
  );
}

export default function RetrainApproval() {
  const [champion, setChampion] = useState(null);
  const [challenger, setChallenger] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState(null);

  async function load() {
    const { data } = await supabase
      .from('model_registry')
      .select('*')
      .order('trained_at', { ascending: false })
      .limit(5);
    
    setChampion(data?.find(m => m.status === 'champion') || null);
    setChallenger(data?.find(m => m.status === 'challenger') || null);
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  const promoteChallenger = async () => {
    if (!challenger) return;
    setActionLoading(true);
    // Demote current champion
    if (champion) {
      await supabase.from('model_registry').update({ status: 'retired' }).eq('id', champion.id);
    }
    // Promote challenger
    await supabase.from('model_registry').update({ status: 'champion' }).eq('id', challenger.id);
    setMessage({ type: 'success', text: 'Challenger promoted to Champion!' });
    setTimeout(() => setMessage(null), 3000);
    setActionLoading(false);
    load();
  };

  const discardChallenger = async () => {
    if (!challenger) return;
    setActionLoading(true);
    await supabase.from('model_registry').update({ status: 'discarded' }).eq('id', challenger.id);
    setMessage({ type: 'info', text: 'Challenger discarded. Champion continues.' });
    setTimeout(() => setMessage(null), 3000);
    setActionLoading(false);
    load();
  };

  return (
    <div className="bg-mesh min-h-screen p-6">
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Shield className="w-6 h-6 text-emerald-400" />
            <span>Retrain Approval</span>
          </h1>
          <p className="text-slate-400 text-sm mt-0.5">Manual champion/challenger promotion · Nothing auto-promotes</p>
        </div>

        {message && (
          <div className={`mb-5 flex items-center space-x-2 p-3 rounded-lg border ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
              : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
          }`}>
            {message.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        {loading ? (
          <div className="space-y-4">
            {[1,2].map(i => <div key={i} className="shimmer h-40 rounded-xl" />)}
          </div>
        ) : !challenger ? (
          <div className="glass-card p-10 text-center">
            <RefreshCw className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No challenger model pending</p>
            <p className="text-sm text-slate-500 mt-1">
              The weekly retrain job will create a challenger automatically.
              Run <code className="text-slate-300">python train.py --mode challenger</code> to trigger manually.
            </p>
          </div>
        ) : (
          <>
            {/* Comparison table */}
            <div className="glass-card p-5 mb-5">
              <div className="grid grid-cols-3 gap-3 mb-3">
                <span className="text-xs text-slate-500 uppercase tracking-wider">Metric</span>
                <div className="text-center">
                  <span className="text-xs font-semibold text-violet-400 uppercase">Champion</span>
                  <p className="text-xs text-slate-500">{champion?.model_type || 'LightGBM'}</p>
                </div>
                <div className="text-center">
                  <span className="text-xs font-semibold text-blue-400 uppercase">Challenger</span>
                  <p className="text-xs text-slate-500">{challenger?.model_type || 'LightGBM'}</p>
                </div>
              </div>
              <ModelCompareRow label="Directional Accuracy" champion={champion?.backtest_accuracy} challenger={challenger?.backtest_accuracy} />
              <ModelCompareRow label="Sharpe Ratio" champion={champion?.backtest_sharpe} challenger={challenger?.backtest_sharpe} />
              <ModelCompareRow label="Training Samples" champion={champion?.backtest_metrics_json?.training_samples} challenger={challenger?.backtest_metrics_json?.training_samples} />
              <ModelCompareRow label="Trained At" champion={champion?.trained_at ? new Date(champion.trained_at).toLocaleDateString() : null} challenger={challenger?.trained_at ? new Date(challenger.trained_at).toLocaleDateString() : null} higherBetter={false} />
            </div>

            {/* Advisory */}
            <div className="glass-card p-4 mb-5 bg-amber-500/5 border-amber-500/20">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-amber-300/80">
                  <strong>Promotion guidance:</strong> Promote only if challenger shows ≥0.5pp improvement in directional accuracy
                  AND comparable or better Sharpe. If metrics are similar, the champion wins (stability preference).
                  If you don't act, the champion keeps serving.
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={promoteChallenger}
                disabled={actionLoading}
                className="flex items-center justify-center space-x-2 bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold py-3 rounded-xl transition-all hover:shadow-lg hover:shadow-emerald-500/20"
              >
                <CheckCircle className="w-4 h-4" />
                <span>Promote Challenger</span>
              </button>
              <button
                onClick={discardChallenger}
                disabled={actionLoading}
                className="flex items-center justify-center space-x-2 bg-slate-700/50 hover:bg-slate-700 text-rose-400 font-semibold py-3 rounded-xl border border-rose-500/20 transition-all"
              >
                <XCircle className="w-4 h-4" />
                <span>Discard Challenger</span>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
