/**
 * SpatialOpportunityPanel.jsx
 * Phase 2B — Consumer-first hybrid spatial intelligence panel.
 *
 * Architectural decisions implemented:
 *   Q1: Hybrid — consumer-first default, expandable research/detail layer.
 *   Q2: Standardized unit — all prices shown per canonical unit (kg/liter/pc).
 *   Q3: Backend returns all routes; frontend highlights positive opportunities,
 *       handles negative/zero with a human-readable equilibrium notice.
 *   Q4: No forecasting/ML — deterministic backend values only.
 *
 * NEVER hardcode price values — all numbers come from the backend response.
 */

import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Truck,
  TrendingDown,
  TrendingUp,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
  Info,
  Clock,
  Navigation,
  ShieldCheck,
  ArrowRight,
  BarChart2,
} from 'lucide-react';
import { getConsumerOpportunity } from '../api/endpoints';

// ── Provenance badge ──────────────────────────────────────────────────────────
function ProvenanceBadge({ provenance }) {
  const cfg = {
    LIVE:        { cls: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300', label: 'Live' },
    FALLBACK:    { cls: 'bg-amber-100  text-amber-800  dark:bg-amber-900/40  dark:text-amber-300',  label: 'Fallback' },
    MODELED:     { cls: 'bg-blue-100   text-blue-800   dark:bg-blue-900/40   dark:text-blue-300',   label: 'Modeled' },
    STALE:       { cls: 'bg-rose-100   text-rose-800   dark:bg-rose-900/40   dark:text-rose-300',   label: 'Stale' },
    UNAVAILABLE: { cls: 'bg-slate-100  text-slate-700  dark:bg-slate-800     dark:text-slate-300',  label: 'Unavailable' },
  };
  const { cls, label } = cfg[provenance] || cfg.FALLBACK;
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${cls}`}>
      <ShieldCheck className="w-2.5 h-2.5" />
      {label}
    </span>
  );
}

// ── Feasibility badge ─────────────────────────────────────────────────────────
function FeasibilityBadge({ feasibility }) {
  if (!feasibility) return null;
  const isHighly  = feasibility === 'Highly Feasible';
  const isMarginal = feasibility === 'Marginal';
  const cls = isHighly
    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
    : isMarginal
    ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${cls}`}>
      {feasibility}
    </span>
  );
}

// ── Price display helper ──────────────────────────────────────────────────────
function PriceDisplay({ price, unit, label, isSource }) {
  if (price == null) return null;
  return (
    <div className={`rounded-xl p-3 border ${isSource
      ? 'bg-emerald-50 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800'
      : 'bg-rose-50 border-rose-200 dark:bg-rose-950/30 dark:border-rose-800'
    }`}>
      <p className={`text-[10px] font-semibold uppercase tracking-wide mb-0.5 ${
        isSource ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
      }`}>{label}</p>
      <p className={`text-xl font-black font-mono ${
        isSource ? 'text-emerald-800 dark:text-emerald-200' : 'text-rose-800 dark:text-rose-200'
      }`}>
        ৳{price.toFixed(0)}
        <span className={`text-xs font-semibold ml-1 ${
          isSource ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
        }`}>/{unit}</span>
      </p>
    </div>
  );
}

