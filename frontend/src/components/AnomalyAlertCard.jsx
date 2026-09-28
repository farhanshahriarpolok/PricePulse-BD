import React from 'react';
import { AlertTriangle, TrendingUp, Info, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function AnomalyAlertCard({ anomaly, onSelectCommodity }) {
  if (!anomaly) return null;

  const {
    canonical_name,
    bangla_name,
    unit,
    observation_date,
    anomaly_severity,
    anomaly_direction,
    metrics,
    explanation,
  } = anomaly;

  const isSpike = anomaly_direction === 'Spike';

  const severityColors = {
    Critical: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
    Severe: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
    Moderate: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    Normal: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 mb-4 shadow-lg backdrop-blur-md transition hover:border-slate-600">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl ${isSpike ? 'bg-rose-500/10 text-rose-400' : 'bg-sky-500/10 text-sky-400'}`}>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white font-outfit">{canonical_name}</h3>
              <span className="text-xs text-emerald-400 font-medium font-bengali">({bangla_name})</span>
            </div>
            <p className="text-xs text-slate-400">Target Date: {observation_date}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${severityColors[anomaly_severity] || severityColors.Moderate}`}>
            {anomaly_severity} {anomaly_direction || 'Shift'}
          </span>
          {onSelectCommodity && (
            <button
              onClick={onSelectCommodity}
              className="px-3 py-1 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-emerald-400 hover:text-emerald-300 text-xs font-semibold transition cursor-pointer"
            >
              Inspect History →
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/50">
          <span className="text-[11px] text-slate-400 block">Observed Price</span>
          <span className="text-base font-bold text-white font-outfit">
            BDT {metrics.current_price.toFixed(2)}
          </span>
          <span className="text-[10px] text-slate-400"> /{unit}</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/50">
          <span className="text-[11px] text-slate-400 block">14-Day SMA</span>
          <span className="text-base font-bold text-slate-200 font-outfit">
            BDT {metrics.baseline_sma_14d ? metrics.baseline_sma_14d.toFixed(2) : 'N/A'}
          </span>
          <span className="text-[10px] text-slate-400"> /{unit}</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/50">
          <span className="text-[11px] text-slate-400 block">Standard Score</span>
          <span className={`text-base font-bold font-outfit ${isSpike ? 'text-rose-400' : 'text-sky-400'}`}>
            Z = {metrics.z_score_14d !== null ? metrics.z_score_14d : '0.0'}
          </span>
          <span className="text-[10px] text-slate-400 block">σ = {metrics.std_dev_14d}</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/50">
          <span className="text-[11px] text-slate-400 block">Net Deviation</span>
          <span className={`text-base font-bold font-outfit flex items-center gap-0.5 ${isSpike ? 'text-rose-400' : 'text-sky-400'}`}>
            {isSpike ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            {metrics.percentage_change_14d > 0 ? `+${metrics.percentage_change_14d}%` : `${metrics.percentage_change_14d}%`}
          </span>
          <span className="text-[10px] text-slate-400 block">CV: {metrics.volatility_cv}%</span>
        </div>
      </div>

      {/* Natural Language Explanation Box */}
      <div className="p-3.5 rounded-xl bg-slate-900/90 border border-indigo-500/20 text-xs leading-relaxed text-slate-300 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-indigo-300 block mb-1">Algorithmic Anomaly Detection Analysis:</strong>
          <p>{explanation}</p>
        </div>
      </div>
    </div>
  );
}
