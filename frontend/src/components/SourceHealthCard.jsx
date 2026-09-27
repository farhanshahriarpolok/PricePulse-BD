import React from 'react';
import { Server, Activity, ShieldCheck, AlertCircle, WifiOff, Clock, CheckCircle2, RefreshCw } from 'lucide-react';

export default function SourceHealthCard({ sources = [], onRefresh, isRefreshing = false }) {
  const getStatusBadge = (status, isFallback) => {
    if (status === 'HEALTHY' && !isFallback) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          HEALTHY (LIVE)
        </span>
      );
    }
    if (status === 'DEGRADED' || isFallback) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
          DEGRADED (FIXTURE FALLBACK)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
        <WifiOff className="w-3.5 h-3.5 text-rose-400" />
        OFFLINE
      </span>
    );
  };

  const formatTimestamp = (isoStr) => {
    if (!isoStr) return 'Pending First Sync';
    try {
      const dt = new Date(isoStr);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' (' + dt.toLocaleDateString() + ')';
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 shadow-sm mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-700/60 gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white font-outfit">Upstream Ingestion & Telemetry Monitor</h3>
            <p className="text-xs text-slate-400">
              Live network connectivity, response latency, and graceful offline fallback states for registered data providers.
            </p>
          </div>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700/70 border border-slate-700 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-teal-400' : ''}`} />
            <span>Check Telemetry</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sources.map((src) => {
          const isHealthy = src.status === 'HEALTHY' && !src.is_fallback;
          const isDegraded = src.status === 'DEGRADED' || src.is_fallback;
          const cardBorder = isHealthy
            ? 'border-emerald-500/30'
            : isDegraded
            ? 'border-amber-500/30'
            : 'border-rose-500/30';

          return (
            <div
              key={src.source_code}
              className={`p-4 rounded-xl bg-slate-900/60 border ${cardBorder} flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h4 className="text-sm font-bold text-white leading-tight">{src.source_name}</h4>
                </div>
                <div className="mb-3">{getStatusBadge(src.status, src.is_fallback)}</div>

                <div className="space-y-1.5 text-xs text-slate-300">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Activity className="w-3.5 h-3.5 text-slate-500" /> Latency:
                    </span>
                    <span className="font-mono font-semibold text-white">{src.latency_ms} ms</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" /> Last Sync:
                    </span>
                    <span className="font-mono text-slate-300">{formatTimestamp(src.last_sync)}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Success / Error:</span>
                    <span className="font-mono text-slate-300">
                      <span className="text-emerald-400">{src.success_count || 0}</span> /{' '}
                      <span className="text-rose-400">{src.error_count || 0}</span>
                    </span>
                  </div>
                </div>
              </div>

              {src.last_error && (
                <div className="mt-3 pt-2 border-t border-slate-800 text-[11px] text-amber-300/90 leading-tight">
                  <span className="font-medium text-amber-400">Notice: </span>
                  {src.last_error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
