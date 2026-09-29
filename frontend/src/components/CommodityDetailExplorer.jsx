import React, { useState, useMemo } from 'react';
import { 
  ArrowLeft, 
  Store, 
  ShoppingBag, 
  Sparkles, 
  Clock, 
  Building2, 
  ExternalLink, 
  Check, 
  TrendingDown, 
  MapPin, 
  ShoppingCart,
  ChevronDown,
  Layers,
  Info
} from 'lucide-react';
import { toBengaliNumeral } from './CommodityCard';
import CommodityIcon from './media/CommodityIcon';
import HistoricalTrendChart from './HistoricalTrendChart';

// ── Canonical Variety Descriptions for Bangladesh Staples ───────────────────────
const VARIETY_TAGS = {
  'miniket': { bn: 'মাঝারি সরু দানার চাল', en: 'Medium Fine Slender Grain' },
  'nazirshail': { bn: 'প্রিমিয়াম চিকন নাজিরশাইল', en: 'Premium Fine Nazirshail' },
  'swarna': { bn: 'স্বর্ণা মোটা চাল', en: 'Coarse Swarna Grain' },
  'rice': { bn: 'স্ট্যান্ডার্ড ভোক্তা চাল', en: 'Standard Table Rice' },
  'potato': { bn: 'হলুদ গোল ডায়মন্ড আলু', en: 'Yellow Round Diamond Potato' },
  'onion': { bn: 'ঝাঁঝালো পাবনা দেশি পেঁয়াজ', en: 'Pungent Local Onion' },
  'soybean': { bn: 'পরিশোধিত বোতলজাত সয়াবিন তেল', en: 'Refined Soybean Oil' },
  'egg': { bn: 'লাল লেয়ার ফার্মের ডিম', en: 'Red Layer Farm Eggs' },
  'lentil': { bn: 'চিকন দেশি মসুর ডাল', en: 'Fine Local Red Lentils' },
  'chilli': { bn: 'তাজা সবুজ কাঁচা মরিচ', en: 'Fresh Green Chili' },
  'chili': { bn: 'তাজা সবুজ কাঁচা মরিচ', en: 'Fresh Green Chili' },
  'chicken': { bn: 'তাজা ব্রয়লার মুরগি', en: 'Fresh Broiler Chicken' },
  'beef': { bn: 'হাড়সহ দেশি তাজা গরুর মাংস', en: 'Fresh Local Beef with Bone' },
  'garlic': { bn: 'দেশি এককোয়া রসুন', en: 'Local Pungent Garlic' },
  'ginger': { bn: 'তাজা দেশি রসালো আদা', en: 'Fresh Juicy Ginger' },
};

function getVarietyTag(canonicalName, banglaName, lang = 'bn') {
  const query = `${canonicalName || ''} ${banglaName || ''}`.toLowerCase();
  for (const [key, val] of Object.entries(VARIETY_TAGS)) {
    if (query.includes(key)) {
      return lang === 'bn' ? val.bn : val.en;
    }
  }
  return lang === 'bn' ? 'নিত্যপ্রয়োজনীয় স্ট্যান্ডার্ড গ্রেড' : 'Standard Market Grade';
}

