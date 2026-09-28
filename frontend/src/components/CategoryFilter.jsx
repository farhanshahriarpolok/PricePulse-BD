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
  { id: 'all', label: 'All Items', icon: AllStaplesIcon },
  { id: 'grains', label: 'Grains & Pulses', icon: GrainIcon, matchKeys: ['grain', 'cereal', 'pulse', 'rice', 'dal', 'flour'] },
  { id: 'vegetables', label: 'Vegetables', icon: VegetableIcon, matchKeys: ['vegetable', 'potato', 'onion', 'chilli', 'garlic'] },
  { id: 'protein', label: 'Meat & Fish', icon: MeatFishIcon, matchKeys: ['meat', 'fish', 'poultry', 'chicken', 'beef', 'mutton', 'seafood'] },
  { id: 'dairy_eggs', label: 'Dairy & Eggs', icon: DairyEggIcon, matchKeys: ['dairy', 'egg', 'milk'] },
  { id: 'spices_oils', label: 'Spices & Oils', icon: OilSpiceIcon, matchKeys: ['spice', 'oil', 'salt', 'sugar', 'mustard'] },
];

export function matchesCategory(item, categoryId) {
  if (!categoryId || categoryId === 'all') return true;
  const catObj = CATEGORIES.find((c) => c.id === categoryId);
  if (!catObj || !catObj.matchKeys) return true;

  const itemCategory = (item.category || '').toLowerCase();
  const itemName = (item.canonical_name || item.raw_name || '').toLowerCase();

  return catObj.matchKeys.some(
    (key) => itemCategory.includes(key) || itemName.includes(key)
  );
}

export default function CategoryFilter({
  selectedCategory,
  onSelectCategory,
  itemsCountMap = {},
}) {
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none my-4">
      {CATEGORIES.map((cat) => {
        const IconComponent = cat.icon;
        const isSelected = selectedCategory === cat.id;
        const count = itemsCountMap[cat.id];

        return (
          <button
            key={cat.id}
            onClick={() => onSelectCategory(cat.id)}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all border ${
              isSelected
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50 shadow-sm shadow-emerald-950/20'
                : 'bg-slate-800/60 text-slate-300 border-slate-700 hover:bg-slate-800 hover:border-slate-600'
            }`}
          >
            <IconComponent className="w-4 h-4 flex-shrink-0" />
            <span>{cat.label}</span>
            {count !== undefined && (
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  isSelected
                    ? 'bg-emerald-500/30 text-emerald-200'
                    : 'bg-slate-700/60 text-slate-400'
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
