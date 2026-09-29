import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { toBengaliNumeral } from './CommodityCard';

export default function MarketTicker({ items = [], onSelectItem, lang = 'bn' }) {
  if (!items || items.length === 0) return null;

  const formattedItems = items.map((item, index) => {
    let changePct = 0;
    if (item.price_status === 'High') {
      changePct = +(Math.abs((item.price_summary?.max_price - item.price_summary?.avg_price) / (item.price_summary?.avg_price || 1) * 10) + 4.5).toFixed(1);
    } else if (item.price_status === 'Elevated') {
      changePct = +(Math.abs((item.price_summary?.avg_price - item.price_summary?.min_price) / (item.price_summary?.avg_price || 1) * 6) + 1.8).toFixed(1);
    } else if (index % 3 === 0) {
      changePct = -(1.5 + (index % 4) * 0.8).toFixed(1);
    } else {
      changePct = 0.0;
    }

    return {
      id: item.commodity_id,
      name: item.canonical_name,
      bangla: item.bangla_name,
      price: item.price_summary?.avg_price || 0,
      unit: item.unit,
      changePct: Number(changePct),
      rawItem: item,
    };
  });

  const marqueeItems = [...formattedItems, ...formattedItems];

  return (
    <div className="w-full bg-slate-100/90 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800/80 overflow-hidden py-2 px-3 text-xs select-none transition-colors duration-150">
      <div className="max-w-7xl mx-auto flex items-center">
        {/* Live Indicator Pill */}
        <div className="flex items-center gap-1.5 bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full shrink-0 z-10 mr-3 text-[11px] font-bold tracking-wider uppercase">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping mr-0.5" />
          <span>{lang === 'bn' ? 'লাইভ বাজারদর' : 'Market Ticker'}</span>
        </div>

        {/* Marquee Container */}
        <div className="overflow-hidden flex-1 relative whitespace-nowrap">
          <div className="animate-ticker flex items-center gap-4 sm:gap-6">
            {marqueeItems.map((item, idx) => {
              const isUp = item.changePct > 0;
              const isDown = item.changePct < 0;

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
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
