import React from 'react';
import { 
  Carrot, 
  Wheat, 
  Fish, 
  Egg, 
  Flame, 
  Droplet, 
  Leaf, 
  Layers 
} from 'lucide-react';

/**
 * Visual styling, icons, and accent borders tailored by commodity category.
 */
export const CATEGORY_THEMES = {
  'Vegetables': {
    label: 'Vegetables',
    icon: Leaf,
    borderAccent: 'border-l-emerald-500',
    tagClass: 'text-emerald-400 bg-emerald-950/40 border-emerald-500/30',
    hoverBorder: 'hover:border-emerald-500/40',
    glowColor: 'rgba(16, 185, 129, 0.15)',
    accentHex: '#10B981',
  },
  'Grains & Pulses': {
    label: 'Grains & Pulses',
    icon: Wheat,
    borderAccent: 'border-l-amber-500',
    tagClass: 'text-amber-400 bg-amber-950/40 border-amber-500/30',
    hoverBorder: 'hover:border-amber-500/40',
    glowColor: 'rgba(245, 158, 11, 0.15)',
    accentHex: '#F59E0B',
  },
  'Meat & Fish': {
    label: 'Meat & Fish',
    icon: Fish,
    borderAccent: 'border-l-rose-500',
    tagClass: 'text-rose-400 bg-rose-950/40 border-rose-500/30',
    hoverBorder: 'hover:border-rose-500/40',
    glowColor: 'rgba(244, 63, 94, 0.15)',
    accentHex: '#F43F5E',
  },
  'Dairy & Eggs': {
    label: 'Dairy & Eggs',
    icon: Egg,
    borderAccent: 'border-l-yellow-500',
    tagClass: 'text-yellow-400 bg-yellow-950/40 border-yellow-500/30',
    hoverBorder: 'hover:border-yellow-500/40',
    glowColor: 'rgba(234, 179, 8, 0.15)',
    accentHex: '#EAB308',
  },
  'Spices & Oils': {
    label: 'Spices & Oils',
    icon: Flame,
    borderAccent: 'border-l-orange-500',
    tagClass: 'text-orange-400 bg-orange-950/40 border-orange-500/30',
    hoverBorder: 'hover:border-orange-500/40',
    glowColor: 'rgba(249, 115, 22, 0.15)',
    accentHex: '#F97316',
  },
};

export const DEFAULT_CATEGORY_THEME = {
  label: 'Staple',
  icon: Layers,
  borderAccent: 'border-l-indigo-500',
  tagClass: 'text-indigo-400 bg-indigo-950/40 border-indigo-500/30',
  hoverBorder: 'hover:border-indigo-500/40',
  glowColor: 'rgba(99, 102, 241, 0.15)',
  accentHex: '#6366F1',
};

export function getCategoryTheme(category) {
  if (!category) return DEFAULT_CATEGORY_THEME;
  const match = Object.keys(CATEGORY_THEMES).find(
    (k) => k.toLowerCase() === category.trim().toLowerCase()
  );
  return match ? CATEGORY_THEMES[match] : DEFAULT_CATEGORY_THEME;
}