// ── Research / Detail expandable layer ───────────────────────────────────────
function ResearchLayer({ opp, lang }) {
  const fd = opp.freight_detail;
  const topRoutes = opp.top_routes || [];
  return (
    <div className="space-y-4 pt-3 border-t border-slate-200 dark:border-slate-700">
      {/* Formula */}
      {fd && (
        <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-4">
          <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5 text-indigo-500" />
            {lang === 'bn' ? 'পরিবহন খরচ বিশ্লেষণ' : 'Freight Cost Breakdown'}
          </h5>
          <table className="w-full text-xs">
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              <tr>
                <td className="py-1.5 text-slate-500 dark:text-slate-400">
                  {lang === 'bn' ? 'বেস লোডিং ওভারহেড' : 'Base loading overhead'}
                </td>
                <td className="py-1.5 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                  ৳{fd.base_loading_bdt.toFixed(2)}/{opp.calculation_unit}
                </td>
              </tr>
              <tr>
                <td className="py-1.5 text-slate-500 dark:text-slate-400">
                  {lang === 'bn'
                    ? `দূরত্ব খরচ (${fd.distance_km} কিমি × ০.০১৮)`
                    : `Distance cost (${fd.distance_km} km × 0.018)`}
                </td>
                <td className="py-1.5 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                  ৳{fd.distance_cost_bdt.toFixed(2)}/{opp.calculation_unit}
                </td>
              </tr>
              <tr>
                <td className="py-1.5 text-slate-500 dark:text-slate-400">
                  {lang === 'bn' ? 'সেতু/টোল বাফার' : 'Bridge/toll buffer'}
                </td>
                <td className="py-1.5 text-right font-mono font-semibold text-slate-700 dark:text-slate-300">
                  ৳{fd.toll_and_bridge_bdt.toFixed(2)}/{opp.calculation_unit}
                </td>
              </tr>
              <tr className="border-t-2 border-slate-300 dark:border-slate-600">
                <td className="py-2 font-bold text-slate-700 dark:text-slate-300">
                  {lang === 'bn' ? 'মোট পরিবহন খরচ' : 'Total freight cost'}
                </td>
                <td className="py-2 text-right font-mono font-black text-slate-900 dark:text-white">
                  ৳{fd.total_freight_bdt.toFixed(2)}/{opp.calculation_unit}
                </td>
              </tr>
            </tbody>
          </table>
          <div className="mt-3 flex flex-wrap gap-3 text-[10px] text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {fd.transit_hours ? `${fd.transit_hours}h transit` : '—'}
            </span>
            <span className="flex items-center gap-1">
              <Navigation className="w-3 h-3" />
              {fd.distance_km} km road-corrected
            </span>
            {fd.corridor_name && (
              <span className="flex items-center gap-1">
                <Truck className="w-3 h-3" />
                <span className="truncate max-w-[160px]">{fd.corridor_name}</span>
              </span>
            )}
          </div>
          <p className="mt-2 text-[10px] text-slate-400 dark:text-slate-500 font-mono">
            Formula: {fd.calculation_basis}
          </p>
        </div>
      )}

      {/* Statistical metrics */}
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-3">
          <p className="text-[10px] text-slate-500 dark:text-slate-400 mb-0.5">
            {lang === 'bn' ? 'স্থানিক বিচ্ছুরণ সূচক D(t)' : 'Spatial Dispersion Index D(t)'}
          </p>
          <p className="text-lg font-black font-mono text-slate-800 dark:text-white">
            {opp.spatial_dispersion_index != null ? opp.spatial_dispersion_index.toFixed(4) : '—'}
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
            σ / μ across all market prices
          </p>
        </div>
        <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-3">
          <p className="text-[10px] text-slate-500 dark:text-slate-400 mb-0.5">
            {lang === 'bn' ? 'মূল্যায়িত করিডোর' : 'Corridors Evaluated'}
          </p>
          <p className="text-lg font-black font-mono text-slate-800 dark:text-white">
            {opp.all_routes_count}
          </p>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
            prod hub × cons hub pairs
          </p>
        </div>
      </div>

      {/* Top routes table */}
      {topRoutes.length > 0 && (
        <div className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div className="bg-slate-50 dark:bg-slate-800 px-4 py-2 border-b border-slate-200 dark:border-slate-700">
            <h5 className="text-xs font-bold text-slate-700 dark:text-slate-300">
              {lang === 'bn' ? 'শীর্ষ সুযোগ করিডোর' : 'Top Opportunity Corridors'}
            </h5>
          </div>
          <table className="w-full text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/80">
              <tr className="text-[10px] text-slate-500 dark:text-slate-400">
                <th className="px-3 py-2 text-left font-semibold">Route</th>
                <th className="px-3 py-2 text-right font-semibold">Gross</th>
                <th className="px-3 py-2 text-right font-semibold">Freight</th>
                <th className="px-3 py-2 text-right font-semibold">Net</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {topRoutes.map((route, idx) => (
                <tr key={idx} className={idx === 0
                  ? 'bg-emerald-50/60 dark:bg-emerald-950/20'
                  : 'bg-white dark:bg-transparent hover:bg-slate-50 dark:hover:bg-slate-800/40'
                }>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-1 text-slate-700 dark:text-slate-300 font-medium">
                      <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                      <span className="truncate max-w-[120px]">
                        {route.source_district} → {route.destination_district}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                      {route.distance_km} km · {route.transit_hours_estimated}h
                    </div>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-600 dark:text-slate-400">
                    ৳{route.gross_spread_bdt.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-600 dark:text-slate-400">
                    ৳{route.estimated_freight_cost_bdt.toFixed(2)}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono font-bold ${
                    route.net_arbitrage_margin_bdt >= 6
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : route.net_arbitrage_margin_bdt >= 2
                      ? 'text-amber-600 dark:text-amber-400'
                      : 'text-rose-600 dark:text-rose-400'
                  }`}>
                    {route.net_arbitrage_margin_bdt >= 0 ? '+' : ''}
                    ৳{route.net_arbitrage_margin_bdt.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Data source */}
      <p className="text-[10px] text-slate-400 dark:text-slate-500 flex items-center gap-1">
        <Info className="w-3 h-3 shrink-0" />
        {lang === 'bn'
          ? 'মূল্য উৎস: DAM / পাইকারি আড়ত পর্যবেক্ষণ। পরিবহন মডেল: ০.০১৮ ৳/কেজি/কিমি + সেতু টোল।'
          : 'Prices: DAM / wholesale hub observations. Freight model: 0.018 BDT/kg/km + bridge toll.'}
      </p>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function SpatialOpportunityPanel({ commodityId, commodityName, lang = 'bn' }) {
  const [opp, setOpp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!commodityId) return;
    setLoading(true);
    setError(null);
    setOpp(null);
    setExpanded(false);

    getConsumerOpportunity(commodityId)
      .then((data) => setOpp(data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [commodityId]);

  // ── Loading ──
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 p-6 flex items-center gap-3">
        <div className="w-5 h-5 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin shrink-0" />
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {lang === 'bn' ? 'বাজারভিত্তিক সুযোগ বিশ্লেষণ হচ্ছে...' : 'Analysing spatial market opportunity…'}
        </span>
      </div>
    );
  }

  // ── Error ──
  if (error) {
    return (
      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 p-5 flex items-start gap-3">
        <AlertCircle className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <p className="text-xs text-slate-400 dark:text-slate-500">
          {lang === 'bn'
            ? 'স্থানিক বিশ্লেষণ লোড করতে ব্যর্থ হয়েছে।'
            : 'Failed to load spatial analysis. Backend may be unavailable.'}
        </p>
      </div>
    );
  }

  // ── No data yet ──
  if (!opp) return null;

  const unit = opp.calculation_unit;
  const hasOpp = opp.has_opportunity;
  const net = opp.net_opportunity_bdt;
  const gross = opp.gross_difference_bdt;
  const freight = opp.transport_cost_bdt;

  return (
    <div
      id="spatial-opportunity-panel"
      className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/40 shadow-sm overflow-hidden"
    >
      {/* ── Section header ── */}
      <div className="px-5 pt-4 pb-3 border-b border-slate-100 dark:border-slate-700/60 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
            hasOpp
              ? 'bg-emerald-100 dark:bg-emerald-900/40'
              : 'bg-slate-100 dark:bg-slate-800'
          }`}>
            <Truck className={`w-3.5 h-3.5 ${hasOpp ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}`} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-white">
              {lang === 'bn' ? 'বাজারভিত্তিক দামের সুযোগ' : 'Spatial Market Opportunity'}
            </h4>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">
              {lang === 'bn'
                ? 'উৎপাদন-বাজার থেকে ভোক্তা-বাজারে দামের ব্যবধান ও পরিবহন সমীক্ষা'
                : 'Production-hub to consumption-hub price spread & freight analysis'}
            </p>
          </div>
        </div>
        <ProvenanceBadge provenance={opp.data_provenance} />
      </div>

      <div className="px-5 py-4 space-y-4">

        {/* ── Consumer layer: Opportunity exists ── */}
        {hasOpp ? (
          <>
            {/* Where cheaper / price difference / net gain */}
            <div className="grid grid-cols-2 gap-2">
              <PriceDisplay
                price={opp.cheapest_price_bdt}
                unit={unit}
                label={lang === 'bn' ? `সস্তা: ${opp.cheapest_district}` : `Cheaper: ${opp.cheapest_district}`}
                isSource={true}
              />
              <PriceDisplay
                price={opp.expensive_price_bdt}
                unit={unit}
                label={lang === 'bn' ? `চাহিদা: ${opp.expensive_district}` : `Demand: ${opp.expensive_district}`}
                isSource={false}
              />
            </div>

            {/* Net opportunity callout */}
            <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span className="text-xs font-bold text-emerald-800 dark:text-emerald-200">
                      {lang === 'bn' ? 'নেট সুযোগ' : 'Net Opportunity'}
                    </span>
                    <FeasibilityBadge feasibility={opp.economic_feasibility} />
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-black font-mono text-emerald-700 dark:text-emerald-300">
                      +৳{net != null ? net.toFixed(2) : '—'}
                    </span>
                    <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                      /{unit}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1.5 text-[11px] text-emerald-600 dark:text-emerald-400">
                    {gross != null && (
                      <span>Gross ৳{gross.toFixed(2)}</span>
                    )}
                    {freight != null && (
                      <>
                        <ArrowRight className="w-3 h-3" />
                        <span>Freight ৳{freight.toFixed(2)}</span>
                      </>
                    )}
                    {opp.roi_percentage != null && (
                      <>
                        <ArrowRight className="w-3 h-3" />
                        <span>ROI {opp.roi_percentage.toFixed(1)}%</span>
                      </>
                    )}
                  </div>
                </div>
                <TrendingUp className="w-8 h-8 text-emerald-400 dark:text-emerald-600 shrink-0 mt-1" />
              </div>

              {/* Route summary */}
              {opp.cheapest_market && opp.expensive_market && (
                <div className="mt-3 pt-3 border-t border-emerald-200 dark:border-emerald-800/60 flex items-center gap-1.5 text-[11px] text-emerald-700 dark:text-emerald-300 flex-wrap">
                  <MapPin className="w-3 h-3 shrink-0" />
                  <span className="font-semibold">{opp.cheapest_market}</span>
                  <ArrowRight className="w-3 h-3" />
                  <span className="font-semibold">{opp.expensive_market}</span>
                </div>
              )}
            </div>
          </>
        ) : (
          /* ── Consumer layer: No opportunity / equilibrium ── */
          <div className="rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 p-4 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center shrink-0 mt-0.5">
              <TrendingDown className="w-4 h-4 text-slate-400" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                {lang === 'bn'
                  ? 'কোনো কার্যকর সুযোগ নেই — বাজার ভারসাম্যে আছে'
                  : 'No Viable Opportunity — Market in Equilibrium'}
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                {opp.opportunity_summary}
              </p>
              {net != null && gross != null && (
                <div className="mt-2 flex flex-wrap gap-3 text-[11px]">
                  <span className="text-slate-500 dark:text-slate-400">
                    {lang === 'bn' ? 'দামের ব্যবধান' : 'Price gap'}: ৳{gross.toFixed(2)}/{unit}
                  </span>
                  <span className="text-slate-500 dark:text-slate-400">
                    {lang === 'bn' ? 'পরিবহন' : 'Freight'}: ৳{freight != null ? freight.toFixed(2) : '—'}/{unit}
                  </span>
                  <span className={`font-semibold ${
                    net >= 0 ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'
                  }`}>
                    {lang === 'bn' ? 'নেট' : 'Net'}: {net >= 0 ? '+' : ''}৳{net.toFixed(2)}/{unit}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Expand / collapse research layer ── */}
        <button
          id="spatial-research-toggle"
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors text-xs text-slate-600 dark:text-slate-400 font-semibold"
        >
          <span className="flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-indigo-500" />
            {lang === 'bn'
              ? expanded ? 'বিস্তারিত গবেষণা তথ্য লুকান' : 'বিস্তারিত গবেষণা তথ্য দেখুন'
              : expanded ? 'Hide Research Details' : 'Show Research Details'}
          </span>
          {expanded
            ? <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
            : <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          }
        </button>

        {/* ── Research / detail layer ── */}
        {expanded && <ResearchLayer opp={opp} lang={lang} />}
      </div>
    </div>
  );
}
