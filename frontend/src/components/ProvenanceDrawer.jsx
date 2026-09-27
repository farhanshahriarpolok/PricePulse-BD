import React from 'react';
import { X, ShieldCheck, Database, Calendar, Award, CheckCircle } from 'lucide-react';

export default function ProvenanceDrawer({ observation, onClose }) {
  if (!observation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-xl bg-slate-900 border border-slate-700 rounded-2xl p-6 shadow-2xl overflow-hidden relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Title */}
        <div className="flex items-center gap-3 mb-5">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white font-outfit">Atomic Observation Provenance</h3>
            <p className="text-xs text-slate-400">Verifiable audit record from SQLite WAL store</p>
          </div>
        </div>

        {/* Observation Specs */}
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Canonical Entity:</span>
              <span className="font-bold text-white text-sm">{observation.commodity_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Market Trading Node:</span>
              <span className="font-semibold text-slate-200">{observation.market_name} ({observation.market_type})</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Publisher Source:</span>
              <span className="font-semibold text-emerald-400">{observation.source_name}</span>
            </div>
          </div>

          {/* Transformation Matrix */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <span className="text-slate-400 text-[11px] block mb-1">Verbatim Scraped Payload</span>
              <div className="font-bold text-white text-sm">
                BDT {observation.raw_price} <span className="text-slate-400 font-normal">/{observation.raw_unit}</span>
              </div>
              <p className="text-[10px] text-slate-500 mt-1">Raw bulletin quotation</p>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/40 border border-emerald-500/30">
              <span className="text-emerald-400 text-[11px] block mb-1">Standardized SI Price</span>
              <div className="font-bold text-white text-sm">
                BDT {observation.normalized_price} <span className="text-emerald-400 font-normal">/{observation.normalized_unit}</span>
              </div>
              <p className="text-[10px] text-emerald-500/80 mt-1">SI conversion applied</p>
            </div>
          </div>

          {/* Confidence Score Breakdown */}
          <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/60">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Award className="w-4 h-4 text-amber-400" />
                Composite Confidence Weight
              </span>
              <span className="font-mono font-bold text-sm text-emerald-400">
                {(observation.confidence_score * 100).toFixed(1)}% ({observation.confidence_score.toFixed(4)})
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2 mb-3">
              <div
                className="bg-gradient-to-r from-teal-500 to-emerald-400 h-2 rounded-full"
                style={{ width: `${observation.confidence_score * 100}%` }}
              ></div>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal">
              Linear confidence model: 40% Source Authority + 30% Alias Precision + 15% Freshness + 15% Completeness.
            </p>
          </div>

          {/* Audit Timestamps */}
          <div className="flex justify-between items-center text-[11px] text-slate-500 pt-2 border-t border-slate-800">
            <span>Observed Date: {observation.observation_date}</span>
            <span>Harvested At: {observation.scraped_at}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