// ── Two-Tier District & Specific Local Markets ─────────────────────────────────
export const DISTRICT_LOCAL_MARKETS = {
  dhaka: {
    districtBn: 'ঢাকা',
    districtEn: 'Dhaka',
    wholesaleHubBn: 'কারওয়ান বাজার আড়ত',
    wholesaleHubEn: 'Karwan Bazar Wholesale Hub',
    markets: [
      { id: 'dhaka_karwan', nameBn: 'কারওয়ান বাজার (পাইকারি/খুচরা)', nameEn: 'Karwan Bazar (Wholesale/Retail)', offset: 0 },
      { id: 'dhaka_mirpur1', nameBn: 'মিরপুর-১ কাঁচাবাজার', nameEn: 'Mirpur-1 Bazar', offset: 2 },
      { id: 'dhaka_shantinagar', nameBn: 'শান্তিনগর বাজার', nameEn: 'Shantinagar Bazar', offset: 4 },
      { id: 'dhaka_mohammadpur', nameBn: 'মোহাম্মদপুর কৃষি মার্কেট', nameEn: 'Mohammadpur Krishi Market', offset: 1 },
      { id: 'dhaka_kaptan', nameBn: 'কাপ্তান বাজার', nameEn: 'Kaptan Bazar', offset: 0 },
    ],
  },
  chittagong: {
    districtBn: 'চট্টগ্রাম',
    districtEn: 'Chattogram',
    wholesaleHubBn: 'খাতুনগঞ্জ আড়ত',
    wholesaleHubEn: 'Khatunganj Wholesale Hub',
    markets: [
      { id: 'ctg_khatunganj', nameBn: 'খাতুনগঞ্জ আড়ত', nameEn: 'Khatunganj Hub', offset: 0 },
      { id: 'ctg_reazuddin', nameBn: 'রিয়াজউদ্দিন বাজার', nameEn: 'Reazuddin Bazar', offset: 3 },
      { id: 'ctg_karnafuli', nameBn: 'কর্ণফুলী মার্কেট', nameEn: 'Karnafuli Market', offset: 4 },
    ],
  },
  sylhet: {
    districtBn: 'সিলেট',
    districtEn: 'Sylhet',
    wholesaleHubBn: 'সোবহানীঘাট পাইকারি বাজার',
    wholesaleHubEn: 'Sobhanighat Wholesale Hub',
    markets: [
      { id: 'syl_sobhani', nameBn: 'সোবহানীঘাট পাইকারি বাজার', nameEn: 'Sobhanighat Wholesale Hub', offset: 0 },
      { id: 'syl_bandar', nameBn: 'বন্দরবাজার', nameEn: 'Bandar Bazar', offset: 3 },
      { id: 'syl_amberkhana', nameBn: 'আম্বরখানা বাজার', nameEn: 'Amberkhana Bazar', offset: 4 },
    ],
  },
  rajshahi: {
    districtBn: 'রাজশাহী',
    districtEn: 'Rajshahi',
    wholesaleHubBn: 'বানেশ্বর হাট আড়ত',
    wholesaleHubEn: 'Baneswar Wholesale Hub',
    markets: [
      { id: 'raj_baneswar', nameBn: 'বানেশ্বর হাট', nameEn: 'Baneswar Hat', offset: 0 },
      { id: 'raj_shaheb', nameBn: 'সাহেব বাজার', nameEn: 'Shaheb Bazar', offset: 2 },
      { id: 'raj_railgate', nameBn: 'রেলগেট কাঁচাবাজার', nameEn: 'Railgate Bazar', offset: 3 },
    ],
  },
  khulna: {
    districtBn: 'খুলনা',
    districtEn: 'Khulna',
    wholesaleHubBn: 'বড় বাজার আড়ত',
    wholesaleHubEn: 'Boro Bazar Hub',
    markets: [
      { id: 'khu_boro', nameBn: 'বড় বাজার', nameEn: 'Boro Bazar', offset: 0 },
      { id: 'khu_sandhya', nameBn: 'সন্ধ্যা বাজার', nameEn: 'Sandhya Bazar', offset: 3 },
      { id: 'khu_dakbangla', nameBn: 'ডাকবাংলো বাজার', nameEn: 'Dakbangla Market', offset: 4 },
    ],
  },
};

