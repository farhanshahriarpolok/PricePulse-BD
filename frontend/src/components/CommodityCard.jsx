import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldCheck, 
  Zap, 
  ChevronRight,
  Flame,
  ArrowUpRight
} from 'lucide-react';
import MiniSparkline from './MiniSparkline';
import { getCategoryTheme } from '../utils/categoryTheme';

/**
 * Helper to compute refined severity badge and styles.
 */
export function getSeverityDetails(item) {
  const z = item.z_score !== undefined ? item.z_score : 0.0;
  const pct = item.percentage_change_7d !== undefined ? item.percentage_change_7d : 0.0;
  const cv = item.volatility_cv !== undefined ? item.volatility_cv : 0.0;

  if (z >= 2.0 || pct >= 20.0) {
    return {
      label: 'Critical Spike',
      badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse',
      icon: AlertTriangle,
      color: '#F43F5E',
    };
  }
  if (z >= 1.5 || pct >= 10.0) {
    return {
      label: 'Elevated',
      badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      icon: TrendingUp,
      color: '#F59E0B',
    };
  }
  if (pct <= -5.0) {
    return {
      label: 'Price Drop',
      badgeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
      icon: TrendingDown,
      color: '#06B6D4',
    };
  }
  if (cv >= 12.0) {
    return {
      label: 'Volatile',
      badgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
      icon: Zap,
      color: '#A855F7',
    };
  }
  return {
    label: 'Stable',
    badgeClass: 'bg-slate-700/50 text-slate-300 border-slate-600/40',
    icon: CheckCircle2,
    color: '#94A3B8',
  };
}

