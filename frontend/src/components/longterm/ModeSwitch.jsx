import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function ModeSwitch() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const isLongTerm = location.pathname.startsWith('/longterm');

  return (
    <div className="flex relative bg-[#0a0a0a]/50 rounded-xl p-1 mb-6 border border-[var(--color-highlight)]/10 mx-3 shadow-inner">
      <button
        onClick={() => {
          if (isLongTerm) {
            if (location.pathname.startsWith('/longterm/stock/')) {
              navigate(location.pathname.replace('/longterm/stock/', '/stock/'));
            } else {
              navigate('/dashboard');
            }
          }
        }}
        className={`relative flex-1 py-2 text-xs font-medium rounded-lg transition-colors z-10 ${!isLongTerm ? 'text-[var(--color-highlight)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
      >
        {!isLongTerm && (
          <motion.div
            layoutId="mode-pill"
            className="absolute inset-0 bg-gradient-to-br from-[var(--color-highlight)]/20 to-[var(--color-highlight)]/5 border border-[var(--color-highlight)]/30 rounded-lg shadow-lg"
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          />
        )}
        <span className="relative z-10 font-display text-sm tracking-wide">Short-Term</span>
        <span className="block relative z-10 text-[10px] font-data opacity-70 mt-0.5">5-Day</span>
      </button>
      <button
        onClick={() => {
          if (!isLongTerm) {
            if (location.pathname.startsWith('/stock/')) {
              navigate(location.pathname.replace('/stock/', '/longterm/stock/'));
            } else {
              navigate('/longterm');
            }
          }
        }}
        className={`relative flex-1 py-2 text-xs font-medium rounded-lg transition-colors z-10 ${isLongTerm ? 'text-emerald-400' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
      >
        {isLongTerm && (
          <motion.div
            layoutId="mode-pill"
            className="absolute inset-0 bg-gradient-to-br from-[var(--color-positive)]/20 to-[var(--color-positive)]/5 border border-[var(--color-positive)]/30 rounded-lg shadow-lg"
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          />
        )}
        <span className="relative z-10 font-display text-sm tracking-wide">Long-Term</span>
        <span className="block relative z-10 text-[10px] font-data opacity-70 mt-0.5">60-Day</span>
      </button>
    </div>
  );
}
