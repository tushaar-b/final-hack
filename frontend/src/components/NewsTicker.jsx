import React, { useEffect, useState } from 'react';
import { Newspaper } from 'lucide-react';
import { API_URL } from '../lib/supabase';

export default function NewsTicker() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchNews() {
      try {
        const res = await fetch(`${API_URL}/market/news`);
        if (res.ok) {
          const data = await res.json();
          setNews(data || []);
        }
      } catch (err) {
        console.error('Failed to load market news', err);
      } finally {
        setLoading(false);
      }
    }
    fetchNews();
  }, []);

  if (loading || news.length === 0) return null;

  // Get the most recent date from the loaded news
  const latestDate = new Date(
    Math.max(...news.map(n => new Date(n.published_at || n.created_at).getTime()))
  ).toLocaleDateString();

  return (
    <div className="ticker-wrap flex items-center h-12 mb-8 shadow-sm">
      <div className="bg-[var(--bg-card)] px-6 h-full flex items-center z-10 whitespace-nowrap shrink-0">
        <Newspaper className="w-4 h-4 text-[var(--text-secondary)] mr-3" />
        <span className="font-label text-[var(--text-primary)]">
          Market News
        </span>
        <span className="font-label text-[var(--text-secondary)] ml-4">
          {latestDate}
        </span>
      </div>
      
      <div className="flex-1 overflow-hidden relative h-full">
        <div className="ticker-content h-full flex items-center">
          {news.map((item, idx) => {
            let sentiment = 'Neutral';
            let dotColor = 'var(--text-secondary)';
            
            if (item.sentiment_score > 0.1) {
              sentiment = 'Pos';
              dotColor = 'var(--color-positive)';
            } else if (item.sentiment_score < -0.1) {
              sentiment = 'Neg';
              dotColor = 'var(--color-negative)';
            }

            return (
              <div key={idx} className="flex items-center mx-8">
                <span className="font-label text-[var(--text-secondary)] mr-4">{item.symbol}</span>
                <span className="font-display text-lg text-[var(--text-primary)] truncate max-w-xl">{item.headline}</span>
                <span className="ml-4 font-label flex items-center gap-1.5" style={{ color: dotColor }}>
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: dotColor }}></span>
                  {sentiment}
                </span>
                <span className="mx-8 text-[var(--text-caption)] opacity-50">•</span>
              </div>
            );
          })}
          {/* Duplicate for seamless looping */}
          {news.map((item, idx) => {
            let sentiment = 'Neutral';
            let dotColor = 'var(--text-secondary)';
            
            if (item.sentiment_score > 0.1) {
              sentiment = 'Pos';
              dotColor = 'var(--color-positive)';
            } else if (item.sentiment_score < -0.1) {
              sentiment = 'Neg';
              dotColor = 'var(--color-negative)';
            }

            return (
              <div key={`dup-${idx}`} className="flex items-center mx-8">
                <span className="font-label text-[var(--text-secondary)] mr-4">{item.symbol}</span>
                <span className="font-display text-lg text-[var(--text-primary)] truncate max-w-xl">{item.headline}</span>
                <span className="ml-4 font-label flex items-center gap-1.5" style={{ color: dotColor }}>
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: dotColor }}></span>
                  {sentiment}
                </span>
                <span className="mx-8 text-[var(--text-caption)] opacity-50">•</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
