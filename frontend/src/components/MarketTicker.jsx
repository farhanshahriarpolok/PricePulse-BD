import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, X } from 'lucide-react';
import { toBengaliNumeral } from './CommodityCard';

export default function MarketTicker({ items = [], onSelectItem, lang = 'bn' }) {
  const [isDismissed, setIsDismissed] = useState(() => {
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        return window.sessionStorage.getItem('pricepulse_ticker_dismissed') === 'true';
      }
    } catch (e) {}
    return false;
  });

  const [isPaused, setIsPaused] = useState(false);

  if (isDismissed || !items || items.length === 0) return null;

  const handleDismiss = (e) => {
    e.stopPropagation();
    setIsDismissed(true);
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.setItem('pricepulse_ticker_dismissed', 'true');
      }
    } catch (e) {}
  };

  const formattedItems = items.map((item) => {
    const rawPct = item.percentage_change_7d !== undefined
      ? item.percentage_change_7d
      : item.price_change_pct !== undefined
      ? item.price_change_pct
      : item.change_pct !== undefined
      ? item.change_pct
      : null;

    const changePct = rawPct !== null && !isNaN(rawPct) ? Number(Number(rawPct).toFixed(1)) : null;

    return {
      id: item.commodity_id,
      name: item.canonical_name,
      bangla: item.bangla_name,
      price: item.price_summary?.avg_price || item.retail_price || item.benchmark_price || 0,
      unit: item.unit,
      changePct: changePct,
      rawItem: item,
    };
  });

  const marqueeItems = [...formattedItems, ...formattedItems];

  return (
    <div 
      className="w-full overflow-hidden bg-slate-100/90 dark:bg-slate-950/90 border-b border-slate-200 dark:border-slate-800/80 py-1.5 px-3 text-xs select-none transition-colors duration-150 backdrop-blur-md"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={() => setIsPaused(true)}
      onTouchEnd={() => setIsPaused(false)}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-2 min-w-0 overflow-hidden">
        {/* Live Indicator Pill */}
        <div className="flex items-center gap-1.5 bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full shrink-0 z-10 mr-1 sm:mr-3 text-[11px] font-bold tracking-wider uppercase">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping mr-0.5" />
          <span className="hidden xs:inline">{lang === 'bn' ? 'লাইভ বাজারদর' : 'Live Ticker'}</span>
          <span className="xs:hidden">{lang === 'bn' ? 'লাইভ' : 'Live'}</span>
        </div>

        {/* Marquee Container with Hover-Pause */}
        <div className="overflow-hidden flex-1 min-w-0 relative whitespace-nowrap">
          <div className={`animate-ticker flex items-center gap-4 sm:gap-6 ${isPaused ? 'paused' : ''}`}>
            {marqueeItems.map((item, idx) => {
              const isUp = item.changePct !== null && item.changePct > 0;
              const isDown = item.changePct !== null && item.changePct < 0;

              return (
                <button
                  key={`${item.id}-${idx}`}
                  type="button"
                  onClick={() => onSelectItem && onSelectItem(item.rawItem)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900/80 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition cursor-pointer group shadow-xs"
                >
                  <span className="font-bold text-slate-800 dark:text-slate-200 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                    {lang === 'bn' ? (item.bangla || item.name) : item.name}
                  </span>
                  <span className="font-mono text-slate-600 dark:text-slate-400 text-[11px]">
                    ৳{toBengaliNumeral(item.price.toFixed(1), lang)}/{item.unit || 'কেজি'}
                  </span>

                  {item.changePct !== null && (
                    <span
                      className={`inline-flex items-center text-[10px] font-bold px-1.5 py-0.2 rounded ${
                        isUp
                          ? 'text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-500/10'
                          : isDown
                          ? 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10'
                          : 'text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700/30'
                      }`}
                    >
                      {isUp && <TrendingUp className="w-3 h-3 mr-0.5" />}
                      {isDown && <TrendingDown className="w-3 h-3 mr-0.5" />}
                      {!isUp && !isDown && <Minus className="w-3 h-3 mr-0.5" />}
                      {isUp ? `+${toBengaliNumeral(item.changePct, lang)}%` : isDown ? `${toBengaliNumeral(item.changePct, lang)}%` : '০%'}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Dismiss Button [×] */}
        <button
          type="button"
          onClick={handleDismiss}
          title={lang === 'bn' ? 'টিকার বন্ধ করুন' : 'Dismiss ticker'}
          aria-label="Dismiss ticker"
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-800/80 transition-colors shrink-0 ml-1"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
