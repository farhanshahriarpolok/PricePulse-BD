/**
 * Canonical Commodity Category Taxonomy System
 * Strictly maps all 35 commodities into 5 standard bazaar categories:
 * 1. vegetables ➔ শাকসবজি (10 items)
 * 2. grains_pulses ➔ চাল ও ডাল (7 items)
 * 3. meat_fish ➔ মাছ ও মাংস (8 items)
 * 4. eggs_dairy ➔ ডিম ও দুধ (2 items: Farm Egg, Pasteurized Cow Milk)
 * 5. oils_spices ➔ তেল ও মসলা (8 items)
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
  // Vegetables (10)
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

  // Grains & Pulses (7)
  'Rice (Miniket)': 'grains_pulses',
  'Rice (Nazirshail)': 'grains_pulses',
  'Rice (Coarse)': 'grains_pulses',
  'Atta (Packaged)': 'grains_pulses',
  'Maida (Packaged)': 'grains_pulses',
  'Masur Dal (Medium)': 'grains_pulses',
  'Masur Dal (Fine)': 'grains_pulses',

  // Meat & Fish (8)
  'Broiler Chicken': 'meat_fish',
  'Deshi Chicken': 'meat_fish',
  'Beef (Local with Bone)': 'meat_fish',
  'Mutton (Goat Meat)': 'meat_fish',
  'Rui Fish (Fresh)': 'meat_fish',
  'Pangas Fish (Farm)': 'meat_fish',
  'Hilsa Fish (Medium)': 'meat_fish',
  'Tilapia Fish': 'meat_fish',

  // Eggs & Dairy (Strictly 2)
  'Farm Egg': 'eggs_dairy',
  'Pasteurized Cow Milk': 'eggs_dairy',

  // Oils & Spices (8)
  'Soybean Oil (Bottled)': 'oils_spices',
  'Soybean Oil (Loose)': 'oils_spices',
  'Mustard Oil': 'oils_spices',
  'Sugar (Refined White)': 'oils_spices',
  'Salt (Iodized)': 'oils_spices',
  'Garlic (Local)': 'oils_spices',
  'Dry Red Chilli': 'oils_spices',
  'Turmeric Powder': 'oils_spices',
};

// Bangla Name Direct Mapping
export const BANGLA_NAME_CATEGORY_MAP = {
  'দেশি পেঁয়াজ': 'vegetables',
  'আমদানি পেঁয়াজ': 'vegetables',
  'ডায়মন্ড আলু': 'vegetables',
  'গোল আলু': 'vegetables',
  'কাঁচা মরিচ': 'vegetables',
  'বেগুন': 'vegetables',
  'গোল বেগুন': 'vegetables',
  'লম্বা বেগুন': 'vegetables',
  'টমেটো': 'vegetables',
  'পাকা টমেটো': 'vegetables',
  'কাঁচা পেঁপে': 'vegetables',
  'শসা': 'vegetables',
  'দেশি শসা': 'vegetables',
  'গাজর': 'vegetables',
  'দেশি আদা': 'vegetables',
  'আদা': 'vegetables',

  'মিনিকেট চাল': 'grains_pulses',
  'নাজিরশাইল চাল': 'grains_pulses',
  'মোটা চাল': 'grains_pulses',
  'প্যাকেট আটা': 'grains_pulses',
  'প্যাকেট ময়দা': 'grains_pulses',
  'মসুর ডাল (মাঝারি)': 'grains_pulses',
  'মসুর ডাল (চিকন)': 'grains_pulses',
  'মসুর ডাল': 'grains_pulses',

  'ব্রয়লার মুরগি': 'meat_fish',
  'দেশি মুরগি': 'meat_fish',
  'গরুর মাংস (হাড়সহ)': 'meat_fish',
  'গরুর মাংস': 'meat_fish',
  'খাসির মাংস': 'meat_fish',
  'রুই মাছ': 'meat_fish',
  'পাঙ্গাস মাছ': 'meat_fish',
  'ইলিশ মাছ': 'meat_fish',
  'তেলাপিয়া মাছ': 'meat_fish',

  'ফার্মের ডিম': 'eggs_dairy',
  'ডিম': 'eggs_dairy',
  'প্যাকেটজাত তরল দুধ': 'eggs_dairy',
  'তরল দুধ': 'eggs_dairy',

  'বোতলজাত সয়াবিন তেল': 'oils_spices',
  'খোলা সয়াবিন তেল': 'oils_spices',
  'সরিষার তেল': 'oils_spices',
  'চিনি (সাদা পরিশোধিত)': 'oils_spices',
  'সাদা চিনি': 'oils_spices',
  'আয়োডিনযুক্ত লবণ': 'oils_spices',
  'দেশি রসুন': 'oils_spices',
  'রসুন': 'oils_spices',
  'শুকনা মরিচ': 'oils_spices',
  'হলুদ গুঁড়া': 'oils_spices',
};

export function getCommodityCanonicalCategory(item) {
  if (!item) return 'all';

  // 1. Direct canonical name lookup
  const canonical = item.canonical_name || item.name || item.commodity_name || '';
  if (COMMODITY_CANONICAL_CATEGORY[canonical]) {
    return COMMODITY_CANONICAL_CATEGORY[canonical];
  }

  // 2. Direct bangla name lookup
  const bn = item.bangla_name || item.bnName || '';
  if (BANGLA_NAME_CATEGORY_MAP[bn]) {
    return BANGLA_NAME_CATEGORY_MAP[bn];
  }

  // 3. Normalized string lookup
  for (const [key, val] of Object.entries(COMMODITY_CANONICAL_CATEGORY)) {
    if (canonical.toLowerCase() === key.toLowerCase()) {
      return val;
    }
  }

  // 4. Fallback to category field if defined in taxonomy
  const cat = item.category || '';
  if (CANONICAL_CATEGORY_MAP[cat]) {
    return CANONICAL_CATEGORY_MAP[cat];
  }

  const lowerCat = cat.toLowerCase();
  for (const [key, val] of Object.entries(CANONICAL_CATEGORY_MAP)) {
    if (lowerCat === key.toLowerCase()) return val;
  }

  // Default safely to vegetables
  return 'vegetables';
}
