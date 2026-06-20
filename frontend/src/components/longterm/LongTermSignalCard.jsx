import React from 'react';
import { useNavigate } from 'react-router-dom';
import FactorBreakdown from './FactorBreakdown';
import { ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LongTermSignalCard({ signal }) {
  const navigate = useNavigate();

  const getExplanation = (signal) => {
    const factors = [
      { name: 'strong recent momentum', val: signal.momentum_z || 0 },
      { name: 'low volatility', val: signal.lowvol_z || 0 },
      { name: 'high delivery accumulation', val: signal.delivery_z || 0 }
    ];
    factors.sort((a, b) => b.val - a.val);
    
    const top = factors[0];
    const second = factors[1];
    
    if (top.val < 0) return "Ranked based on composite factor profile.";
    if (top.val >= 0.5 && second.val >= 0) return `Led by ${top.name} & ${second.name}.`;
    return `Led primarily by ${top.name}.`;
  };

  return (
    <motion.div 
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      onClick={() => navigate(`/longterm/stock/${signal.symbol}`)}
      className="bg-[var(--bg-card)] backdrop-blur-xl border border-[var(--color-highlight)]/10 rounded-2xl p-6 hover:border-[var(--color-highlight)]/30 hover:shadow-[0_12px_40px_rgba(212,175,55,0.1)] cursor-pointer group flex flex-col h-full relative overflow-hidden"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[var(--color-highlight)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      
      <div className="flex justify-between items-start mb-4 relative z-10 gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-2xl font-display text-[var(--text-primary)] group-hover:text-[var(--color-highlight)] transition-colors truncate">
            {signal.symbol}
          </h3>
          {signal.rank_in_sector && (
             <p className="text-xs font-label text-[var(--text-secondary)] mt-1 truncate">Sector Rank: #{signal.rank_in_sector}</p>
          )}
        </div>
        <div className="flex flex-col items-end flex-shrink-0">
          <div className="bg-[var(--bg-page)] px-4 py-1.5 rounded-full text-sm font-data text-[var(--color-highlight)] border border-[var(--color-highlight)]/20 shadow-inner">
            #{signal.rank_in_universe}
          </div>
          <span className="text-[10px] text-[var(--text-caption)] mt-2 uppercase tracking-widest font-label truncate max-w-[100px]">
            Score: {signal.display_score != null ? signal.display_score.toFixed(1) : 'N/A'}
          </span>
        </div>
      </div>

      <div className="mb-6 bg-[var(--color-positive)]/5 border border-[var(--color-positive)]/10 rounded-lg px-3 py-2 text-xs text-[var(--text-primary)] font-data relative z-10">
        <span className="font-semibold text-[var(--color-positive)]">Why #{signal.rank_in_universe}: </span>
        <span className="text-[var(--text-secondary)]">{getExplanation(signal)}</span>
      </div>

      <div className="flex-grow flex items-center justify-center py-2 relative z-10">
        <FactorBreakdown signal={signal} />
      </div>

      <div className="mt-6 pt-4 border-t border-[var(--text-caption)]/10 flex justify-between items-center text-xs font-label tracking-widest uppercase text-[var(--text-caption)] group-hover:text-[var(--color-highlight)] transition-colors relative z-10">
        <span>View Details</span>
        <ChevronRight className="w-4 h-4 opacity-50 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
      </div>
    </motion.div>
  );
}
