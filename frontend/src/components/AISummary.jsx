import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';

export default function AISummary({ trades }) {
  const [text, setText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!trades || trades.length === 0) {
      setText("You haven't logged any trades yet. Start building your portfolio to unlock AI-powered insights!");
      return;
    }

    const total = trades.length;
    const closed = trades.filter(t => t.exitPrice != null);
    const open = total - closed.length;
    
    const wins = closed.filter(t => t.side === 'BUY' ? t.exitPrice > t.entryPrice : t.exitPrice < t.entryPrice);
    const winRate = closed.length > 0 ? ((wins.length / closed.length) * 100).toFixed(0) : 0;
    
    let bestTrade = null;
    let worstTrade = null;
    let maxPnL = -Infinity;
    let minPnL = Infinity;
    let totalPnL = 0;
    
    for (let t of closed) {
      const pnl = t.side === 'BUY' ? (t.exitPrice - t.entryPrice) * t.qty : (t.entryPrice - t.exitPrice) * t.qty;
      totalPnL += pnl;
      if (pnl > maxPnL) { maxPnL = pnl; bestTrade = t; }
      if (pnl < minPnL) { minPnL = pnl; worstTrade = t; }
    }
    
    let summary = `You have logged ${total} trades so far, with ${open} currently active. `;
    
    if (closed.length > 0) {
      summary += `Out of your ${closed.length} closed positions, you maintain a win rate of ${winRate}%. `;
      
      if (totalPnL > 0) {
        summary += `Your portfolio is profitable with a net realized gain of ₹${totalPnL.toFixed(0)}. `;
      } else if (totalPnL < 0) {
        summary += `Your realized P&L is sitting at ₹${totalPnL.toFixed(0)}. `;
      }
      
      if (bestTrade && maxPnL > 0) {
        summary += `Your most successful play was on ${bestTrade.symbol}, netting ₹${maxPnL.toFixed(0)}. `;
      }
      if (worstTrade && minPnL < 0) {
        summary += `Your largest drawdown came from ${worstTrade.symbol} (₹${Math.abs(minPnL).toFixed(0)} loss). `;
      }
      
      if (winRate >= 60) {
        summary += `Overall, your strategy demonstrates a strong edge. Keep trusting your core signals!`;
      } else if (winRate < 40) {
        summary += `Consider reviewing the setups that led to recent losses and practicing strict risk management.`;
      } else {
        summary += `Your win rate is balanced. Maintaining a strict risk-to-reward ratio will be key to compounding.`;
      }
    } else {
      summary += `Once you close some positions, Aarthi AI will deeply analyze your win rate and profitability metrics here.`;
    }

    // Typewriter effect
    setIsTyping(true);
    let i = 0;
    setText('');
    const interval = setInterval(() => {
      setText(summary.substring(0, i));
      i++;
      if (i > summary.length) {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 15);

    return () => clearInterval(interval);
  }, [trades]);

  return (
    <div className="glass-card p-5 mb-5 border-violet-500/30 relative overflow-hidden group">
      {/* Background glow */}
      <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-fuchsia-500/10 opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative z-10 flex gap-4">
        <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center shrink-0 shadow-[0_0_15px_rgba(139,92,246,0.3)]">
          <Sparkles className="w-5 h-5 text-violet-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white mb-1.5 flex items-center gap-2">
            Aarthi AI Analysis
            {isTyping && <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />}
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed font-medium">
            {text}
          </p>
        </div>
      </div>
    </div>
  );
}