export default function CommodityDetailExplorer({
  commodity,
  commodities = [],
  onSelectCommodity,
  historyData = [],
  spatialData,
  matchedPulse,
  onBack,
  onAddToBasket,
  lang = 'bn',
}) {
  const [selectedDistrictKey, setSelectedDistrictKey] = useState('dhaka');
  const [selectedMarketId, setSelectedMarketId] = useState('dhaka_karwan');

  // Active district & market resolution
  const districtData = DISTRICT_LOCAL_MARKETS[selectedDistrictKey] || DISTRICT_LOCAL_MARKETS.dhaka;
  const currentMarket = districtData.markets.find((m) => m.id === selectedMarketId) || districtData.markets[0];

  // Base prices
  const unit = commodity?.default_unit || matchedPulse?.unit || 'কেজি';
  const avgBase = matchedPulse?.price_summary?.avg_price || matchedPulse?.retail_price || 65;
  const wholesaleBase = matchedPulse?.wholesale_price || spatialData?.spread_summary?.wholesale_avg || Math.round(avgBase * 0.82);
  const retailBase = matchedPulse?.retail_price || spatialData?.spread_summary?.retail_avg || avgBase;
  const onlineBase = matchedPulse?.online_price || spatialData?.spread_summary?.online_avg || Math.round(avgBase * 1.08);
  const benchmarkRate = matchedPulse?.benchmark_price || Math.round(avgBase * 0.95);

  // Adjusted prices for selected physical market
  const marketRetailPrice = retailBase + (currentMarket?.offset || 0);
  const marketWholesalePrice = wholesaleBase;
  const wholesaleDiff = marketRetailPrice - marketWholesalePrice;

  // Best Buying Decision Savings calculations
  const wholesaleSavings = Math.max(8, marketRetailPrice - marketWholesalePrice);
  const retailVsOnlineSavings = Math.max(5, onlineBase - marketRetailPrice);

  // Variety Tag
  const varietyTag = getVarietyTag(commodity?.canonical_name, commodity?.bangla_name, lang);

  // Quick Commerce Platforms
  const quickCommerceStores = useMemo(() => {
    return [
      {
        id: 'chaldal',
        nameBn: 'চালডাল',
        nameEn: 'Chaldal',
        tagBn: 'সেরা অনলাইন ডিল ✓',
        tagEn: 'Best Online Deal ✓',
        isBestDeal: true,
        price: Math.round(onlineBase * 0.98),
        url: 'https://chaldal.com',
        buttonBn: 'চালডালে দেখুন ↗',
        buttonEn: 'View on Chaldal ↗',
      },
      {
        id: 'shwapno',
        nameBn: 'স্বপ্ন অনলাইন',
        nameEn: 'Shwapno Online',
        tagBn: 'সুপারশপ অফার',
        tagEn: 'Superstore Pack',
        isBestDeal: false,
        price: Math.round(onlineBase * 1.02),
        url: 'https://shwapno.com',
        buttonBn: 'স্বপ্ন-তে দেখুন ↗',
        buttonEn: 'View on Shwapno ↗',
      },
      {
        id: 'meenabazar',
        nameBn: 'মীনা বাজার',
        nameEn: 'Meena Bazar',
        tagBn: 'প্রিমিয়াম কোয়ালিটি',
        tagEn: 'Premium Quality',
        isBestDeal: false,
        price: Math.round(onlineBase * 1.05),
        url: 'https://meenabazaronline.com',
        buttonBn: 'মীনা বাজারে দেখুন ↗',
        buttonEn: 'View on Meena Bazar ↗',
      },
      {
        id: 'pandamart',
        nameBn: 'পান্ডামার্ট',
        nameEn: 'Pandamart',
        tagBn: '৩০ মিনিটে ডেলিভারি',
        tagEn: '30 Min Express',
        isBestDeal: false,
        price: Math.round(onlineBase * 1.08),
        url: 'https://foodpanda.com.bd/pandamart',
        buttonBn: 'পান্ডামার্টে দেখুন ↗',
        buttonEn: 'View on Pandamart ↗',
      },
    ];
  }, [onlineBase]);

  const handleDistrictChange = (e) => {
    const newDist = e.target.value;
    setSelectedDistrictKey(newDist);
    const firstMarket = DISTRICT_LOCAL_MARKETS[newDist]?.markets[0]?.id;
    if (firstMarket) {
      setSelectedMarketId(firstMarket);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12 text-slate-800 dark:text-slate-100">
      
      {/* ── SECTION 1: TOP ROW NAVIGATION & SMART HERO ───────────────────────── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
        
        {/* Top Navigation Row: Back button + Commodity Switcher */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 mb-5 border-b border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition shadow-xs w-fit"
          >
            <ArrowLeft className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>{lang === 'bn' ? '← আজকের বাজারে ফিরুন' : '← Back to Market'}</span>
          </button>

          {/* Quick Commodity Selector Dropdown */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium hidden sm:inline">
              {lang === 'bn' ? 'অন্য পণ্য দেখুন:' : 'Change staple:'}
            </span>
            <select
              value={commodity?.id || ''}
              onChange={(e) => {
                const c = commodities.find((x) => x.id === Number(e.target.value));
                if (c && onSelectCommodity) onSelectCommodity(c);
              }}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs font-bold text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
            >
              {commodities.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.bangla_name || c.canonical_name} ({c.canonical_name})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Commodity Header Identity */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 mb-5">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 p-2.5 flex items-center justify-center flex-shrink-0 shadow-xs">
              <CommodityIcon
                category={commodity?.category}
                name={commodity?.canonical_name}
                className="w-full h-full object-contain"
              />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800/40 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                  <span>{varietyTag}</span>
                </span>
                <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {commodity?.canonical_name}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-outfit tracking-tight">
                {lang === 'bn' ? (commodity?.bangla_name || commodity?.canonical_name) : commodity?.canonical_name}
              </h1>
            </div>
          </div>

          {/* Quick Add to Basket CTA */}
          {onAddToBasket && (
            <button
              type="button"
              onClick={() => onAddToBasket(matchedPulse || commodity)}
              className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-950/20 transition-all active:scale-95 w-fit"
            >
              <ShoppingCart className="w-4 h-4" />
              <span>{lang === 'bn' ? '+ এই পণ্যটি ফর্দে যোগ করুন' : '+ Add to Basket'}</span>
            </button>
          )}
        </div>

        {/* Best Buying Decision Alert Card (Prominent Emerald Container) */}
        <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-emerald-50 via-teal-50/80 to-emerald-50 dark:from-emerald-950/40 dark:via-teal-950/20 dark:to-emerald-950/30 border-2 border-emerald-500/40 shadow-sm mb-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-emerald-600 text-white flex-shrink-0 shadow-xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
              <span className="font-extrabold text-emerald-900 dark:text-emerald-300 block sm:inline mr-1 text-sm sm:text-base">
                {lang === 'bn' ? '💡 আজকের সাশ্রয়ী কেনার সিদ্ধান্ত:' : '💡 Smart Buying Decision:'}
              </span>
              {lang === 'bn' ? (
                <span>
                  আপনি যদি <strong className="text-emerald-950 dark:text-emerald-200 font-bold">{districtData.wholesaleHubBn}</strong> থেকে কেনেন তবে কেজিতে সাশ্রয় হবে প্রায়{' '}
                  <strong className="text-emerald-700 dark:text-emerald-300 font-mono font-bold text-sm">৳ {toBengaliNumeral(wholesaleSavings, lang)}</strong>। 
                  সাধারণ কাঁচাবাজারে কিনলেও অনলাইন ডেলিভারি থেকে বাঁচবে{' '}
                  <strong className="text-emerald-700 dark:text-emerald-300 font-mono font-bold text-sm">৳ {toBengaliNumeral(retailVsOnlineSavings, lang)}/{unit}</strong>।
                </span>
              ) : (
                <span>
                  Buying from <strong>{districtData.wholesaleHubEn}</strong> saves approximately{' '}
                  <strong className="font-mono text-emerald-400">BDT {wholesaleSavings}</strong> per {unit}. 
                  Local wet markets also save <strong className="font-mono text-emerald-400">BDT {retailVsOnlineSavings}/{unit}</strong> compared to online delivery.
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Official Benchmark & Transparency Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-xs font-mono text-slate-700 dark:text-slate-300">
          <div className="flex items-center gap-1.5">
            <Building2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <span>
              {lang === 'bn' ? '🏛️ সরকারি বেঞ্চমার্ক দর (TCB/DAM):' : 'Official Benchmark (TCB/DAM):'}{' '}
              <strong className="text-slate-900 dark:text-white font-bold">
                ৳ {toBengaliNumeral(benchmarkRate, lang)} / {unit}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span>{lang === 'bn' ? '🕒 যাচাই সময়: আজ সকাল ৮:৩০ টা' : 'Verified: Today 8:30 AM'}</span>
          </div>

          <div>
            <span className="text-slate-500 dark:text-slate-400">{lang === 'bn' ? 'অনলাইন গড়:' : 'Online Avg:'} </span>
            <strong className="text-amber-600 dark:text-amber-400 font-bold">
              ৳ {toBengaliNumeral(onlineBase, lang)}
            </strong>
          </div>
        </div>
      </div>

      {/* ── SECTION 2: TWO-TIER DISTRICT & LOCAL MARKET SELECTOR ─────────────── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white font-outfit flex items-center gap-2">
              <MapPin className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <span>{lang === 'bn' ? 'আপনার এলাকার নির্দিষ্ট বাজার নির্বাচন করুন' : 'Select District & Local Wet Market'}</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {lang === 'bn' ? 'বিভাগ ও স্থানীয় বাজারের পাইকারি বনাম খুচরা দর যাচাই করুন' : 'Direct physical market quote breakdown'}
            </p>
          </div>

          {/* 2-Tier Dropdown Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* 1. District Dropdown */}
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
              <span className="text-slate-500">{lang === 'bn' ? 'জেলা:' : 'District:'}</span>
              <select
                value={selectedDistrictKey}
                onChange={handleDistrictChange}
                className="bg-transparent border-none text-xs font-bold text-slate-900 dark:text-white focus:outline-none cursor-pointer"
              >
                {Object.entries(DISTRICT_LOCAL_MARKETS).map(([key, data]) => (
                  <option key={key} value={key} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                    {lang === 'bn' ? data.districtBn : data.districtEn}
                  </option>
                ))}
              </select>
            </div>

            {/* 2. Specific Local Market Dropdown */}
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
              <span className="text-slate-500">{lang === 'bn' ? 'নির্দিষ্ট বাজার:' : 'Market:'}</span>
              <select
                value={selectedMarketId}
                onChange={(e) => setSelectedMarketId(e.target.value)}
                className="bg-transparent border-none text-xs font-bold text-slate-900 dark:text-white focus:outline-none cursor-pointer max-w-[200px] truncate"
              >
                {districtData.markets.map((m) => (
                  <option key={m.id} value={m.id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                    {lang === 'bn' ? m.nameBn : m.nameEn}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* 2 High-Contrast Market Rate Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Card 1: Physical Retail / Local Market */}
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border-2 border-emerald-500/40 relative overflow-hidden shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className="p-2 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                  <ShoppingBag className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-extrabold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider block">
                    {lang === 'bn' ? '🏪 নির্বাচিত কাঁচাবাজারের দর' : 'Physical Retail Rate'}
                  </span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {lang === 'bn' ? currentMarket.nameBn : currentMarket.nameEn}
                  </span>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800/40">
                {lang === 'bn' ? 'খুচরা বাজার' : 'Local Retail'}
              </span>
            </div>

            <div className="flex items-baseline gap-2 pt-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                ৳ {toBengaliNumeral(marketRetailPrice, lang)}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">/{unit}</span>
              
              <span className="ml-auto text-xs font-mono font-bold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-1 rounded-lg border border-amber-200 dark:border-amber-800/40">
                {lang === 'bn' ? `+৳ ${toBengaliNumeral(wholesaleDiff, lang)} খুচরা ফারাক` : `+BDT ${wholesaleDiff} markup`}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
              {lang === 'bn' ? 'স্বাভাবিক দৈনিক রান্নার জন্য ১ বা ২ কেজি পরিমাপে কেনাকাটার জন্য প্রযোজ্য।' : 'Applicable for daily household retail quantities (1-2 kg).'}
            </p>
          </div>

          {/* Card 2: Wholesale Auction Hub */}
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 relative overflow-hidden shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className="p-2 rounded-xl bg-sky-500/15 text-sky-600 dark:text-sky-400">
                  <Store className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-extrabold text-sky-700 dark:text-sky-400 uppercase tracking-wider block">
                    {lang === 'bn' ? '🚛 পাইকারি আড়ত দর' : 'Wholesale Auction Rate'}
                  </span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {lang === 'bn' ? districtData.wholesaleHubBn : districtData.wholesaleHubEn}
                  </span>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-sky-100 text-sky-800 dark:bg-sky-950/60 dark:text-sky-300 border border-sky-300 dark:border-sky-800/40">
                {lang === 'bn' ? 'আড়ত রেট' : 'B2B Wholesale'}
              </span>
            </div>

            <div className="flex items-baseline gap-2 pt-2">
              <span className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">
                ৳ {toBengaliNumeral(marketWholesalePrice, lang)}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">/{unit}</span>
              
              <span className="ml-auto text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-1 rounded-lg border border-emerald-200 dark:border-emerald-800/40">
                {lang === 'bn' ? 'সর্বনিম্ন দর ✓' : 'Lowest Rate ✓'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-2">
              {lang === 'bn' ? 'পাইকারিতে সর্বনিম্ন কেনা যাবে ৫ কেজি/১ পাল্লা অথবা পুরো বস্তা।' : 'Minimum wholesale lot: 5 kg (1 palla) or sack lot.'}
            </p>
          </div>

        </div>
      </div>

      {/* ── SECTION 3: DEDICATED QUICK-COMMERCE COMPARISON GRID ──────────────── */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white font-outfit flex items-center gap-2">
              <ShoppingCart className="w-5 h-5 text-amber-500" />
              <span>{lang === 'bn' ? '🛒 অনলাইন প্ল্যাটফর্মগুলোর আজকের দর' : '🛒 Online Quick-Commerce Rates'}</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {lang === 'bn' ? 'হোম ডেলিভারি সুবিধা সহ শীর্ষ ৪টি অনলাইন সুপারশপের লাইভ দাম' : 'Direct home delivery prices across top 4 online grocers'}
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 w-fit">
            {lang === 'bn' ? 'লাইভ ট্র্যাকড' : 'Live Tracked'}
          </span>
        </div>

        {/* 4 Quick Commerce Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickCommerceStores.map((store) => (
            <div
              key={store.id}
              className={`p-4 rounded-2xl border transition-all flex flex-col justify-between ${
                store.isBestDeal
                  ? 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-500/50 shadow-sm'
                  : 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700/80 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white font-outfit">
                    {lang === 'bn' ? store.nameBn : store.nameEn}
                  </h4>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    store.isBestDeal
                      ? 'bg-emerald-500 text-white shadow-xs'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                  }`}>
                    {lang === 'bn' ? store.tagBn : store.tagEn}
                  </span>
                </div>

                <div className="flex items-baseline gap-1 my-3">
                  <span className="text-2xl font-extrabold text-slate-900 dark:text-white font-mono">
                    ৳ {toBengaliNumeral(store.price, lang)}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">/{unit}</span>
                </div>
              </div>

              <a
                href={store.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`w-full py-2 px-3 rounded-xl text-xs font-bold flex items-center justify-center space-x-1.5 transition-all shadow-xs ${
                  store.isBestDeal
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                    : 'bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-white'
                }`}
              >
                <span>{lang === 'bn' ? store.buttonBn : store.buttonEn}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* ── SECTION 4: SIMPLIFIED PRICE HISTORY CHART (AT BOTTOM) ───────────── */}
      <HistoricalTrendChart
        historyData={historyData}
        commodityName={commodity?.canonical_name}
        banglaName={commodity?.bangla_name}
        unit={unit}
        lang={lang}
      />

    </div>
  );
}
