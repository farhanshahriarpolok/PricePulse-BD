import React, { useState, useEffect } from 'react';
import {
  TrendingDown,
  TrendingUp,
  Truck,
  Building2,
  Package,
  Layers,
  Info,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Scale
} from 'lucide-react';
import { getSupplyChainDeconstruction } from '../api/endpoints';
import { toBengaliNumeral } from './CommodityCard';
import { getTranslation } from '../i18n/translations';

export default function SupplyChainMarginPanel({ commodityId, commodityName, lang = 'bn', currentDistrictId = null }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAccordionOpen, setIsAccordionOpen] = useState(false);
  const [showMethodologyModal, setShowMethodologyModal] = useState(false);

  useEffect(() => {
    if (!commodityId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    const params = {};
    if (currentDistrictId) {
      params.district_id = currentDistrictId;
    }

    getSupplyChainDeconstruction(commodityId, params)
      .then((res) => {
        if (!isMounted) return;
        const payload = res?.data || res;
        setData(payload);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.warn('Supply chain data unavailable:', err);
        setError('UNAVAILABLE');
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [commodityId, currentDistrictId]);

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-xs animate-pulse">
        <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3 mb-3"></div>
        <div className="h-8 bg-slate-100 dark:bg-slate-800/60 rounded w-2/3 mb-4"></div>
        <div className="h-24 bg-slate-50 dark:bg-slate-800/40 rounded-xl"></div>
      </div>
    );
  }

  if (error || !data || data.wholesale_price === null || data.retail_price === null) {
    return null; // Gracefully hide when pricing pair is incomplete
  }

  const unit = data.calculation_unit || 'kg';
  const isCompressed = data.spread_status === 'COMPRESSED_MARGIN';
  const isExpanded = data.spread_status === 'EXPANDED_SPREAD';
  const grossSpread = data.gross_spread_bdt || 0;
  const residual = data.residual_spread_bdt !== null ? data.residual_spread_bdt : 0;
  const compressionAmt = data.margin_compression_bdt || 0;

  // Extract component values
  const compMap = {};
  (data.components || []).forEach((c) => {
    compMap[c.name] = c;
  });

  const freightComp = (data.components || []).find((c) => c.name.includes('Freight') || c.name.includes('Transport'));
  const arathComp = (data.components || []).find((c) => c.name.includes('Arath') || c.name.includes('Commission'));
  const handlingComp = (data.components || []).find((c) => c.name.includes('Handling') || c.name.includes('Porterage'));
  const wastageComp = (data.components || []).find((c) => c.name.includes('Spoilage') || c.name.includes('Shrinkage'));

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xs relative overflow-hidden">
      {/* Header with Title & Provenance Indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-outfit">
              {getTranslation('sc_title', lang)}
            </h2>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {getTranslation('sc_subtitle', lang)}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Status Badge */}
          {isCompressed ? (
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>{getTranslation('sc_margin_compressed', lang)}</span>
            </span>
          ) : isExpanded ? (
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-900 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-800">
              {getTranslation('sc_expanded_spread', lang)}
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>{getTranslation('sc_normal_spread', lang)}</span>
            </span>
          )}

          <button
            type="button"
            onClick={() => setShowMethodologyModal(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
            title="Methodology & Provenance Notice"
            aria-label="Methodology & Provenance Notice"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ── SECTION 1: OBSERVED BENCHMARK SPREAD ─────────────────────────────── */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700/80 mb-5">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-2">
          <span className="font-bold uppercase tracking-wider text-[10px] text-slate-600 dark:text-slate-300 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            {getTranslation('sc_observed_benchmarks', lang)}
          </span>
          {data.is_symmetric_freshness ? (
            <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
              {lang === 'bn' ? '✓ উভয় দর একই তারিখের' : '✓ Synchronous Observation'}
            </span>
          ) : (
            <span className="text-[11px] font-mono text-amber-600 dark:text-amber-400">
              {lang === 'bn' ? `! ${data.temporal_divergence_days} দিনের ব্যবধান` : `! ${data.temporal_divergence_days}d gap`}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
          {/* Wholesale Box */}
          <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans">
              {getTranslation('sc_wholesale_base', lang)}
            </span>
            <div className="text-xl font-black text-slate-900 dark:text-white font-mono mt-0.5">
              ৳ {toBengaliNumeral(data.wholesale_price, lang)}
              <span className="text-xs font-normal text-slate-500">/{unit}</span>
            </div>
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block truncate mt-1">
              {data.wholesale_market_name}
            </span>
          </div>

          {/* Spread Arrow */}
          <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center relative">
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans">
              {getTranslation('sc_gross_spread', lang)}
            </span>
            <div className={`text-xl font-black font-mono mt-0.5 ${grossSpread >= 0 ? 'text-indigo-600 dark:text-indigo-400' : 'text-amber-600 dark:text-amber-400'}`}>
              {grossSpread >= 0 ? '+' : ''}৳ {toBengaliNumeral(grossSpread, lang)}
              <span className="text-xs font-normal text-slate-500">/{unit}</span>
            </div>
            <span className="text-[10px] text-slate-400 block mt-1">
              {grossSpread >= 0 ? `+${data.gross_spread_pct}%` : `${data.gross_spread_pct}%`}
            </span>
          </div>

          {/* Retail Box */}
          <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans">
              {getTranslation('sc_retail_base', lang)}
            </span>
            <div className="text-xl font-black text-slate-900 dark:text-white font-mono mt-0.5">
              ৳ {toBengaliNumeral(data.retail_price, lang)}
              <span className="text-xs font-normal text-slate-500">/{unit}</span>
            </div>
            <span className="text-[10px] text-slate-400 dark:text-slate-500 block truncate mt-1">
              {data.retail_market_name}
            </span>
          </div>
        </div>
      </div>

      {/* ── SECTION 2: DECONSTRUCTED COST BREAKDOWN CARDS ────────────────────── */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3 text-xs">
          <span className="font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-indigo-500" />
            <span>{getTranslation('sc_modeled_assumptions', lang)}</span>
          </span>
          <span className="text-[11px] text-slate-500">
            {lang === 'bn' ? 'গবেষণালব্ধ অর্থনৈতিক মডেল' : 'Secondary Research Estimates'}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {/* Freight Item */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 flex flex-col justify-between">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
                {getTranslation('sc_freight_logistics', lang)}
              </span>
              <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono mt-0.5 block">
                ৳ {toBengaliNumeral(freightComp?.value_bdt || 0, lang)}
              </span>
            </div>
            <span className="text-[9px] font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-1.5 py-0.5 rounded mt-2 w-fit">
              {freightComp?.provenance_type === 'OFFICIAL' ? getTranslation('sc_provenance_official', lang) : getTranslation('sc_provenance_modeled', lang)}
            </span>
          </div>

          {/* Arath Commission */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 flex flex-col justify-between">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
                {getTranslation('sc_arath_commission', lang)}
              </span>
              <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono mt-0.5 block">
                ৳ {toBengaliNumeral(arathComp?.value_bdt || 0, lang)}
              </span>
            </div>
            <span className="text-[9px] font-bold text-slate-600 dark:text-slate-300 bg-slate-200/80 dark:bg-slate-700 px-1.5 py-0.5 rounded mt-2 w-fit">
              {getTranslation('sc_provenance_modeled', lang)} (3%)
            </span>
          </div>

          {/* Handling & Porterage */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 flex flex-col justify-between">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
                {getTranslation('sc_handling_porterage', lang)}
              </span>
              <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono mt-0.5 block">
                ৳ {toBengaliNumeral(handlingComp?.value_bdt || 0, lang)}
              </span>
            </div>
            <span className="text-[9px] font-bold text-slate-600 dark:text-slate-300 bg-slate-200/80 dark:bg-slate-700 px-1.5 py-0.5 rounded mt-2 w-fit">
              {getTranslation('sc_provenance_modeled', lang)}
            </span>
          </div>

          {/* Spoilage Allowance */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 flex flex-col justify-between">
            <div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block">
                {getTranslation('sc_transit_wastage', lang)}
              </span>
              <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono mt-0.5 block">
                ৳ {toBengaliNumeral(wastageComp?.value_bdt || 0, lang)}
              </span>
            </div>
            <span className="text-[9px] font-bold text-slate-600 dark:text-slate-300 bg-slate-200/80 dark:bg-slate-700 px-1.5 py-0.5 rounded mt-2 w-fit">
              {getTranslation('sc_provenance_modeled', lang)}
            </span>
          </div>
        </div>
      </div>

      {/* ── SECTION 3: RESIDUAL SPREAD BANNER ────────────────────────────────── */}
      <div className={`p-4 rounded-xl border mb-4 ${isCompressed ? 'bg-amber-50/70 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800/60' : 'bg-indigo-50/70 dark:bg-indigo-950/20 border-indigo-200 dark:border-indigo-800/50'}`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-xs font-bold text-slate-900 dark:text-white block font-outfit">
              {getTranslation('sc_residual_spread', lang)}
            </span>
            <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
              {isCompressed
                ? (lang === 'bn'
                    ? `মধ্যবর্তী ব্যয় মোট দামের ব্যবধানকে ৳${toBengaliNumeral(compressionAmt, lang)} অতিক্রম করেছে। মার্জিন সংকোচন বা পরিবহন ঘাটতি বিদ্যমান।`
                    : `Intermediate costs exceed price spread by BDT ${compressionAmt}. Margin compression or transport deficit exists.`)
                : (lang === 'bn'
                    ? 'মোট দামের ব্যবধান থেকে পর্যবেক্ষিত পরিবহন ও মধ্যবর্তী মডেল ব্যয় বাদ দেওয়ার পর গাণিতিক অবশিষ্ট অংশ। এটি সরাসরি নিরীক্ষিত নয়।'
                    : 'Mathematical remainder after subtracting supported freight and modeled intermediary components from gross spread. It is NOT directly observed.')}
            </p>
          </div>

          <div className="text-right flex-shrink-0">
            <span className={`text-2xl font-black font-mono block ${isCompressed ? 'text-amber-600 dark:text-amber-400' : 'text-indigo-600 dark:text-indigo-400'}`}>
              {residual < 0 ? '-' : ''}৳ {toBengaliNumeral(Math.abs(residual), lang)}
              <span className="text-xs font-normal text-slate-500">/{unit}</span>
            </span>
            <span className="text-[10px] text-slate-500 block">
              {grossSpread > 0 ? `${((residual / grossSpread) * 100).toFixed(1)}% of spread` : 'Residual Balance'}
            </span>
          </div>
        </div>
      </div>

      {/* ── SECTION 4: EXPANDABLE ACCORDION (RESEARCH / AUDIT DRILL-DOWN) ─────── */}
      <div className="border-t border-slate-200 dark:border-slate-800 pt-3">
        <button
          type="button"
          onClick={() => setIsAccordionOpen(!isAccordionOpen)}
          className="w-full flex items-center justify-between text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white py-1 transition cursor-pointer"
        >
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>{lang === 'bn' ? 'গবেষণা ও সম্পূর্ণ ব্যয় উপাত্ত তালিকা' : 'Research & Full Itemized Breakdown Table'}</span>
          </span>
          {isAccordionOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {isAccordionOpen && (
          <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 animate-in fade-in duration-200">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 text-[10px] uppercase font-bold">
                    <th className="py-2 pr-3">{lang === 'bn' ? 'ব্যয় উপাদান' : 'Component'}</th>
                    <th className="py-2 px-2 text-right">{lang === 'bn' ? 'মূল্য (৳)' : 'Cost (BDT)'}</th>
                    <th className="py-2 px-2">{lang === 'bn' ? 'উপাত্ত শ্রেণি' : 'Provenance'}</th>
                    <th className="py-2 pl-3">{lang === 'bn' ? 'তথ্যসূত্র ও পদ্ধতি' : 'Source & Reference'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-[11px]">
                  {(data.components || []).map((comp, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="py-2 pr-3 font-medium text-slate-900 dark:text-slate-100">
                        {lang === 'bn' ? comp.bangla_name : comp.name}
                      </td>
                      <td className="py-2 px-2 text-right font-mono font-bold text-slate-800 dark:text-slate-200">
                        ৳ {toBengaliNumeral(comp.value_bdt, lang)}
                      </td>
                      <td className="py-2 px-2">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          comp.provenance_type === 'OBSERVED'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                            : comp.provenance_type === 'OFFICIAL'
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                            : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        }`}>
                          {comp.provenance_type}
                        </span>
                      </td>
                      <td className="py-2 pl-3 text-slate-500 dark:text-slate-400 text-[10px] leading-tight">
                        <span className="font-semibold text-slate-700 dark:text-slate-300 block">{comp.source_name}</span>
                        <span>{comp.methodology_note}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ── METHODOLOGY & TRANSPARENCY MODAL ─────────────────────────────────── */}
      {showMethodologyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 max-w-lg w-full shadow-2xl relative">
            <button
              type="button"
              onClick={() => setShowMethodologyModal(false)}
              className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
            >
              ✕
            </button>

            <div className="flex items-center gap-2 mb-3">
              <Scale className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white font-outfit">
                {lang === 'bn' ? 'মূল্য বিশ্লেষণ ও প্রাক্কলন পদ্ধতি' : 'Supply Chain Methodology & Provenance'}
              </h3>
            </div>

            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed max-h-[70vh] overflow-y-auto pr-1">
              <p>
                {data.methodology_disclaimer}
              </p>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span className="font-bold text-slate-900 dark:text-white block mb-1">
                  {lang === 'bn' ? '১. সরাসরি পর্যবেক্ষিত তথ্য (OBSERVED)' : '1. Directly Observed Data'}
                </span>
                {lang === 'bn'
                  ? 'পাইকারি ও খুচরা বাজারদর সরকারি সংস্থা (DAM, TCB) এবং কাঁচাবাজার থেকে সরাসরি সংগৃহীত। হাইওয়ে সড়ক দূরত্ব ভূ-স্থানিক ম্যাপিং দ্বারা নির্ধারিত।'
                  : 'Wholesale and retail prices are collected directly from primary markets and DAM bulletins. Highway transit distances reflect geographic routing.'}
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span className="font-bold text-slate-900 dark:text-white block mb-1">
                  {lang === 'bn' ? '২. অর্থনৈতিক মডেল প্রাক্কলন (MODELED_ASSUMPTION)' : '2. Modeled Economic Assumptions'}
                </span>
                {lang === 'bn'
                  ? 'আড়তদারি কমিশন (৩.০%), কুলি খরচ (৳১.২৫/কেজি), এবং পচনশীলতা অপচয় (০.৫% - ৬.০%) কৃষি গবেষণা সাহিত্য ও নীতিমালার আলোকে প্রাক্কলিত। এটি নির্দিষ্ট কোনো ব্যবসায়ীর ক্যাশ মেমো নয়।'
                  : 'Arath commission (3.0%), handling (1.25 BDT/kg), and transit wastage (0.5% - 6.0%) are modeled from agricultural research literature. They are not merchant ledger entries.'}
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <span className="font-bold text-slate-900 dark:text-white block mb-1">
                  {lang === 'bn' ? '৩. অবশিষ্ট স্প্রেড — অনিরীক্ষিত/অনাবন্টিত অংশ' : '3. Residual Spread — Unobserved/Unallocated Portion'}
                </span>
                {lang === 'bn'
                  ? 'মোট দামের ব্যবধান থেকে পর্যবেক্ষিত পরিবহন ও মধ্যবর্তী মডেল ব্যয় বাদ দেওয়ার পর গাণিতিক অবশিষ্ট অংশ। এটি সরাসরি নিরীক্ষিত নয় এবং কোনো নির্দিষ্ট ব্যবসায়ীর প্রকৃত মুনাফা বা প্রত্যক্ষ পরিচালন ব্যয় হিসেবে দাবি করা হয় না।'
                  : 'Calculated as the mathematical remainder after subtracting supported freight and modeled intermediate cost components from gross spread. It is NOT directly observed and is not claimed as actual retailer profit or observed operating cost.'}
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowMethodologyModal(false)}
              className="mt-4 w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 text-white transition cursor-pointer"
            >
              {lang === 'bn' ? 'বুঝেছি' : 'Understood'}
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
