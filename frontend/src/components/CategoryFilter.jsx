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
    <div className="border-b border-slate-200 dark:border-slate-800 w-full mb-6">
      <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto scrollbar-none pb-px select-none">
        {CATEGORIES.map((cat) => {
          const IconComponent = cat.icon;
          const isSelected = selectedCategory === cat.id;
          const count = itemsCountMap[cat.id];
          const label = lang === 'bn' ? cat.labelBn : cat.labelEn;

          let activeClasses = '';
          let inactiveClasses = 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/70 dark:hover:bg-slate-800/50 border-b-2 border-transparent';

          if (isSelected) {
            if (cat.isTrending) {
              activeClasses = 'text-rose-700 dark:text-rose-400 font-bold border-b-2 border-rose-600 dark:border-rose-500 bg-rose-50/70 dark:bg-rose-950/30';
            } else {
              activeClasses = 'text-emerald-700 dark:text-emerald-400 font-bold border-b-2 border-emerald-600 dark:border-emerald-500 bg-emerald-50/70 dark:bg-emerald-950/30';
            }
          }

          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelectCategory(cat.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 text-xs sm:text-sm whitespace-nowrap transition-all rounded-t-lg ${
                isSelected ? activeClasses : inactiveClasses
              }`}
            >
              <IconComponent className={`w-4 h-4 flex-shrink-0 ${
                isSelected 
                  ? cat.isTrending ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400' 
                  : cat.isTrending ? 'text-rose-500' : 'text-slate-400 dark:text-slate-500'
              }`} />
              <span>{cat.isTrending ? `🔥 ${label}` : label}</span>
              {count !== undefined && (
                <span
                  className={`text-[11px] px-1.5 py-0.5 rounded-md font-mono font-medium ${
                    isSelected
                      ? cat.isTrending
                        ? 'bg-rose-100 dark:bg-rose-900/50 text-rose-800 dark:text-rose-200'
                        : 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-200'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
