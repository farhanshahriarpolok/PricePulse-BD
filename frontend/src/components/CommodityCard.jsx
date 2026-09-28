import React from 'react';
import MiniSparkline from './MiniSparkline';
import CommodityIcon from './media/CommodityIcon';

/**
 * Converts English digits to Bengali numerals if language is 'bn'.
 */
export function toBengaliNumeral(num, lang = 'bn') {
  if (num === null || num === undefined || isNaN(num)) return '--';
  const str = typeof num === 'number' ? (Number.isInteger(num) ? String(num) : num.toFixed(1)) : String(num);
  if (lang !== 'bn') return str;
  const bnDigits = { '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯' };
  return str.replace(/[0-9]/g, (d) => bnDigits[d] || d);
}

/**
 * Human-friendly, non-academic trend badge.
 */
export function getTrendBadge(pctChange, lang = 'bn') {
  const pct = Number(pctChange) || 0;
  const absVal = Math.abs(pct).toFixed(1);
  const formattedPct = toBengaliNumeral(absVal, lang);

  if (pct >= 0.5) {
    return {
      label: lang === 'bn' ? `↑ ${formattedPct}% বেড়েছে` : `↑ ${absVal}% up`,
      className: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
    };
  }
  if (pct <= -0.5) {
    return {
      label: lang === 'bn' ? `↓ ${formattedPct}% কমেছে` : `↓ ${absVal}% down`,
      className: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
    };
  }
  return {
    label: lang === 'bn' ? 'স্থির' : 'Stable',
    className: 'bg-slate-800 text-slate-300 border border-slate-700/80',
  };
}

