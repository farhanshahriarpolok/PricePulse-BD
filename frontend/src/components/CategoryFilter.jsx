import React from 'react';
import { 
  VegetableIcon, 
  GrainIcon, 
  MeatFishIcon, 
  DairyEggIcon, 
  OilSpiceIcon, 
  AllStaplesIcon 
} from './media/CommodityIcon';

export const CATEGORIES = [
  { 
    id: 'all', 
    labelEn: 'All Items', 
    labelBn: 'সব পণ্য', 
    icon: AllStaplesIcon 
  },
  { 
    id: 'vegetables', 
    labelEn: 'Vegetables', 
    labelBn: 'শাকসবজি', 
    icon: VegetableIcon, 
    matchKeys: ['vegetable', 'potato', 'onion', 'chilli', 'garlic', 'সবজি', 'আলু', 'পেঁয়াজ', 'মরিচ'] 
  },
  { 
    id: 'grains', 
    labelEn: 'Grains & Pulses', 
    labelBn: 'চাল ও ডাল', 
    icon: GrainIcon, 
    matchKeys: ['grain', 'cereal', 'pulse', 'rice', 'dal', 'flour', 'চাল', 'ডাল', 'আটা'] 
  },
  { 
    id: 'protein', 
    labelEn: 'Meat & Fish', 
    labelBn: 'মাছ ও মাংস', 
    icon: MeatFishIcon, 
    matchKeys: ['meat', 'fish', 'poultry', 'chicken', 'beef', 'mutton', 'seafood', 'মাছ', 'মাংস', 'মুরগি', 'গরু'] 
  },
  { 
    id: 'dairy_eggs', 
    labelEn: 'Dairy & Eggs', 
    labelBn: 'ডিম ও দুধ', 
    icon: DairyEggIcon, 
    matchKeys: ['dairy', 'egg', 'milk', 'ডিম', 'দুধ'] 
  },
  { 
    id: 'spices_oils', 
    labelEn: 'Spices & Oils', 
    labelBn: 'তেল ও মসলা', 
    icon: OilSpiceIcon, 
    matchKeys: ['spice', 'oil', 'salt', 'sugar', 'mustard', 'তেল', 'মসলা', 'লবণ', 'চিনি'] 
  },
];

export function matchesCategory(item, categoryId) {
  if (!categoryId || categoryId === 'all') return true;
  const catObj = CATEGORIES.find((c) => c.id === categoryId);
  if (!catObj || !catObj.matchKeys) return true;

  const itemCategory = (item.category || '').toLowerCase();
  const itemName = (item.canonical_name || item.raw_name || '').toLowerCase();
  const banglaName = (item.bangla_name || '').toLowerCase();

  return catObj.matchKeys.some(
    (key) => itemCategory.includes(key) || itemName.includes(key) || banglaName.includes(key)
  );
}

export default function CategoryFilter({
  selectedCategory,
  onSelectCategory,
  itemsCountMap = {},
  lang = 'bn',
}) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none my-3 select-none">
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
                ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-950/20'
                : 'bg-white dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 shadow-sm'
            }`}
          >
            <IconComponent className={`w-4 h-4 flex-shrink-0 ${isSelected ? 'text-white' : 'text-slate-500 dark:text-slate-400'}`} />
            <span>{label}</span>
            {count !== undefined && (
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                  isSelected
                    ? 'bg-emerald-800/50 text-white'
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
