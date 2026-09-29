import React from 'react';
import { 
  VegetableIcon, 
  GrainIcon, 
  MeatFishIcon, 
  DairyEggIcon, 
  OilSpiceIcon, 
  AllStaplesIcon 
} from './media/CommodityIcon';
import { Flame } from 'lucide-react';
import { 
  getCommodityCanonicalCategory,
  COMMODITY_CANONICAL_CATEGORY,
  CANONICAL_CATEGORY_MAP 
} from '../utils/taxonomy';

export { getCommodityCanonicalCategory, COMMODITY_CANONICAL_CATEGORY, CANONICAL_CATEGORY_MAP };

export const CATEGORIES = [
  { 
    id: 'all', 
    labelEn: 'All Items', 
    labelBn: 'সব পণ্য', 
    icon: AllStaplesIcon 
  },
  {
    id: 'trending_up',
    labelEn: 'Trending Up',
    labelBn: 'আজ বাড়তির দিকে',
    icon: Flame,
    isTrending: true,
  },
  { 
    id: 'vegetables', 
    labelEn: 'Vegetables', 
    labelBn: 'শাকসবজি', 
    icon: VegetableIcon, 
  },
  { 
    id: 'grains_pulses', 
    labelEn: 'Grains & Pulses', 
    labelBn: 'চাল ও ডাল', 
    icon: GrainIcon, 
  },
  { 
    id: 'meat_fish', 
    labelEn: 'Meat & Fish', 
    labelBn: 'মাছ ও মাংস', 
    icon: MeatFishIcon, 
  },
  { 
    id: 'eggs_dairy', 
    labelEn: 'Eggs & Dairy', 
    labelBn: 'ডিম ও দুধ', 
    icon: DairyEggIcon, 
  },
  { 
    id: 'oils_spices', 
    labelEn: 'Oils & Spices', 
    labelBn: 'তেল ও মসলা', 
    icon: OilSpiceIcon, 
  },
];

export function matchesCategory(item, categoryId) {
  if (!categoryId || categoryId === 'all') return true;

  if (categoryId === 'trending_up') {
    const pct = item.percentage_change_7d !== undefined 
      ? Number(item.percentage_change_7d) 
      : item.change_pct !== undefined 
      ? Number(item.change_pct) 
      : 0;
    return pct > 1.5;
  }

  const itemCat = getCommodityCanonicalCategory(item);
  return itemCat === categoryId;
}

export default function CategoryFilter({
  selectedCategory,
  onSelectCategory,
  itemsCountMap = {},
  lang = 'bn',
}) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none my-2 select-none">
      {CATEGORIES.map((cat) => {
        const IconComponent = cat.icon;
        const isSelected = selectedCategory === cat.id;
        const count = itemsCountMap[cat.id];
        const label = lang === 'bn' ? cat.labelBn : cat.labelEn;

        return (
          <button
            key={cat.id}
            type="button"
            onClick={() => onSelectCategory(cat.id)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border ${
              isSelected
                ? cat.isTrending
                  ? 'bg-rose-600 text-white border-rose-600 shadow-md shadow-rose-950/20'
                  : 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-950/20'
                : cat.isTrending
                ? 'bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800/50 hover:border-rose-300'
                : 'bg-white dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 shadow-sm'
            }`}
          >
            <IconComponent className={`w-4 h-4 flex-shrink-0 ${
              isSelected 
                ? 'text-white' 
                : cat.isTrending 
                ? 'text-rose-500' 
                : 'text-slate-500 dark:text-slate-400'
            }`} />
            <span>{cat.isTrending ? `🔥 ${label}` : label}</span>
            {count !== undefined && (
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                  isSelected
                    ? cat.isTrending
                      ? 'bg-rose-800/50 text-white'
                      : 'bg-emerald-800/50 text-white'
                    : cat.isTrending
                    ? 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                }`}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
