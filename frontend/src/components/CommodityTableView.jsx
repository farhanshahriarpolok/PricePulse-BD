import React from 'react';
import CommodityIcon from './media/CommodityIcon';
import { 
  toBengaliNumeral, 
  getTrendBadge, 
  FAMILIAR_NAMES 
} from './CommodityCard';
import { getCommodityCanonicalCategory } from '../utils/taxonomy';
import { getMarketById, calculateMarketPrice } from '../utils/markets';
import { ShoppingBasket, Plus, Minus, ArrowRight, Check } from 'lucide-react';

const CATEGORY_LABELS = {
  vegetables: { bn: 'শাকসবজি', en: 'Vegetables', badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800' },
  grains_pulses: { bn: 'চাল ও ডাল', en: 'Grains & Pulses', badge: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border-amber-200 dark:border-amber-800' },
  meat_fish: { bn: 'মাছ ও মাংস', en: 'Meat & Fish', badge: 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border-rose-200 dark:border-rose-800' },
  eggs_dairy: { bn: 'ডিম ও দুধ', en: 'Eggs & Dairy', badge: 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-300 border-sky-200 dark:border-sky-800' },
  oils_spices: { bn: 'তেল ও মসলা', en: 'Oils & Spices', badge: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border-purple-200 dark:border-purple-800' },
};

function formatPrice(val) {
  if (val === null || val === undefined || isNaN(val)) return '--';
  const rounded = Math.round(Number(val) * 2) / 2;
  return rounded % 1 === 0 ? rounded : rounded.toFixed(1);
}

export default function CommodityTableView({
  items = [],
  lang = 'bn',
  getBasketQuantity,
  onAddToBasket,
  onUpdateQuantity,
  onSelectCommodity,
  selectedMarketId = 'dhaka_mirpur1',
}) {
  if (!items || items.length === 0) return null;

  const activeMarket = getMarketById(selectedMarketId);

  return (
    <div className="w-full overflow-hidden rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[760px]">
          {/* Table Header */}
          <thead>
            <tr className="bg-slate-100/90 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-700/80 select-none">
              <th scope="col" className="py-3.5 px-4 font-outfit">
                {lang === 'bn' ? 'পণ্য' : 'Commodity'}
              </th>
              <th scope="col" className="py-3.5 px-3 font-outfit">
                {lang === 'bn' ? 'ক্যাটাগরি' : 'Category'}
              </th>
              <th scope="col" className="py-3.5 px-3 font-outfit">
                {lang === 'bn' ? 'আজকের দর (গড়)' : 'Avg Price'}
              </th>
              <th scope="col" className="py-3.5 px-3 font-outfit">
                {lang === 'bn' ? 'পাইকারি দর' : 'Wholesale'}
              </th>
              <th scope="col" className="py-3.5 px-3 font-outfit">
                {lang === 'bn' ? 'খুচরা দর' : 'Retail'}
              </th>
              <th scope="col" className="py-3.5 px-3 font-outfit">
                {lang === 'bn' ? 'অনলাইন দর' : 'Online'}
              </th>
              <th scope="col" className="py-3.5 px-3 font-outfit">
                {lang === 'bn' ? 'ট্রেন্ড' : 'Trend'}
              </th>
              <th scope="col" className="py-3.5 px-4 text-right font-outfit">
                {lang === 'bn' ? 'অ্যাকশন' : 'Action'}
              </th>
            </tr>
          </thead>

          {/* Table Body with alternating subtle zebra stripes */}
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {items.map((item) => {
              const familiar = FAMILIAR_NAMES[item.canonical_name];
              const displayTitle = lang === 'bn' 
                ? (familiar?.bn || item.bangla_name || item.canonical_name)
                : (familiar?.en || item.canonical_name);
              const displaySubtitle = lang === 'bn' 
                ? (familiar?.en || item.canonical_name)
                : (familiar?.bn || item.bangla_name || '');

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

              if (isEgg) {
                displayUnit = lang === 'bn' ? 'হালি' : 'Hali (4 pcs)';
                if (rawAvg > 0 && rawAvg < 30) {
                  const perPiece = rawAvg;
                  rawAvg = rawAvg * 4;
                  rawWs = rawWs ? rawWs * 4 : Math.round(rawAvg * 0.85);
                  rawRet = rawRet ? rawRet * 4 : rawAvg;
                  rawOn = rawOn ? rawOn * 4 : Math.round(rawAvg * 1.08);
                  perPieceSubtext = lang === 'bn'
                    ? `প্রতি পিস ৳ ${toBengaliNumeral(formatPrice(perPiece), lang)}`
                    : `৳ ${formatPrice(perPiece)} / pc`;
                } else if (rawAvg >= 30) {
                  const perPiece = rawAvg / 4;
                  perPieceSubtext = lang === 'bn'
                    ? `প্রতি পিস ৳ ${toBengaliNumeral(formatPrice(perPiece), lang)}`
                    : `৳ ${formatPrice(perPiece)} / pc`;
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

              const catKey = getCommodityCanonicalCategory(item);
              const catMeta = CATEGORY_LABELS[catKey] || { bn: 'নিত্যপণ্য', en: 'Staple', badge: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300' };

              const qty = getBasketQuantity ? getBasketQuantity(item) : 0;

              return (
                <tr 
                  key={item.commodity_id || item.id}
                  onClick={() => onSelectCommodity && onSelectCommodity(item)}
                  className="even:bg-slate-50/60 dark:even:bg-slate-800/30 hover:bg-emerald-50/50 dark:hover:bg-slate-800/80 transition-colors cursor-pointer group"
                >
                  {/* 1. Commodity Name & Icon */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-center p-1.5 flex-shrink-0 group-hover:scale-105 transition-transform">
                        <CommodityIcon
                          category={item.category}
                          name={item.canonical_name}
                          className="w-full h-full object-contain"
                        />
                      </div>
                      <div className="min-w-0">
                        <span className="font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors block truncate">
                          {displayTitle}
                        </span>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400 block truncate">
                          {displaySubtitle}
                        </span>
                      </div>
                    </div>
                  </td>

                  {/* 2. Category */}
                  <td className="py-3 px-3">
                    <span className={`inline-block px-2 py-0.5 text-[11px] font-medium rounded-md border ${catMeta.badge}`}>
                      {lang === 'bn' ? catMeta.bn : catMeta.en}
                    </span>
                  </td>

                  {/* 3. Average Price */}
                  <td className="py-3 px-3">
                    <div className="font-mono">
                      <span className="font-bold text-slate-900 dark:text-white">
                        ৳ {toBengaliNumeral(formatPrice(rawAvg), lang)}
                      </span>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 ml-0.5">
                        /{displayUnit}
                      </span>
                    </div>
                    {perPieceSubtext && (
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 block">
                        {perPieceSubtext}
                      </span>
                    )}
                  </td>

                  {/* 4. Wholesale */}
                  <td className="py-3 px-3 font-mono text-slate-700 dark:text-slate-300">
                    ৳ {toBengaliNumeral(Math.round(wholesale), lang)}
                  </td>

                  {/* 5. Retail (Selected Market Rate & Tag) */}
                  <td className="py-3 px-3">
                    <div className="font-mono text-slate-700 dark:text-slate-300 font-medium">
                      ৳ {toBengaliNumeral(Math.round(calculateMarketPrice(retail, selectedMarketId)), lang)}
                    </div>
                    <span className="text-[10px] text-emerald-700 dark:text-emerald-400 font-sans block truncate">
                      ({lang === 'bn' ? activeMarket.shortBn : activeMarket.shortEn})
                    </span>
                  </td>

                  {/* 6. Online */}
                  <td className="py-3 px-3 font-mono text-slate-700 dark:text-slate-300">
                    ৳ {toBengaliNumeral(Math.round(online), lang)}
                  </td>

                  {/* 7. Trend Badge */}
                  <td className="py-3 px-3">
                    <span className={`inline-block px-2 py-0.5 text-[11px] font-bold rounded-md whitespace-nowrap ${trend.className}`}>
                      {trend.label}
                    </span>
                  </td>

                  {/* 8. Action */}
                  <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-2">
                      {qty > 0 ? (
                        <div className="flex items-center rounded-lg border border-emerald-500 bg-emerald-50/80 dark:bg-emerald-950/40 p-0.5 text-xs">
                          <button
                            type="button"
                            onClick={() => onUpdateQuantity && onUpdateQuantity(item, -1)}
                            aria-label="Decrease quantity"
                            className="w-6 h-6 flex items-center justify-center rounded bg-white dark:bg-slate-800 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900 border border-emerald-300 dark:border-emerald-700 font-bold transition-colors"
                          >
                            <Minus className="w-3 h-3" />
                          </button>
                          <span className="font-bold text-emerald-800 dark:text-emerald-200 px-2 font-mono text-center min-w-[2.5rem]">
                            {toBengaliNumeral(qty, lang)}
                          </span>
                          <button
                            type="button"
                            onClick={() => onUpdateQuantity && onUpdateQuantity(item, 1)}
                            aria-label="Increase quantity"
                            className="w-6 h-6 flex items-center justify-center rounded bg-emerald-600 text-white hover:bg-emerald-500 font-bold transition-colors shadow-xs"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => {
                            if (onUpdateQuantity) onUpdateQuantity(item, 1);
                            else if (onAddToBasket) onAddToBasket(item);
                          }}
                          className="px-2.5 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-xs flex items-center gap-1 active:scale-95"
                        >
                          <ShoppingBasket className="w-3.5 h-3.5" />
                          <span>{lang === 'bn' ? '+ ফর্দে যোগ' : '+ Add'}</span>
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => onSelectCommodity && onSelectCommodity(item)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        title={lang === 'bn' ? 'বিস্তারিত দেখুন' : 'Details'}
                      >
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
