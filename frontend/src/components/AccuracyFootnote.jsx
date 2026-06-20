import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { Activity } from 'lucide-react';

export default function AccuracyFootnote() {
  const [accuracy, setAccuracy] = useState(null);
  const [sharpe, setSharpe] = useState(null);

  useEffect(() => {
    async function fetchAccuracy() {
      const { data, error } = await supabase
        .from('model_registry')
        .select('backtest_accuracy, backtest_sharpe')
        .eq('status', 'champion')
        .order('trained_at', { ascending: false })
        .limit(1)
        .single();

      if (!error && data) {
        setAccuracy((data.backtest_accuracy * 100).toFixed(2));
        setSharpe(data.backtest_sharpe?.toFixed(2));
      }
    }
    fetchAccuracy();
  }, []);

  if (accuracy === null) return null;

  return (
    <div className="flex items-center space-x-2 text-xs text-slate-500 mt-3 pt-3 border-t border-slate-700/50">
      <Activity className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
      <span>
        System trailing accuracy: <strong className="text-white">{accuracy}%</strong>
        {sharpe && <> · Sharpe: <strong className="text-white">{sharpe}</strong></>}
      </span>
      <span className="ml-auto italic opacity-60 hidden sm:block">Updated weekly</span>
    </div>
  );
}
