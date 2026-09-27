import React from 'react';
import { Layers, Store, ShoppingBag, Globe, ArrowRight } from 'lucide-react';

export default function ChannelComparisonCard({ channels, unit = 'kg', priceStatus = 'Normal' }) {
  if (!channels) return null;

  const { wholesale_avg, retail_avg, online_avg, spread_bdt, markup_percentage } = channels;

  const tiers = [
    {
      title: 'Wholesale Hub',
      sub: 'Karwan Bazar / Khatunganj',
      price: wholesale_avg,
      icon: Store,
      badge: 'B2B Bulletin',
      color: 'text-sky-400',
      bgColor: 'bg-sky-500/10',
      border: 'border-sky-500/30',
    },
    {
      title: 'Physical Retail',
      sub: 'Local Wet Markets',
      price: retail_avg,
      icon: ShoppingBag,
      badge: 'Consumer Wet Market',
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
    },
    {
      title: 'Online Quick-Commerce',
      sub: 'Chaldal / E-Commerce',
      price: online_avg,
      icon: Globe,
      badge: 'Packaged Delivery',
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
      border: 'border-purple-500/30',
    },
  ];

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white font-outfit">Supply Chain Channel Dispersion</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Market Margin Status:</span>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
            priceStatus === 'High' 
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
              : priceStatus === 'Elevated'
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
          }`}>
            {priceStatus}
          </span>
        </div>
      </div>

      {/* 3 Channel Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {tiers.map((tier, idx) => {
          const Icon = tier.icon;
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl bg-slate-900/60 border ${tier.border} relative overflow-hidden`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{tier.title}</span>
                <div className={`p-1.5 rounded-md ${tier.bgColor} ${tier.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="text-xl font-bold font-outfit text-white">
                {tier.price ? `BDT ${tier.price.toFixed(2)}` : 'N/A'}
                <span className="text-xs font-normal text-slate-400"> /{unit}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">{tier.sub}</p>
            </div>
          );
        })}
      </div>

      {/* Spread Metric Strip */}
      {spread_bdt !== null && (
        <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300">
            <span className="text-slate-400">Inter-Channel Gap:</span>
            <span className="font-semibold text-white">BDT {spread_bdt.toFixed(2)}/{unit}</span>
            <span className="text-slate-500">•</span>
            <span>Markup: <strong className="text-amber-400">+{markup_percentage}%</strong></span>
          </div>
          <div className="text-[11px] text-slate-400">
            Comparing primary wholesale auction vs weighted retail retail/delivery
          </div>
        </div>
      )}
    </div>
  );
}
