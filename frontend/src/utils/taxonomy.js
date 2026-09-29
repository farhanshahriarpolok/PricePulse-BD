/**
 * Canonical Commodity Category Taxonomy System
 * Strictly maps all 35 commodities into 5 standard bazaar categories:
 * 1. vegetables ➔ শাকসবজি
 * 2. grains_pulses ➔ চাল ও ডাল
 * 3. meat_fish ➔ মাছ ও মাংস
 * 4. eggs_dairy ➔ ডিম ও দুধ
 * 5. oils_spices ➔ তেল ও মসলা
 */

export const CANONICAL_CATEGORY_MAP = {
  // 1. vegetables ➔ শাকসবজি
  'Vegetables': 'vegetables',
  'vegetables': 'vegetables',
  'vegetable': 'vegetables',

  // 2. grains_pulses ➔ চাল ও ডাল
  'Grains': 'grains_pulses',
  'grains': 'grains_pulses',
  'Pulses': 'grains_pulses',
  'pulses': 'grains_pulses',
  'grains_pulses': 'grains_pulses',

  // 3. meat_fish (combining meat_poultry and fish_seafood) ➔ মাছ ও মাংস
  'Meat & Poultry': 'meat_fish',
  'meat & poultry': 'meat_fish',
  'Fish & Seafood': 'meat_fish',
  'fish & seafood': 'meat_fish',
  'meat_fish': 'meat_fish',

  // 4. eggs_dairy ➔ ডিম ও দুধ
  'Eggs & Dairy': 'eggs_dairy',
  'eggs & dairy': 'eggs_dairy',
  'Dairy': 'eggs_dairy',
  'dairy': 'eggs_dairy',
  'eggs_dairy': 'eggs_dairy',

  // 5. oils_spices ➔ তেল ও মসলা
  'Edible Oils': 'oils_spices',
  'edible oils': 'oils_spices',
  'Spices': 'oils_spices',
  'spices': 'oils_spices',
  'Sweeteners': 'oils_spices',
  'sweeteners': 'oils_spices',
  'Condiments': 'oils_spices',
  'condiments': 'oils_spices',
  'oils_spices': 'oils_spices',
};

// Strict explicit mapping by canonical commodity name to guarantee zero false matches
export const COMMODITY_CANONICAL_CATEGORY = {
  'Onion (Local)': 'vegetables',
  'Onion (Imported)': 'vegetables',
  'Potato (Diamond)': 'vegetables',
  'Green Chilli': 'vegetables',
  'Brinjal (Eggplant)': 'vegetables',
  'Tomato': 'vegetables',
  'Papaya (Green)': 'vegetables',
  'Cucumber': 'vegetables',
  'Carrot': 'vegetables',
  'Ginger (Local)': 'vegetables',

  'Rice (Miniket)': 'grains_pulses',
  'Rice (Nazirshail)': 'grains_pulses',
  'Rice (Coarse)': 'grains_pulses',
  'Atta (Packaged)': 'grains_pulses',
  'Maida (Packaged)': 'grains_pulses',
  'Masur Dal (Medium)': 'grains_pulses',
  'Masur Dal (Fine)': 'grains_pulses',

  'Broiler Chicken': 'meat_fish',
  'Deshi Chicken': 'meat_fish',
  'Beef (Local with Bone)': 'meat_fish',
  'Mutton (Goat Meat)': 'meat_fish',
  'Rui Fish (Fresh)': 'meat_fish',
  'Pangas Fish (Farm)': 'meat_fish',
  'Hilsa Fish (Medium)': 'meat_fish',
  'Tilapia Fish': 'meat_fish',

  'Farm Egg': 'eggs_dairy',
  'Pasteurized Cow Milk': 'eggs_dairy',

  'Soybean Oil (Bottled)': 'oils_spices',
  'Soybean Oil (Loose)': 'oils_spices',
  'Mustard Oil': 'oils_spices',
  'Sugar (Refined White)': 'oils_spices',
  'Salt (Iodized)': 'oils_spices',
  'Garlic (Local)': 'oils_spices',
  'Dry Red Chilli': 'oils_spices',
  'Turmeric Powder': 'oils_spices',
};

export function getCommodityCanonicalCategory(item) {
  if (!item) return 'all';
  const name = item.canonical_name || item.raw_name || '';
  if (COMMODITY_CANONICAL_CATEGORY[name]) {
    return COMMODITY_CANONICAL_CATEGORY[name];
  }
  const cat = item.category || '';
  if (CANONICAL_CATEGORY_MAP[cat]) {
    return CANONICAL_CATEGORY_MAP[cat];
  }
  const lowerCat = cat.toLowerCase();
  for (const [key, val] of Object.entries(CANONICAL_CATEGORY_MAP)) {
    if (lowerCat === key.toLowerCase()) return val;
  }
  return 'vegetables';
}
