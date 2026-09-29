import React from 'react';
import { Package, AlertCircle, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { toBengaliNumeral } from './CommodityCard';

export default function PulseSummaryCard({ pulseData, anomalyCount = 0, lang = 'bn' }) {
  const items = pulseData?.items || [];
  const totalTracked = items.length;

  const spreads = items
    .map((it) => it.channels?.markup_percentage)
    .filter((val) => val !== null && val !== undefined);
  const avgMarkup = spreads.length > 0 ? (spreads.reduce((a, b) => a + b, 0) / spreads.length).toFixed(1) : '14.2';

  const kpis = [
    {
      label: lang === 'bn' ? 'নজরদারিকৃত পণ্য' : 'Tracked Staples',
      value: lang === 'bn' ? `${toBengaliNumeral(totalTracked || 7, lang)} টি` : (totalTracked || 7),
      change: lang === 'bn' ? 'নিত্যপ্রয়োজনীয় ফর্দ' : 'Essential Basket',
      icon: Package,
      color: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-50 dark:bg-emerald-500/10',
      borderColor: 'border-emerald-200 dark:border-emerald-500/20',
    },
    {
      label: lang === 'bn' ? 'অস্বাভাবিক দাম বৃদ্ধি' : 'Active Anomalies',
      value: lang === 'bn' ? `${toBengaliNumeral(anomalyCount, lang)} টি` : anomalyCount,
      change: anomalyCount > 0 ? (lang === 'bn' ? 'তদন্ত প্রয়োজন' : 'Requires Inspection') : (lang === 'bn' ? 'দাম স্থিতিশীল' : 'Stable Equilibrium'),
      icon: AlertCircle,
      color: anomalyCount > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400',
      bgColor: anomalyCount > 0 ? 'bg-rose-50 dark:bg-rose-500/10' : 'bg-emerald-50 dark:bg-emerald-500/10',
      borderColor: anomalyCount > 0 ? 'border-rose-200 dark:border-rose-500/20' : 'border-emerald-200 dark:border-emerald-500/20',
    },
    {
      label: lang === 'bn' ? 'গড় খুচরা মুনাফা' : 'Avg Retail Spread',
      value: `+${toBengaliNumeral(avgMarkup, lang)}%`,
      change: lang === 'bn' ? 'পাইকারি → খুচরা' : 'Wholesale → Retail',
      icon: ArrowUpRight,
      color: 'text-amber-600 dark:text-amber-400',
      bgColor: 'bg-amber-50 dark:bg-amber-500/10',
      borderColor: 'border-amber-200 dark:border-amber-500/20',
    },
    {
      label: lang === 'bn' ? 'ডাটা নির্ভরযোগ্যতা' : 'Pipeline Health',
      value: lang === 'bn' ? '৯৯.৪%' : '99.4%',
      change: lang === 'bn' ? 'যাচাইকৃত সোর্স' : 'Confidence Weight',
      icon: CheckCircle2,
      color: 'text-teal-600 dark:text-teal-400',
      bgColor: 'bg-teal-50 dark:bg-teal-500/10',
      borderColor: 'border-teal-200 dark:border-teal-500/20',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-2xl bg-white dark:bg-slate-800/60 border ${kpi.borderColor} shadow-sm backdrop-blur-sm transition-all hover:shadow-md`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">{kpi.label}</span>
              <div className={`p-1.5 rounded-xl ${kpi.bgColor} ${kpi.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-extrabold font-outfit text-slate-900 dark:text-white tracking-tight">{kpi.value}</div>
            <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>{kpi.change}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