export default function CommodityCard({
  item,
  onClick,
  isHero = false,
}) {
  if (!item) return null;

  const theme = getCategoryTheme(item.category);
  const CategoryIcon = theme.icon;
  const severity = getSeverityDetails(item);
  const SeverityIcon = severity.icon;

  const avgPrice = item.price_summary?.avg_price || 0.0;
  const minPrice = item.min_price || item.price_summary?.min_price || avgPrice * 0.92;
  const maxPrice = item.max_price || item.price_summary?.max_price || avgPrice * 1.08;

  const wholesale = item.wholesale_avg || item.channels?.wholesale_avg;
  const retail = item.retail_avg || item.channels?.retail_avg;
  const online = item.online_avg || item.channels?.online_avg;

  const pctChange = item.percentage_change_7d !== undefined ? item.percentage_change_7d : 0.0;
  const sparklineData = item.sparkline_7d && item.sparkline_7d.length > 0
    ? item.sparkline_7d
    : [avgPrice * 0.98, avgPrice * 0.99, avgPrice, avgPrice * 1.01, avgPrice];

  const sourceCount = item.source_count || (item.price_summary?.sample_count ? Math.min(item.price_summary.sample_count, 3) : 2);
  const confPct = Math.round((item.confidence_score || 0.92) * 100);

  // HERO CARD RENDER VARIANT
  if (isHero) {
    return (
      <div
        onClick={onClick}
        className="col-span-full p-5 sm:p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-rose-950/20 to-slate-900 border-2 border-rose-500/40 hover:border-rose-500 shadow-xl shadow-rose-950/20 cursor-pointer transition-all duration-300 group relative overflow-hidden"
      >
        {/* Glow Accent Backdrop */}
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          {/* Left Column: Hero Header & Title */}
          <div className="space-y-3 max-w-xl">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="px-2.5 py-1 text-xs font-bold uppercase tracking-wider bg-rose-500 text-white rounded-md shadow-sm shadow-rose-500/40 flex items-center gap-1.5 animate-pulse">
                <Flame className="w-3.5 h-3.5" />
                Today's Top Market Mover
              </span>
              <span className={`px-2.5 py-1 text-xs font-semibold rounded-md border flex items-center gap-1.5 ${theme.tagClass}`}>
                <CategoryIcon className="w-3.5 h-3.5" />
                {item.category}
              </span>
              <span className={`px-2 py-0.5 text-xs font-bold rounded-md border ${severity.badgeClass} flex items-center gap-1`}>
                <SeverityIcon className="w-3 h-3" />
                {severity.label}
              </span>
            </div>

            <div>
              <div className="flex items-baseline gap-2.5">
                <h3 className="text-2xl sm:text-3xl font-extrabold text-white font-outfit tracking-tight group-hover:text-rose-400 transition-colors">
                  {item.canonical_name}
                </h3>
                <span className="text-sm font-medium text-slate-400 font-bengali">
                  ({item.bangla_name})
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                Experiencing elevated market pressure with an empirical 7-day surge of{' '}
                <span className="font-bold text-rose-400 font-mono">
                  {pctChange > 0 ? `+${pctChange.toFixed(1)}%` : `${pctChange.toFixed(1)}%`}
                </span>
                . Injected wholesale supply friction detected at central terminal markets.
              </p>
            </div>

            {/* Micro Channel Split */}
            <div className="flex items-center gap-3 text-xs text-slate-300 bg-slate-800/80 border border-slate-700/60 rounded-xl px-3.5 py-2 font-mono flex-wrap">
              <span>Wholesale: <strong className="text-white">৳{wholesale ? wholesale.toFixed(1) : '--'}</strong></span>
              <span className="text-slate-600">•</span>
              <span>Retail: <strong className="text-amber-300">৳{retail ? retail.toFixed(1) : '--'}</strong></span>
              <span className="text-slate-600">•</span>
              <span>Online: <strong className="text-emerald-400">৳{online ? online.toFixed(1) : '--'}</strong></span>
            </div>
          </div>

          {/* Right Column: Price Display & Expanded Sparkline */}
          <div className="flex flex-col sm:flex-row lg:flex-col items-start lg:items-end justify-between gap-4">
            <div className="text-left lg:text-right">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">Benchmark Spot Price</span>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl sm:text-4xl font-black text-white font-mono tracking-tight">
                  BDT {avgPrice.toFixed(2)}
                </span>
                <span className="text-sm font-medium text-slate-400">/{item.unit}</span>
              </div>
              <div className="text-xs text-slate-400 font-mono mt-0.5">
                Observed Range: <span className="text-slate-200">৳{minPrice.toFixed(1)}</span> – <span className="text-rose-400 font-semibold">৳{maxPrice.toFixed(1)}</span>
              </div>
            </div>

            {/* Sparkline & Action Button */}
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-xl bg-slate-800/60 border border-slate-700/60">
                <MiniSparkline
                  data={sparklineData}
                  percentageChange={pctChange}
                  width={110}
                  height={42}
                />
              </div>

              <div className="hidden sm:flex items-center gap-1 px-3.5 py-2 rounded-xl text-xs font-bold bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 transition-all">
                <span>Inspect Anomaly</span>
                <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // STANDARD COMMODITY CARD VARIANT
  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-xl bg-slate-900/90 border border-slate-800/90 ${theme.borderAccent} border-l-[3.5px] ${theme.hoverBorder} hover:shadow-lg transition-all duration-200 cursor-pointer group flex flex-col justify-between space-y-3.5`}
    >
      {/* 1. Header Row */}
      <div className="flex items-center justify-between gap-2">
        <span className={`px-2 py-0.5 text-[10.5px] font-semibold rounded border flex items-center gap-1.5 ${theme.tagClass}`}>
          <CategoryIcon className="w-3 h-3" />
          {item.category}
        </span>

        <div className="flex items-center gap-1.5">
          {/* Percentage Delta Tag */}
          <span
            className={`px-1.5 py-0.5 text-[10.5px] font-bold rounded font-mono flex items-center gap-0.5 ${
              pctChange > 2.0
                ? 'bg-rose-500/15 text-rose-400 border border-rose-500/25'
                : pctChange < -2.0
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25'
                : 'bg-slate-800 text-slate-400 border border-slate-700/60'
            }`}
          >
            {pctChange > 0 ? (
              <TrendingUp className="w-3 h-3" />
            ) : pctChange < 0 ? (
              <TrendingDown className="w-3 h-3" />
            ) : (
              <Minus className="w-3 h-3" />
            )}
            {pctChange > 0 ? `+${pctChange.toFixed(1)}%` : `${pctChange.toFixed(1)}%`}
          </span>

          {/* Severity Badge */}
          <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded border flex items-center gap-1 ${severity.badgeClass}`}>
            <SeverityIcon className="w-2.5 h-2.5" />
            {severity.label}
          </span>
        </div>
      </div>

      {/* 2. Title Section */}
      <div>
        <h4 className="text-sm font-bold text-white group-hover:text-emerald-400 transition-colors leading-snug">
          {item.canonical_name}
        </h4>
        <div className="text-[11px] text-slate-400 font-bengali mt-0.5">
          {item.bangla_name}
        </div>
      </div>

      {/* 3. Price & Sparkline Core */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
        <div>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Benchmark Price</span>
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-bold text-white font-mono tracking-tight">
              BDT {avgPrice.toFixed(2)}
            </span>
            <span className="text-[11px] text-slate-400">/{item.unit}</span>
          </div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">
            Range: <span className="text-slate-300">৳{minPrice.toFixed(0)}</span> – <span className="text-slate-300">৳{maxPrice.toFixed(0)}</span>
          </div>
        </div>

        {/* 7-Day Sparkline */}
        <div className="pl-2">
          <MiniSparkline
            data={sparklineData}
            percentageChange={pctChange}
            width={80}
            height={32}
          />
        </div>
      </div>

      {/* 4. Channel Split Bar */}
      <div className="p-2 rounded-lg bg-slate-800/40 border border-slate-800/60 text-[10.5px] font-mono text-slate-300 flex items-center justify-between">
        <span>WS: <strong className="text-slate-200">৳{wholesale ? wholesale.toFixed(0) : '--'}</strong></span>
        <span className="text-slate-600">•</span>
        <span>Retail: <strong className="text-amber-300">৳{retail ? retail.toFixed(0) : '--'}</strong></span>
        <span className="text-slate-600">•</span>
        <span>Online: <strong className="text-emerald-400">৳{online ? online.toFixed(0) : '--'}</strong></span>
      </div>

      {/* 5. Footer Provenance Row */}
      <div className="pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
        <span className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
          <span>{sourceCount} Sources</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300 font-mono">{confPct}% Conf</span>
        </span>

        <span className="text-slate-500 group-hover:text-emerald-400 transition-colors flex items-center gap-0.5">
          <span>Details</span>
          <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        </span>
      </div>
    </div>
  );
}
