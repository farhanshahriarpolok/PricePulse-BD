import React, { useState, useEffect } from 'react';
import { Search, Loader2, Sparkles, AlertCircle, ArrowRight } from 'lucide-react';
import { searchRealtime } from '../api/endpoints';

export default function RealtimeSearch({ onSelectCommodity }) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Quick preset search tags
  const presets = [
    { label: 'Onion (দেশি পেঁয়াজ)', query: 'onion' },
    { label: 'Potato (ডায়মন্ড আলু)', query: 'potato' },
    { label: 'Miniket Rice (মিনিকেট চাল)', query: 'miniket' },
    { label: 'Soybean Oil (সয়াবিন তেল)', query: 'soybean' },
  ];

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 450);
    return () => clearTimeout(handler);
  }, [query]);

  useEffect(() => {
    if (!debouncedQuery) {
      setResult(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    searchRealtime(debouncedQuery)
      .then((data) => {
        if (isMounted) setResult(data);
      })
      .catch((err) => {
        if (isMounted) {
          setResult(null);
          setError(err.message || 'No matching commodity found in taxonomy');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [debouncedQuery]);

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-5 mb-6 shadow-xl backdrop-blur-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-bold text-white font-outfit flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            Realtime Commodity Price Discovery
          </h2>
          <p className="text-xs text-slate-400">
            Search in English or Bengali script (e.g., "পেঁয়াজ", "Miniket", "Alu"). Missing data triggers automatic on-demand harvest.
          </p>
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap gap-1.5">
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(p.query)}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-700/60 hover:bg-slate-700 text-slate-300 border border-slate-600/50 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input Box */}
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search staple commodity (e.g., deshi peyaj, diamond potato, চাল)..."
          className="w-full bg-slate-900/90 text-white placeholder-slate-500 pl-11 pr-12 py-3 rounded-xl border border-slate-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm font-medium transition"
        />
        <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
        {loading && <Loader2 className="w-5 h-5 text-emerald-400 animate-spin absolute right-3.5 top-3.5" />}
      </div>

      {/* Error state */}
      {error && (
        <div className="mt-3 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Card */}
      {result && (
        <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-emerald-500/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-white">{result.canonical_name}</span>
              <span className="text-sm font-medium text-emerald-400">({result.bangla_name})</span>
              <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {result.category}
              </span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded uppercase tracking-wide ${
                result.freshness.status === 'realtime_ingested' 
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}>
                {result.freshness.status === 'realtime_ingested' ? 'Live Ingested' : 'Cached Fresh'}
              </span>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-300">
              <div>
                <span className="text-slate-500">Benchmark Avg: </span>
                <span className="font-bold text-white font-outfit text-sm">
                  BDT {result.price_summary.avg_price.toFixed(2)}
                </span>
                <span className="text-slate-400">/{result.unit}</span>
              </div>
              <div>
                <span className="text-slate-500">Market Range: </span>
                <span className="text-slate-200">
                  BDT {result.price_summary.min_price} – {result.price_summary.max_price}
                </span>
              </div>
              {result.channels.markup_percentage && (
                <div>
                  <span className="text-slate-500">Retail Markup: </span>
                  <span className="font-semibold text-amber-400">+{result.channels.markup_percentage}%</span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => onSelectCommodity && onSelectCommodity(result)}
            className="w-full md:w-auto px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-emerald-900/40"
          >
            <span>Explore Trends & Spreads</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
