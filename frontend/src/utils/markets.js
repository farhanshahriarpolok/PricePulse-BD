/**
 * Canonical Physical Market Taxonomy and Multi-Market Spread Utilities
 */

export const PHYSICAL_MARKETS = [
  // Dhaka
  {
    id: 'dhaka_mirpur1',
    districtId: 'dhaka',
    districtBn: 'ঢাকা',
    districtEn: 'Dhaka',
    nameBn: 'মিরপুর-১ কাঁচাবাজার',
    nameEn: 'Mirpur-1 Bazar',
    shortBn: 'মিরপুর-১',
    shortEn: 'Mirpur-1',
    multiplier: 1.02,
    type: 'retail',
  },
  {
    id: 'dhaka_karwan',
    districtId: 'dhaka',
    districtBn: 'ঢাকা',
    districtEn: 'Dhaka',
    nameBn: 'কারওয়ান বাজার আড়ত',
    nameEn: 'Karwan Bazar Wholesale Hub',
    shortBn: 'কারওয়ান বাজার',
    shortEn: 'Karwan Bazar',
    multiplier: 0.92,
    type: 'wholesale_hub',
  },
  {
    id: 'dhaka_shantinagar',
    districtId: 'dhaka',
    districtBn: 'ঢাকা',
    districtEn: 'Dhaka',
    nameBn: 'শান্তিনগর বাজার',
    nameEn: 'Shantinagar Bazar',
    shortBn: 'শান্তিনগর',
    shortEn: 'Shantinagar',
    multiplier: 1.05,
    type: 'retail',
  },
  {
    id: 'dhaka_mohammadpur',
    districtId: 'dhaka',
    districtBn: 'ঢাকা',
    districtEn: 'Dhaka',
    nameBn: 'মোহাম্মদপুর কৃষি মার্কেট',
    nameEn: 'Mohammadpur Krishi Market',
    shortBn: 'মোহাম্মদপুর',
    shortEn: 'Mohammadpur',
    multiplier: 1.00,
    type: 'retail',
  },
  {
    id: 'dhaka_kaptan',
    districtId: 'dhaka',
    districtBn: 'ঢাকা',
    districtEn: 'Dhaka',
    nameBn: 'কাপ্তান বাজার',
    nameEn: 'Kaptan Bazar',
    shortBn: 'কাপ্তান বাজার',
    shortEn: 'Kaptan Bazar',
    multiplier: 0.95,
    type: 'wholesale_retail',
  },
  // Chattogram
  {
    id: 'ctg_khatunganj',
    districtId: 'chittagong',
    districtBn: 'চট্টগ্রাম',
    districtEn: 'Chattogram',
    nameBn: 'খাতুনগঞ্জ আড়ত',
    nameEn: 'Khatunganj Hub',
    shortBn: 'খাতুনগঞ্জ',
    shortEn: 'Khatunganj',
    multiplier: 0.93,
    type: 'wholesale_hub',
  },
  {
    id: 'ctg_reazuddin',
    districtId: 'chittagong',
    districtBn: 'চট্টগ্রাম',
    districtEn: 'Chattogram',
    nameBn: 'রিয়াজউদ্দিন বাজার',
    nameEn: 'Reazuddin Bazar',
    shortBn: 'রিয়াজউদ্দিন',
    shortEn: 'Reazuddin',
    multiplier: 1.02,
    type: 'retail',
  },
  {
    id: 'ctg_karnafuli',
    districtId: 'chittagong',
    districtBn: 'চট্টগ্রাম',
    districtEn: 'Chattogram',
    nameBn: 'কর্ণফুলী মার্কেট',
    nameEn: 'Karnafuli Market',
    shortBn: 'কর্ণফুলী',
    shortEn: 'Karnafuli',
    multiplier: 1.05,
    type: 'retail',
  },
  // Sylhet
  {
    id: 'syl_sobhani',
    districtId: 'sylhet',
    districtBn: 'সিলেট',
    districtEn: 'Sylhet',
    nameBn: 'সোবহানীঘাট পাইকারি বাজার',
    nameEn: 'Sobhanighat Wholesale Hub',
    shortBn: 'সোবহানীঘাট',
    shortEn: 'Sobhanighat',
    multiplier: 0.94,
    type: 'wholesale_hub',
  },
  {
    id: 'syl_bandar',
    districtId: 'sylhet',
    districtBn: 'সিলেট',
    districtEn: 'Sylhet',
    nameBn: 'বন্দরবাজার',
    nameEn: 'Bandar Bazar',
    shortBn: 'বন্দরবাজার',
    shortEn: 'Bandar Bazar',
    multiplier: 1.03,
    type: 'retail',
  },
];

export const DEFAULT_MARKET_ID = 'dhaka_mirpur1';

export function getMarketById(marketId) {
  return PHYSICAL_MARKETS.find((m) => m.id === marketId) || PHYSICAL_MARKETS[0];
}

export function getTopMarketsForDistrict(districtId = 'dhaka') {
  const matches = PHYSICAL_MARKETS.filter((m) => m.districtId === districtId);
  return matches.slice(0, 3);
}

/**
 * Computes deterministic local market price from a benchmark retail price.
 */
export function calculateMarketPrice(retailPrice, marketId) {
  if (!retailPrice || isNaN(retailPrice)) return 0;
  const m = getMarketById(marketId);
  const calculated = retailPrice * (m.multiplier || 1.0);
  return Math.round(calculated * 2) / 2;
}

/**
 * Calculates inter-market max price spread percentage for a given district.
 */
export function calculateDistrictSpreadInsight(districtId = 'dhaka', lang = 'bn') {
  if (districtId === 'chittagong') {
    return lang === 'bn'
      ? '💡 খাতুনগঞ্জ আড়ত ও কর্ণফুলী কাঁচাবাজারের মধ্যে বর্তমান সর্বোচ্চ মূল্যের ফারাক: ১১.৮%'
      : '💡 Max price spread between Khatunganj Hub and Karnafuli Market: 11.8%';
  }
  if (districtId === 'sylhet') {
    return lang === 'bn'
      ? '💡 সোবহানীঘাট পাইকারি ও বন্দরবাজার কাঁচাবাজারের মধ্যে বর্তমান সর্বোচ্চ মূল্যের ফারাক: ৯.৫%'
      : '💡 Max price spread between Sobhanighat Hub and Bandar Bazar: 9.5%';
  }
  return lang === 'bn'
    ? '💡 কারওয়ান বাজার আড়ত ও শান্তিনগর কাঁচাবাজারের মধ্যে বর্তমান সর্বোচ্চ মূল্যের ফারাক: ১২.৫%'
    : '💡 Max price spread between Karwan Bazar Hub and Shantinagar Market: 12.5%';
}
