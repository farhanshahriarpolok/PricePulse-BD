/**
 * ForecastOutlookPanel.jsx
 * Phase 3 — 7-Day Price Forecast, Rolling Backtest Selection & Volatility-Aware Direction.
 *
 * Architecture:
 *   Q1: Hybrid forecasting (Baselines + ARIMA(1,1,0) + Rolling Backtesting + Model Selection).
 *   Q2: Channel-separated national aggregation (Wholesale, Retail, Online).
 *   Q3: Populated verified markets with channel labels; unpopulated markets handled gracefully.
 *   Q4: Volatility-aware directional threshold (±3% base deadband modulated by CV).
 *
 * NEVER hardcode price or forecast values — all numbers come directly from the backend API.
 */

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Layers,
  BarChart3,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Info,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { getCommodityForecast } from '../api/endpoints';

// ── Direction badge ─────────────────────────────────────────────────────────
function DirectionBadge({ direction, lang }) {
  if (direction === 'UP') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
        <TrendingUp className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400" />
        {lang === 'bn' ? 'সম্ভাব্য বৃদ্ধি' : 'Expected Rise'}
      </span>
    );
  }
  if (direction === 'DOWN') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
        <TrendingDown className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        {lang === 'bn' ? 'সম্ভাব্য হ্রাস' : 'Expected Drop'}
      </span>
    );
  }
  if (direction === 'STABLE') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
        <Minus className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
        {lang === 'bn' ? 'স্থিতিশীল' : 'Stable Outlook'}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
      <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
      {lang === 'bn' ? 'অপ্রতুল তথ্য' : 'Unavailable'}
    </span>
  );
}

