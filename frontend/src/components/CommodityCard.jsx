import React, { useState } from 'react';
import MiniSparkline from './MiniSparkline';
import CommodityIcon from './media/CommodityIcon';
import { ShoppingBasket, Check, ArrowRight, Clock, Plus, Minus } from 'lucide-react';

/**
 * Converts English digits to Bengali numerals if language is 'bn'.
 */
export function toBengaliNumeral(num, lang = 'bn') {
  if (num === null || num === undefined || isNaN(num)) return '--';
  const str = typeof num === 'number' ? (Number.isInteger(num) ? String(num) : num.toFixed(1)) : String(num);
  if (lang !== 'bn') return str;
  const bnDigits = { '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯' };
  return str.replace(/[0-9]/g, (d) => bnDigits[d] || d);
}

/**
 * Human-friendly, non-academic trend badge.
 */
export function getTrendBadge(pctChange, lang = 'bn') {
  const pct = Number(pctChange) || 0;
  const absVal = Math.abs(pct).toFixed(1);
  const formattedPct = toBengaliNumeral(absVal, lang);

  if (pct >= 0.5) {
    return {
      label: lang === 'bn' ? `↑ ${formattedPct}%` : `↑ ${absVal}%`,
      className: 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30',
    };
  }
  if (pct <= -0.5) {
    return {
      label: lang === 'bn' ? `↓ ${formattedPct}%` : `↓ ${absVal}%`,
      className: 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30',
    };
  }
  return {
    label: lang === 'bn' ? 'স্থির' : 'Stable',
    className: 'bg-slate-100 text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
  };
}

/**
 * Standard Consumer Familiar Titles for Clean Bazaar Look
 */
export const FAMILIAR_NAMES = {
  'Farm Egg': { bn: 'ফার্মের ডিম', en: 'Farm Egg' },
  'Farm Eggs (Brown)': { bn: 'ফার্মের ডিম', en: 'Farm Egg' },
  'Pasteurized Cow Milk': { bn: 'প্যাকেটজাত তরল দুধ', en: 'Pasteurized Milk' },
  'Milk (Pasteurized)': { bn: 'প্যাকেটজাত তরল দুধ', en: 'Pasteurized Milk' },
  'Soybean Oil (Bottled)': { bn: 'বোতলজাত সয়াবিন তেল', en: 'Bottled Soybean Oil' },
  'Soybean Oil (Loose)': { bn: 'খোলা সয়াবিন তেল', en: 'Loose Soybean Oil' },
  'Sugar (Refined White)': { bn: 'চিনি (সাদা পরিশোধিত)', en: 'White Refined Sugar' },
  'Brinjal (Eggplant)': { bn: 'বেগুন (গোল/লম্বা)', en: 'Brinjal (Eggplant)' },
  'Potato (Diamond)': { bn: 'গোল আলু (ডায়মন্ড)', en: 'Potato (Diamond)' },
  'Onion (Local)': { bn: 'দেশি পেঁয়াজ', en: 'Local Onion' },
  'Onion (Imported)': { bn: 'আমদানি পেঁয়াজ', en: 'Imported Onion' },
  'Garlic (Local)': { bn: 'দেশি রসুন', en: 'Local Garlic' },
  'Ginger (Local)': { bn: 'দেশি আদা', en: 'Local Ginger' },
  'Green Chilli': { bn: 'কাঁচা মরিচ', en: 'Green Chilli' },
  'Broiler Chicken': { bn: 'ব্রয়লার মুরগি', en: 'Broiler Chicken' },
  'Deshi Chicken': { bn: 'দেশি মুরগি', en: 'Deshi Chicken' },
  'Beef (Local with Bone)': { bn: 'গরুর মাংস (হাড়সহ)', en: 'Beef (with Bone)' },
  'Mutton (Goat Meat)': { bn: 'খাসির মাংস', en: 'Mutton (Goat Meat)' },
  'Rui Fish (Fresh)': { bn: 'রুই মাছ', en: 'Rui Fish (Fresh)' },
  'Tilapia Fish': { bn: 'তেলাপিয়া মাছ', en: 'Tilapia Fish' },
  'Pangas Fish (Farm)': { bn: 'পাঙ্গাশ মাছ', en: 'Pangas Fish' },
  'Hilsa Fish (Medium)': { bn: 'ইলিশ মাছ (মাঝারি)', en: 'Hilsa Fish (Medium)' },
  'Rice (Miniket)': { bn: 'মিনিকেট চাল', en: 'Miniket Rice' },
  'Rice (Nazirshail)': { bn: 'নাজিরশাইল চাল', en: 'Nazirshail Rice' },
  'Rice (Coarse)': { bn: 'মোটা চাল', en: 'Coarse Rice' },
  'Masur Dal (Medium)': { bn: 'মসুর ডাল (মাঝারি)', en: 'Masur Dal (Medium)' },
  'Masur Dal (Fine)': { bn: 'মসুর ডাল (চিকন)', en: 'Masur Dal (Fine)' },
  'Salt (Iodized)': { bn: 'আয়োডিনযুক্ত লবণ', en: 'Iodized Salt' },
  'Mustard Oil': { bn: 'খাঁটি সরিষার তেল', en: 'Mustard Oil' },
  'Dry Red Chilli': { bn: 'শুকনা মরিচ', en: 'Dry Red Chilli' },
  'Turmeric Powder': { bn: 'হলুদ গুঁড়া', en: 'Turmeric Powder' },
  'Atta (Packaged)': { bn: 'প্যাকেটজাত আটা', en: 'Packaged Atta' },
  'Maida (Packaged)': { bn: 'প্যাকেটজাত ময়দা', en: 'Packaged Maida' },
  'Tomato': { bn: 'পাকা টমেটো', en: 'Fresh Tomato' },
  'Papaya (Green)': { bn: 'কাঁচা পেঁপে', en: 'Green Papaya' },
  'Cucumber': { bn: 'শসা', en: 'Fresh Cucumber' },
  'Carrot': { bn: 'গাজর', en: 'Fresh Carrot' },
};

