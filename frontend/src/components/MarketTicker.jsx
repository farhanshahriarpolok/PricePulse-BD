import React from 'react';
import { TrendingUp, TrendingDown, Minus, Flame } from 'lucide-react';

export default function MarketTicker({ items = [], onSelectItem }) {
  if (!items || items.length === 0) return null;

  // Compute or extract percentage change indicators for ticker
  const formattedItems = items.map((item, index) => {
    // Generate deterministic trend change indicator based on price status and spread
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

  // Duplicate for continuous seamless marquee looping
  const marqueeItems = [...formattedItems, ...formattedItems];

  return (
    <div className="w-full bg-slate-950 border-b border-slate-800/80 overflow-hidden py-2 px-3 text-xs select-none">
      <div className="max-w-7xl mx-auto flex items-center">
        {/* Live Indicator Pill */}
        <div className="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full shrink-0 z-10 mr-3 text-[11px] font-semibold tracking-wider uppercase">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-0.5" />
          <span>Market Ticker</span>
        </div>

        {/* Marquee Container */}
        <div className="overflow-hidden flex-1 relative whitespace-nowrap mask-gradient">
          <div className="animate-ticker flex items-center gap-6">
            {marqueeItems.map((item, idx) => {
              const isUp = item.changePct > 0;
              const isDown = item.changePct < 0;

              return (
                <button
                  key={`${item.id}-${idx}`}
                  onClick={() => onSelectItem && onSelectItem(item.rawItem)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800/80 hover:border-slate-700 transition cursor-pointer group"
                >
                  <span className="font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                    {item.name}
                  </span>
                  <span className="font-mono text-slate-400 text-[11px]">
                    ৳{item.price.toFixed(1)}/{item.unit}
                  </span>

                  <span
                    className={`inline-flex items-center text-[11px] font-bold px-1.5 py-0.2 rounded ${
                      isUp
                        ? 'text-rose-400 bg-rose-500/10'
                        : isDown
                        ? 'text-emerald-400 bg-emerald-500/10'
                        : 'text-slate-400 bg-slate-700/30'
                    }`}
                  >
                    {isUp && <TrendingUp className="w-3 h-3 mr-0.5" />}
                    {isDown && <TrendingDown className="w-3 h-3 mr-0.5" />}
                    {!isUp && !isDown && <Minus className="w-3 h-3 mr-0.5" />}
                    {isUp ? `+${item.changePct}%` : isDown ? `${item.changePct}%` : '0.0%'}
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