// ── Research / Details Layer ────────────────────────────────────────────────
function ForecastResearchLayer({ data, lang }) {
  const fc = data.forecast_detail;
  const elig = data.data_eligibility;
  const dir = data.direction_signal;
  const metrics = data.backtest_metrics || [];

  return (
    <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-700">
      {/* 1. Candidate Models Backtest Evaluation */}
      {metrics.length > 0 && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="bg-slate-50 dark:bg-slate-800 px-4 py-2.5 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h5 className="text-xs font-bold text-slate-800 dark:text-white flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-indigo-500" />
              {lang === 'bn' ? 'মডেল যাচাইকরণ ও নির্বাচন (Backtest)' : 'Model Selection & Rolling Backtest'}
            </h5>
            <span className="text-[10px] font-mono text-slate-400">Walk-Forward MAE</span>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-[10px] text-slate-500 dark:text-slate-400">
              <tr>
                <th className="px-3 py-2 text-left font-semibold">Model</th>
                <th className="px-3 py-2 text-right font-semibold">Windows</th>
                <th className="px-3 py-2 text-right font-semibold">MAE (৳)</th>
                <th className="px-3 py-2 text-right font-semibold">RMSE (৳)</th>
                <th className="px-3 py-2 text-center font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {metrics.map((m, idx) => (
                <tr
                  key={idx}
                  className={
                    m.is_selected
                      ? 'bg-indigo-50/70 dark:bg-indigo-950/30 font-semibold'
                      : 'bg-white dark:bg-transparent'
                  }
                >
                  <td className="px-3 py-2 text-slate-700 dark:text-slate-300 font-mono">
                    {m.model_name}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-500 dark:text-slate-400">
                    {m.windows_evaluated}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-800 dark:text-slate-200">
                    ৳{m.mae_bdt.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-600 dark:text-slate-400">
                    ৳{m.rmse_bdt.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {m.is_selected ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-100 dark:bg-indigo-900/50 px-1.5 py-0.5 rounded">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        Selected
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400">Candidate</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 2. Statistical Volatility & Deadband Mechanics */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-3">
          <p className="text-[10px] text-slate-500 dark:text-slate-400 mb-0.5">
            {lang === 'bn' ? 'বাজারের অস্থিরতা (১৪-দিনের CV)' : 'Historical Volatility (14d CV)'}
          </p>
          <p className="text-base font-black font-mono text-slate-800 dark:text-white">
            {dir?.historical_cv_pct != null ? `${dir.historical_cv_pct.toFixed(1)}%` : '—'}
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
            {dir?.historical_cv_pct > 8 ? 'উচ্চ অস্থিরতা (High volatility)' : 'স্বাভাবিক অস্থিরতা (Normal)'}
          </p>
        </div>
        <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-3">
          <p className="text-[10px] text-slate-500 dark:text-slate-400 mb-0.5">
            {lang === 'bn' ? 'কার্যকর পরিবর্তন থ্রেশহোল্ড' : 'Effective Deadband Threshold'}
          </p>
          <p className="text-base font-black font-mono text-slate-800 dark:text-white">
            ±{dir?.effective_threshold_pct != null ? dir.effective_threshold_pct.toFixed(1) : 3.0}%
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
            Base ±3.0% + CV modulation
          </p>
        </div>
      </div>

      {/* 3. Daily 7-Day Forecast Schedule Table */}
      {fc?.daily_schedule && fc.daily_schedule.length > 0 && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="bg-slate-50 dark:bg-slate-800 px-4 py-2 border-b border-slate-200 dark:border-slate-700">
            <h5 className="text-xs font-bold text-slate-800 dark:text-white">
              {lang === 'bn' ? 'দৈনিক ৭-দিনের পূর্বাভাস তালিকা' : 'Daily 7-Day Projection Schedule'}
            </h5>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-[10px] text-slate-500 dark:text-slate-400">
              <tr>
                <th className="px-3 py-1.5 text-left font-semibold">Day</th>
                <th className="px-3 py-1.5 text-left font-semibold">Date</th>
                <th className="px-3 py-1.5 text-right font-semibold">Point Estimate</th>
                <th className="px-3 py-1.5 text-right font-semibold">
                  {lang === 'bn' ? 'অনিশ্চয়তা পরিধি (±1.96σ)' : 'Uncertainty Range (±1.96σ)'}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {fc.daily_schedule.map((pt) => (
                <tr key={pt.day_offset} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="px-3 py-1.5 font-bold text-slate-700 dark:text-slate-300">
                    Day +{pt.day_offset}
                  </td>
                  <td className="px-3 py-1.5 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                    {pt.target_date || '—'}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono font-bold text-slate-900 dark:text-white">
                    ৳{pt.predicted_price_bdt.toFixed(2)}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono text-[11px] text-slate-500 dark:text-slate-400">
                    ৳{pt.lower_bound_bdt.toFixed(2)} – ৳{pt.upper_bound_bdt.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 4. Data Provenance & Leakage Protection Notice */}
      <div className="text-[10px] text-slate-400 dark:text-slate-500 space-y-1">
        <p className="flex items-center gap-1">
          <Info className="w-3 h-3 shrink-0" />
          {lang === 'bn'
            ? `উপাত্ত পরিধি: ${elig.distinct_dates_count} দিন (${elig.date_start} থেকে ${elig.date_end})।`
            : `Training span: ${elig.distinct_dates_count} dates (${elig.date_start} to ${elig.date_end}).`}
          {elig.modeled_observations_excluded > 0 && (
            <span className="text-amber-600 dark:text-amber-400 font-medium ml-1">
              ({elig.modeled_observations_excluded} modeled Pandamart records strictly excluded)
            </span>
          )}
        </p>
        <p>
          Method: Chronological rolling-origin walk-forward validation (Zero future data leakage). Uncertainty range is an estimated parametric interval based on out-of-sample RMSE (σ_h = RMSE_OOS · √(1 + 0.10(h-1))).
        </p>
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────
export default function ForecastOutlookPanel({ commodityId, commodityName, lang = 'bn' }) {
  const [channel, setChannel] = useState('wholesale');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!commodityId) return;
    setLoading(true);
    setError(null);
    setData(null);

    getCommodityForecast(commodityId, channel)
      .then((res) => setData(res))
      .catch((err) => {
        if (err.response?.status === 404) {
          setData({ status: 'UNAVAILABLE' });
        } else {
          setError(true);
        }
      })
      .finally(() => setLoading(false));
  }, [commodityId, channel]);

  // Loading state
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 p-5 flex items-center gap-3">
        <div className="w-5 h-5 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin shrink-0" />
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {lang === 'bn' ? '৭-দিনের পূর্বাভাস মডেল তৈরি হচ্ছে...' : 'Computing 7-day price forecast outlook…'}
        </span>
      </div>
    );
  }

  // Network / server error
  if (error) {
    return (
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 p-4 flex items-center gap-2 text-xs text-slate-400">
        <AlertCircle className="w-4 h-4 text-slate-400 shrink-0" />
        {lang === 'bn' ? 'পূর্বাভাস লোড করা সম্ভব হয়নি।' : 'Unable to load forecast model.'}
      </div>
    );
  }

  if (!data) return null;

  const status = data.status;
  const fc = data.forecast_detail;
  const dir = data.direction_signal;
  const unit = data.calculation_unit || 'kg';

  return (
    <div
      id="forecast-outlook-panel"
      className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 shadow-sm overflow-hidden"
    >
      {/* ── Section Header ── */}
      <div className="px-5 pt-4 pb-3 border-b border-slate-100 dark:border-slate-700/60 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-white">
              {lang === 'bn' ? '৭-দিনের মূল্যের পূর্বাভাস' : '7-Day Price Forecast'}
            </h4>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">
              {lang === 'bn'
                ? 'ঐতিহাসিক সময়ক্রম ব্যাকটেস্টিং ও সম্ভাব্যতা বিশ্লেষণ'
                : 'Rolling walk-forward time-series backtesting & uncertainty interval'}
            </p>
          </div>
        </div>

        {/* Channel Selector */}
        <div className="inline-flex rounded-lg bg-slate-100 dark:bg-slate-800 p-0.5 text-xs">
          <button
            type="button"
            onClick={() => setChannel('wholesale')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
              channel === 'wholesale'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-800 dark:text-slate-400'
            }`}
          >
            {lang === 'bn' ? 'পাইকারি' : 'Wholesale'}
          </button>
          <button
            type="button"
            onClick={() => setChannel('retail')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
              channel === 'retail'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-800 dark:text-slate-400'
            }`}
          >
            {lang === 'bn' ? 'খুচরা' : 'Retail'}
          </button>
          <button
            type="button"
            onClick={() => setChannel('online')}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all ${
              channel === 'online'
                ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-800 dark:text-slate-400'
            }`}
          >
            {lang === 'bn' ? 'অনলাইন' : 'Online'}
          </button>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {status === 'FORECAST' && fc ? (
          <>
            {/* ── Consumer Tier: Primary Outlook Card ── */}
            <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {lang === 'bn' ? 'সম্ভাব্য গতিপথ:' : 'Expected Direction:'}
                    </span>
                    <DirectionBadge direction={dir?.direction} lang={lang} />
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 pt-0.5">
                    {dir?.direction_summary}
                  </p>
                </div>

                {/* Projected 7-day range callout */}
                <div className="sm:text-right bg-white dark:bg-slate-800 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 shadow-xs">
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wider font-semibold block">
                    {lang === 'bn' ? '৭-দিনের আনুমানিক পরিধি' : 'Estimated 7-Day Range'}
                  </span>
                  <div className="flex items-baseline gap-1 sm:justify-end mt-0.5">
                    <span className="text-xl font-black font-mono text-slate-900 dark:text-white">
                      ৳{fc.forecast_day7_lower_bdt.toFixed(0)} – ৳{fc.forecast_day7_upper_bdt.toFixed(0)}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      /{unit}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5 flex items-center gap-1 sm:justify-end">
                    <span>Point: ৳{fc.forecast_day7_bdt.toFixed(2)}</span>
                    <span>({dir?.recent_change_pct > 0 ? '+' : ''}{dir?.recent_change_pct.toFixed(1)}%)</span>
                  </div>
                </div>
              </div>

              {/* Consumer Disclaimers */}
              <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-700/60 flex items-center gap-1">
                <Info className="w-3 h-3 shrink-0" />
                {lang === 'bn'
                  ? 'পূর্বাভাস কোনো নিশ্চিত ভবিষ্যৎ মূল্য নয়; বাজার পর্যবেক্ষণ ও গাণিতিক ব্যাকটেস্টিং মডেল ভিত্তিক সম্ভাব্য প্রাক্কলন।'
                  : 'Analytical projection only. Not a guaranteed future transaction price.'}
              </p>
            </div>

            {/* ── Research Tier Toggle ── */}
            <button
              id="forecast-research-toggle"
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="w-full flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 py-1 transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-500" />
                {lang === 'bn'
                  ? (expanded ? 'গবেষণা ও মডেল নির্বাচন তথ্য লুকান' : 'মডেল নির্বাচন ও ব্যাকটেস্টিং বিবরণ দেখুন')
                  : (expanded ? 'Hide Research & Model Selection Data' : 'View Model Selection & Backtesting Details')}
              </span>
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {/* Expandable Research Content */}
            {expanded && <ForecastResearchLayer data={data} lang={lang} />}
          </>
        ) : (
          /* ── Insufficient Data / Unavailable State ── */
          <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-4 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h5 className="text-xs font-bold text-slate-800 dark:text-white">
                {lang === 'bn' ? 'পূর্বাভাস অপ্রতুল — পর্যাপ্ত উপাত্ত নেই' : 'Forecast Unavailable — Insufficient History'}
              </h5>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                {data.data_eligibility?.reason ||
                  (lang === 'bn'
                    ? 'এই পণ্যের জন্য প্রয়োজনীয় ১৪ দিনের ধারাবাহিক ঐতিহাসিক মূল্য পর্যবেক্ষণ এখনো বিদ্যমান নেই।'
                    : 'Minimum 14 days of consecutive historical observations required for rolling-origin forecast models.')}
              </p>
              {data.data_eligibility?.distinct_dates_count != null && (
                <div className="text-[10px] text-slate-400 mt-2 font-mono">
                  Recorded dates: {data.data_eligibility.distinct_dates_count} (Minimum required: 14)
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