function formatBazaarPrice(val) {
  if (val === null || val === undefined || isNaN(val)) return '--';
  const rounded = Math.round(Number(val) * 2) / 2;
  return rounded % 1 === 0 ? rounded : rounded.toFixed(1);
}

export default function CommodityCard({
  item,
  onClick,
  onAddToBasket,
  onUpdateQuantity,
  basketQuantity = 0,
  isHero = false,
  lang = 'bn',
}) {
  const [justAdded, setJustAdded] = useState(false);

  if (!item) return null;

  // Title formatting: Use consumer familiar titles
  const familiar = FAMILIAR_NAMES[item.canonical_name];
  const displayTitle = lang === 'bn' 
    ? (familiar?.bn || item.bangla_name || item.canonical_name)
    : (familiar?.en || item.canonical_name);
  const displaySubtitle = lang === 'bn' 
    ? (familiar?.en || item.canonical_name)
    : (familiar?.bn || item.bangla_name || '');

  // Natural Egg Unit Conversion (pc -> হালি / 4 pcs)
  const isEgg = (
    item.canonical_name === 'Farm Egg' ||
    item.canonical_name === 'Farm Eggs (Brown)' ||
    (item.canonical_name && item.canonical_name.toLowerCase().includes('egg') && !item.canonical_name.toLowerCase().includes('eggplant')) ||
    (item.bangla_name && item.bangla_name.includes('ডিম') && !item.bangla_name.includes('বেগুন'))
  );

  let rawAvg = item.price_summary?.avg_price || item.avg_price || 0.0;
  let rawWs = item.wholesale_avg || item.channels?.wholesale_avg;
  let rawRet = item.retail_avg || item.channels?.retail_avg || rawAvg;
  let rawOn = item.online_avg || item.channels?.online_avg;

  let displayUnit = item.unit || (lang === 'bn' ? 'কেজি' : 'kg');
  let perPieceSubtext = null;
  let sparklineMultiplier = 1;

  if (isEgg) {
    displayUnit = lang === 'bn' ? 'হালি' : 'Hali (4 pcs)';
    if (rawAvg > 0 && rawAvg < 30) {
      const perPiece = rawAvg;
      rawAvg = rawAvg * 4;
      rawWs = rawWs ? rawWs * 4 : Math.round(rawAvg * 0.85);
      rawRet = rawRet ? rawRet * 4 : rawAvg;
      rawOn = rawOn ? rawOn * 4 : Math.round(rawAvg * 1.08);
      sparklineMultiplier = 4;
      perPieceSubtext = lang === 'bn'
        ? `প্রতি পিস ৳ ${toBengaliNumeral(formatBazaarPrice(perPiece), lang)}`
        : `৳ ${formatBazaarPrice(perPiece)} / pc`;
    } else if (rawAvg >= 30) {
      const perPiece = rawAvg / 4;
      perPieceSubtext = lang === 'bn'
        ? `প্রতি পিস ৳ ${toBengaliNumeral(formatBazaarPrice(perPiece), lang)}`
        : `৳ ${formatBazaarPrice(perPiece)} / pc`;
    }
  } else {
    if ((displayUnit === 'kg' || displayUnit === 'কেজি') && lang === 'bn') displayUnit = 'কেজি';
    if ((displayUnit === 'liter' || displayUnit === 'লিটার') && lang === 'bn') displayUnit = 'লিটার';
  }

  const wholesale = rawWs || Math.round(rawAvg * 0.88);
  const retail = rawRet || rawAvg;
  const online = rawOn || Math.round(rawAvg * 1.05);

  const pctChange = item.percentage_change_7d !== undefined ? item.percentage_change_7d : 0.0;
  const trend = getTrendBadge(pctChange, lang);

  const sparklineData = item.sparkline_7d && item.sparkline_7d.length > 0
    ? item.sparkline_7d.map(val => val * sparklineMultiplier)
    : [rawAvg * 0.98, rawAvg * 0.99, rawAvg, rawAvg * 1.01, rawAvg];

  const channels = [
    { id: 'ws', name: lang === 'bn' ? 'পাইকারি' : 'Wholesale', price: wholesale },
    { id: 'ret', name: lang === 'bn' ? 'খুচরা' : 'Retail', price: retail },
    { id: 'on', name: lang === 'bn' ? 'অনলাইন' : 'Online', price: online },
  ];

  const minPrice = Math.min(...channels.map((c) => c.price));

  const handleAddClick = (e) => {
    e.stopPropagation();
    setJustAdded(true);
    if (onUpdateQuantity) {
      onUpdateQuantity(1);
    } else if (onAddToBasket) {
      onAddToBasket(item);
    }
    setTimeout(() => {
      setJustAdded(false);
    }, 900);
  };

  // ── HERO CARD VARIANT ──────────────────────────────────────────────────────
  if (isHero) {
    return (
      <div
        onClick={onClick}
        className="col-span-full p-5 sm:p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-xs hover:shadow-sm cursor-pointer transition-all duration-200 group relative overflow-hidden text-slate-800 dark:text-slate-100"
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="flex items-start gap-4">
            <CommodityIcon
              category={item.category}
              name={item.canonical_name}
              className="w-14 h-14 flex-shrink-0 mt-0.5 p-2 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60"
            />
            <div>
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className="px-2.5 py-0.5 text-xs font-bold bg-amber-500 text-white rounded-md flex items-center gap-1 shadow-sm">
                  <span>🔥</span>
                  <span>{lang === 'bn' ? 'আজকের শীর্ষ উঠানামা' : 'Top Market Mover'}</span>
                </span>
                <span className={`px-2.5 py-0.5 text-xs font-bold rounded-md ${trend.className}`}>
                  {trend.label}
                </span>
              </div>

              <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-outfit tracking-tight group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                {displayTitle}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {displaySubtitle}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center gap-6">
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                  ৳ {toBengaliNumeral(formatBazaarPrice(rawAvg), lang)}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  / {displayUnit}
                </span>
              </div>
              {perPieceSubtext && (
                <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium block mt-0.5">
                  {perPieceSubtext}
                </span>
              )}

              {/* 3-Channel Comparison Strip */}
              <div className="mt-2.5 flex items-center gap-1.5 text-xs font-mono text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/60 rounded-lg p-1">
                {channels.map((ch) => {
                  const isCheapest = ch.price === minPrice;
                  return (
                    <span 
                      key={ch.id}
                      className={`px-2 py-0.5 rounded ${
                        isCheapest 
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 font-bold flex items-center gap-1' 
                          : 'text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {isCheapest && <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />}
                      {ch.name}: ৳{toBengaliNumeral(Math.round(ch.price), lang)}
                    </span>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {basketQuantity > 0 ? (
                <div 
                  onClick={(e) => e.stopPropagation()}
                  className="flex items-center rounded-xl border-2 border-emerald-500 bg-emerald-50/80 dark:bg-emerald-950/50 p-1 shadow-sm gap-2"
                >
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onUpdateQuantity) onUpdateQuantity(-1);
                    }}
                    aria-label="Decrease quantity"
                    className="w-8 h-8 flex items-center justify-center rounded-lg bg-white dark:bg-slate-800 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900 border border-emerald-300 dark:border-emerald-700 font-bold transition-colors active:scale-90"
                  >
                    <Minus className="w-4 h-4" />
                  </button>

                  <span className="font-bold text-emerald-800 dark:text-emerald-200 px-2 font-mono text-sm select-none">
                    {toBengaliNumeral(basketQuantity, lang)} {displayUnit}
                  </span>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onUpdateQuantity) onUpdateQuantity(1);
                    }}
                    aria-label="Increase quantity"
                    className="w-8 h-8 flex items-center justify-center rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 font-bold transition-colors active:scale-90 shadow-xs"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button 
                  onClick={handleAddClick}
                  className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md transition-all flex items-center justify-center gap-1.5 whitespace-nowrap active:scale-95"
                >
                  {justAdded ? (
                    <>
                      <Check className="w-4 h-4" />
                      <span>{lang === 'bn' ? 'ফর্দে যুক্ত হয়েছে ✓' : 'Added to List ✓'}</span>
                    </>
                  ) : (
                    <>
                      <ShoppingBasket className="w-4 h-4" />
                      <span>{lang === 'bn' ? '+ ফর্দে যোগ করুন' : '+ Add to Basket'}</span>
                    </>
                  )}
                </button>
              )}

              <button 
                onClick={onClick}
                className="px-3.5 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold border border-slate-200 dark:border-slate-700 transition-all flex items-center justify-center gap-1"
              >
                <span>{lang === 'bn' ? 'বিস্তারিত দেখুন →' : 'Details →'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── STANDARD HYBRID CARD VARIANT ──────────────────────────────────────────
  return (
    <div
      onClick={onClick}
      className="p-5 rounded-2xl bg-white dark:bg-slate-900 hover:bg-slate-50/60 dark:hover:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 shadow-xs hover:shadow-sm transition-all duration-150 cursor-pointer group flex flex-col justify-between space-y-4 h-full"
    >
      {/* 1. Header Row: Category Vector Icon + Multi-line Wrapped Staple Name + English Subtitle */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <div className="w-10 h-10 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-center p-2 flex-shrink-0 group-hover:scale-105 transition-transform mt-0.5">
            <CommodityIcon
              category={item.category}
              name={item.canonical_name}
              className="w-full h-full object-contain"
            />
          </div>
          <div className="min-w-0 flex-1">
            <div className="min-h-[44px] flex flex-col justify-center">
              <h4 
                className="text-sm sm:text-base font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors leading-snug line-clamp-2"
                title={displayTitle}
              >
                {displayTitle}
              </h4>
            </div>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate block mt-0.5">
              {displaySubtitle}
            </span>
          </div>
        </div>

        {/* Compact Trend Pill */}
        <span className={`px-2 py-0.5 text-[11px] font-bold rounded-lg whitespace-nowrap flex-shrink-0 ${trend.className}`}>
          {trend.label}
        </span>
      </div>

      {/* 2. Hero Price & Sparkline Row */}
      <div className="flex items-baseline justify-between pt-0.5">
        <div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white font-mono tracking-tight">
              ৳ {toBengaliNumeral(formatBazaarPrice(rawAvg), lang)}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">/{displayUnit}</span>
          </div>
          {perPieceSubtext && (
            <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium block mt-0.5">
              {perPieceSubtext}
            </span>
          )}
        </div>

        <MiniSparkline
          data={sparklineData}
          percentageChange={pctChange}
          width={64}
          height={22}
        />
      </div>

      {/* 3. 3-Channel Split Comparison Bar */}
      <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-slate-100/80 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800 text-[11px] font-mono text-center">
        {channels.map((ch) => {
          const isCheapest = ch.price === minPrice;
          return (
            <div
              key={ch.id}
              className={`py-1 px-1 rounded-lg flex flex-col justify-center transition-colors ${
                isCheapest
                  ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800/40'
                  : 'text-slate-600 dark:text-slate-400'
              }`}
            >
              <span className="text-[10px] font-sans flex items-center justify-center gap-0.5 leading-none mb-0.5">
                {isCheapest && <Check className="w-2.5 h-2.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />}
                {ch.name}
              </span>
              <span className="leading-tight">৳{toBengaliNumeral(Math.round(ch.price), lang)}</span>
            </div>
          );
        })}
      </div>

      {/* 4. Transparency Badge */}
      <div className="flex items-center text-[10px] text-slate-500 dark:text-slate-400 gap-1 select-none">
        <Clock className="w-3 h-3 text-slate-400 dark:text-slate-500 flex-shrink-0" />
        <span className="truncate">
          {lang === 'bn' ? 'সর্বশেষ আপডেট: আজ সকাল ৭টা (DAM/TCB)' : 'Latest Update: Today 7:00 AM (DAM/TCB)'}
        </span>
      </div>

      {/* 5. Action Bar: Active In-Card Stepper [- N +] or 1-Click '+ ফর্দে যোগ করুন' */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-between gap-2">
        {basketQuantity > 0 ? (
          <div 
            onClick={(e) => e.stopPropagation()}
            className="flex-1 flex items-center justify-between rounded-xl border-2 border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/40 p-0.5 text-xs shadow-xs"
          >
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                if (onUpdateQuantity) onUpdateQuantity(-1);
              }}
              aria-label="Decrease quantity"
              className="w-7 h-7 flex items-center justify-center rounded-lg bg-white dark:bg-slate-800 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900 border border-emerald-300 dark:border-emerald-700 font-bold transition-colors active:scale-90"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>

            <span className="font-bold text-emerald-800 dark:text-emerald-200 px-1.5 font-mono text-center select-none truncate">
              {toBengaliNumeral(basketQuantity, lang)} {displayUnit}
            </span>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                if (onUpdateQuantity) onUpdateQuantity(1);
              }}
              aria-label="Increase quantity"
              className="w-7 h-7 flex items-center justify-center rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 font-bold transition-colors active:scale-90 shadow-xs"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={handleAddClick}
            className={`flex-1 py-1.5 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-sm active:scale-95 ${
              justAdded
                ? 'bg-emerald-700 text-white'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950/20'
            }`}
            title={lang === 'bn' ? 'বাজারে যাওয়ার ফর্দে যুক্ত করুন' : 'Add to Shopping Basket'}
          >
            {justAdded ? (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>{lang === 'bn' ? 'যুক্ত হয়েছে ✓' : 'Added ✓'}</span>
              </>
            ) : (
              <>
                <ShoppingBasket className="w-3.5 h-3.5" />
                <span>{lang === 'bn' ? '+ ফর্দে যোগ করুন' : '+ Add to Basket'}</span>
              </>
            )}
          </button>
        )}

        <button
          type="button"
          onClick={onClick}
          className="px-2.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700/60 transition-colors flex items-center gap-0.5 whitespace-nowrap"
        >
          <span>{lang === 'bn' ? 'বিস্তারিত দেখুন →' : 'Details →'}</span>
        </button>
      </div>
    </div>
  );
}