export default function CommodityCard({
  item,
  onClick,
  isHero = false,
  lang = 'bn',
}) {
  if (!item) return null;

  const avgPrice = item.price_summary?.avg_price || item.avg_price || 0.0;
  const wholesale = item.wholesale_avg || item.channels?.wholesale_avg;
  const retail = item.retail_avg || item.channels?.retail_avg || avgPrice;
  const online = item.online_avg || item.channels?.online_avg;

  const pctChange = item.percentage_change_7d !== undefined ? item.percentage_change_7d : 0.0;
  const trend = getTrendBadge(pctChange, lang);

  const sparklineData = item.sparkline_7d && item.sparkline_7d.length > 0
    ? item.sparkline_7d
    : [avgPrice * 0.98, avgPrice * 0.99, avgPrice, avgPrice * 1.01, avgPrice];

  // Detect cheapest channel
  const channels = [
    { id: 'ws', name: lang === 'bn' ? 'পাইকারি' : 'Wholesale', price: wholesale },
    { id: 'ret', name: lang === 'bn' ? 'খুচরা' : 'Retail', price: retail },
    { id: 'on', name: lang === 'bn' ? 'অনলাইন' : 'Online', price: online },
  ].filter((c) => c.price != null && c.price > 0);

  const minPrice = channels.length > 0 ? Math.min(...channels.map((c) => c.price)) : null;

  // ── HERO CARD VARIANT ──────────────────────────────────────────────────────
  if (isHero) {
    return (
      <div
        onClick={onClick}
        className="col-span-full p-5 sm:p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-rose-950/20 to-slate-900 border border-rose-500/40 hover:border-rose-500 shadow-xl shadow-rose-950/20 cursor-pointer transition-all duration-300 group relative overflow-hidden"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="flex items-start gap-4">
            <CommodityIcon
              category={item.category}
              name={item.canonical_name}
              className="w-12 h-12 flex-shrink-0 mt-1"
            />
            <div>
              <div className="flex items-center gap-2.5 mb-1.5 flex-wrap">
                <span className="px-2.5 py-0.5 text-xs font-bold bg-rose-500 text-white rounded-md flex items-center gap-1 shadow-sm">
                  <span>🔥</span>
                  <span>{lang === 'bn' ? 'আজকের শীর্ষ উঠানামা' : 'Top Market Mover'}</span>
                </span>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-md ${trend.className}`}>
                  {trend.label}
                </span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-extrabold text-white font-outfit tracking-tight group-hover:text-rose-400 transition-colors">
                {lang === 'bn' ? (item.bangla_name || item.canonical_name) : item.canonical_name}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {lang === 'bn' ? item.canonical_name : (item.bangla_name || '')}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-6">
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl sm:text-3xl font-extrabold text-white font-mono">
                  ৳ {toBengaliNumeral(avgPrice > 0 ? (Number.isInteger(avgPrice) ? avgPrice : avgPrice.toFixed(1)) : '--', lang)}
                </span>
                <span className="text-xs text-slate-400 font-medium">
                  / {item.unit || 'কেজি'}
                </span>
              </div>

              {/* 3-Channel Strip */}
              <div className="mt-2 flex items-center gap-1.5 text-xs font-mono text-slate-300 bg-slate-800/80 border border-slate-700/60 rounded-lg px-2.5 py-1">
                {channels.map((ch, idx) => {
                  const isCheapest = ch.price === minPrice;
                  return (
                    <React.Fragment key={ch.id}>
                      <span className={isCheapest ? 'text-emerald-400 font-bold' : 'text-slate-300'}>
                        {ch.name}: ৳{toBengaliNumeral(Math.round(ch.price), lang)}
                      </span>
                      {idx < channels.length - 1 && <span className="text-slate-600">|</span>}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>

            <button className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md transition-all flex items-center justify-center gap-1 whitespace-nowrap">
              <span>{lang === 'bn' ? 'বিস্তারিত দেখুন →' : 'View Details →'}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── STANDARD CARD VARIANT ──────────────────────────────────────────────────
  return (
    <div
      onClick={onClick}
      className="p-4 rounded-2xl bg-slate-800/50 hover:bg-slate-800/80 border border-slate-700/70 hover:border-emerald-500/50 hover:shadow-lg transition-all duration-200 cursor-pointer group flex flex-col justify-between space-y-3"
    >
      {/* 1. Top Row: Icon + Name + Trend Badge */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <CommodityIcon
            category={item.category}
            name={item.canonical_name}
            className="w-8 h-8 flex-shrink-0"
          />
          <div className="min-w-0 flex-1">
            <h4 className="text-sm font-bold text-white group-hover:text-emerald-400 transition-colors leading-snug truncate">
              {lang === 'bn' ? (item.bangla_name || item.canonical_name) : item.canonical_name}
            </h4>
            <span className="text-[11px] text-slate-400 truncate block">
              {lang === 'bn' ? item.canonical_name : (item.bangla_name || '')}
            </span>
          </div>
        </div>

        <span className={`px-2 py-0.5 text-[11px] font-semibold rounded-md whitespace-nowrap ${trend.className}`}>
          {trend.label}
        </span>
      </div>

      {/* 2. Main Price Row */}
      <div className="flex items-baseline justify-between pt-1">
        <div className="flex items-baseline gap-1">
          <span className="text-xl font-bold text-white font-mono tracking-tight">
            ৳ {toBengaliNumeral(avgPrice > 0 ? (Number.isInteger(avgPrice) ? avgPrice : avgPrice.toFixed(1)) : '--', lang)}
          </span>
          <span className="text-xs text-slate-400">/{item.unit || 'কেজি'}</span>
        </div>

        <MiniSparkline
          data={sparklineData}
          percentageChange={pctChange}
          width={68}
          height={24}
        />
      </div>

      {/* 3. Simple 3-Channel Comparison Strip */}
      <div className="px-2.5 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] font-mono text-slate-300 flex items-center justify-between">
        {channels.map((ch, idx) => {
          const isCheapest = ch.price === minPrice;
          return (
            <React.Fragment key={ch.id}>
              <span className={isCheapest ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                {ch.name}: ৳{toBengaliNumeral(Math.round(ch.price), lang)}
              </span>
              {idx < channels.length - 1 && <span className="text-slate-700">|</span>}
            </React.Fragment>
          );
        })}
      </div>

      {/* 4. Single Clean Action Link */}
      <div className="pt-2 border-t border-slate-700/50 flex items-center justify-between">
        <span className="text-[11px] text-slate-500">
          {lang === 'bn' ? 'আজকের রেট' : 'Daily Rate'}
        </span>
        <span className="text-xs font-semibold text-emerald-400 group-hover:text-emerald-300 transition-colors flex items-center gap-0.5">
          <span>{lang === 'bn' ? 'বিস্তারিত দেখুন →' : 'View Details →'}</span>
        </span>
      </div>
    </div>
  );
}
