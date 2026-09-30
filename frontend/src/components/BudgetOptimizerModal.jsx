import React, { useState, useMemo } from 'react';
import { 
  Sparkles, 
  X, 
  Users, 
  Wallet, 
  ShoppingBasket, 
  Check, 
  ArrowRight,
  TrendingDown,
  Info
} from 'lucide-react';
import { toBengaliNumeral } from './CommodityCard';

// Core essential staples model for Bangladesh households
const ESSENTIAL_STAPLES = [
  { name: 'Miniket Rice', bnName: 'মিনিকেট চাল', unit: 'kg', baseRate: 72, defaultSmallQty: 5, defaultMedQty: 8 },
  { name: 'Red Lentils (Mosur)', bnName: 'দেশি মসুর ডাল', unit: 'kg', baseRate: 135, defaultSmallQty: 1, defaultMedQty: 1.5 },
  { name: 'Soybean Oil', bnName: 'বোতলজাত সয়াবিন তেল', unit: 'liter', baseRate: 170, defaultSmallQty: 2, defaultMedQty: 3 },
  { name: 'Diamond Potato', bnName: 'ডায়মন্ড আলু', unit: 'kg', baseRate: 45, defaultSmallQty: 3, defaultMedQty: 5 },
  { name: 'Local Onion', bnName: 'দেশি পেঁয়াজ', unit: 'kg', baseRate: 95, defaultSmallQty: 2, defaultMedQty: 3 },
  { name: 'Farm Eggs', bnName: 'ফার্মের ডিম', unit: 'হালি', baseRate: 48, defaultSmallQty: 3, defaultMedQty: 5 },
  { name: 'Green Chili', bnName: 'কাঁচা মরিচ', unit: 'g', baseRate: 0.18, defaultSmallQty: 250, defaultMedQty: 500 },
];

export default function BudgetOptimizerModal({
  isOpen,
  onClose,
  commodities = [],
  onApplyBasket,
  lang = 'bn'
}) {
  const [familySize, setFamilySize] = useState('small'); // 'small' (2-3) or 'medium' (4-5)
  const [budget, setBudget] = useState(1500);
  const [applied, setApplied] = useState(false);

  // Map commodities rates dynamically if available in DB
  const { optimizedItems, totalCalculated, isInfeasible, minRequiredCost } = useMemo(() => {
    // Determine minimum and baseline requirements
    const unscaledList = ESSENTIAL_STAPLES.map((staple) => {
      const match = commodities.find(
        (c) => c.canonical_name?.toLowerCase().includes(staple.name.toLowerCase()) ||
               c.bangla_name?.includes(staple.bnName)
      );
      const rate = match?.price_summary?.avg_price || match?.retail_avg || staple.baseRate;
      const baseQty = familySize === 'small' ? staple.defaultSmallQty : staple.defaultMedQty;
      const minQty = staple.unit === 'হালি' ? 1 : staple.unit === 'g' ? 100 : staple.unit === 'liter' ? 1 : 1;
      return {
        commodity_id: match?.id || null,
        name: staple.name,
        bnName: staple.bnName,
        unit: staple.unit,
        rate,
        baseQty,
        minQty,
        minCost: rate * minQty,
        cost: rate * baseQty,
      };
    });

    const minRequired = unscaledList.reduce((sum, item) => sum + item.minCost, 0);
    if (budget < minRequired) {
      return {
        optimizedItems: [],
        totalCalculated: 0,
        isInfeasible: true,
        minRequiredCost: Math.round(minRequired),
      };
    }

    const totalUnscaled = unscaledList.reduce((sum, item) => sum + item.cost, 0);
    let scalingFactor = budget / totalUnscaled;

    // Iteratively ensure we NEVER exceed budget
    let items = unscaledList.map((item, idx) => {
      let qty = item.baseQty * scalingFactor;
      if (item.unit === 'kg' || item.unit === 'liter') {
        qty = Math.max(item.minQty, Math.floor(qty * 2) / 2); // round down to nearest 0.5 to avoid budget overrun
      } else if (item.unit === 'হালি') {
        qty = Math.max(item.minQty, Math.floor(qty));
      } else if (item.unit === 'g') {
        qty = Math.max(item.minQty, Math.floor(qty / 50) * 50);
      }
      return {
        ...item,
        id: `opt-${idx}`,
        quantity: qty,
        totalCost: Math.round(qty * item.rate),
      };
    });

    let currentTotal = items.reduce((acc, it) => acc + it.totalCost, 0);
    // If rounding slightly exceeded budget, decrement highest cost item safely
    while (currentTotal > budget) {
      const candidates = items.filter((it) => it.quantity > it.minQty);
      if (candidates.length === 0) break;
      const highest = candidates.reduce((prev, curr) => (curr.totalCost > prev.totalCost ? curr : prev));
      if (highest.unit === 'kg' || highest.unit === 'liter') highest.quantity -= 0.5;
      else if (highest.unit === 'হালি') highest.quantity -= 1;
      else if (highest.unit === 'g') highest.quantity -= 50;
      highest.totalCost = Math.round(highest.quantity * highest.rate);
      currentTotal = items.reduce((acc, it) => acc + it.totalCost, 0);
    }

    return {
      optimizedItems: items,
      totalCalculated: currentTotal,
      isInfeasible: false,
      minRequiredCost: Math.round(minRequired),
    };
  }, [familySize, budget, commodities]);

  const budgetRemaining = Math.max(0, budget - totalCalculated);

  if (!isOpen) return null;

  const handleApply = () => {
    setApplied(true);
    if (onApplyBasket) {
      onApplyBasket(optimizedItems);
    }
    setTimeout(() => {
      setApplied(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
      <div 
        className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center border border-emerald-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-outfit">
                {lang === 'bn' ? 'পারিবারিক সাপ্তাহিক বাজার বাজেট অপ্টিমাইজার' : 'Family Weekly Budget Optimizer'}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {lang === 'bn' ? 'আপনার বাজেটের সর্বোচ্চ ব্যবহারে সেরা পুষ্টিকর নিত্যপণ্য ফর্দ' : 'Smart basket allocation maximizing nutrition within your weekly budget'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Controls Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 text-slate-800 dark:text-slate-200">
          {/* 1. Family Size Selection */}
          <div>
            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block mb-2">
              {lang === 'bn' ? '১. পরিবারের সদস্য সংখ্যা' : '1. Family Size'}
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setFamilySize('small')}
                className={`flex items-center space-x-3 p-3 rounded-xl border text-left transition-all ${
                  familySize === 'small'
                    ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-300 ring-2 ring-emerald-500/30'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300 hover:border-slate-300'
                }`}
              >
                <Users className="w-5 h-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <div className="text-xs font-bold">{lang === 'bn' ? 'ছোট পরিবার (২-৩ জন)' : 'Small Family (2-3 Members)'}</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">{lang === 'bn' ? 'সাপ্তাহিক মৌলিক চাহিদা' : 'Standard weekly baseline'}</div>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setFamilySize('medium')}
                className={`flex items-center space-x-3 p-3 rounded-xl border text-left transition-all ${
                  familySize === 'medium'
                    ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-300 ring-2 ring-emerald-500/30'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300 hover:border-slate-300'
                }`}
              >
                <Users className="w-5 h-5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <div className="text-xs font-bold">{lang === 'bn' ? 'মাঝারি পরিবার (৪-৫ জন)' : 'Medium Family (4-5 Members)'}</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400">{lang === 'bn' ? 'পূর্ণাঙ্গ পারিবারিক বরাদ্দ' : 'Scaled staple volume'}</div>
                </div>
              </button>
            </div>
          </div>

          {/* 2. Budget Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                {lang === 'bn' ? '২. আপনার সাপ্তাহিক বাজেট (টাকা)' : '2. Weekly Budget (BDT)'}
              </label>
              <span className="text-sm font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                ৳ {toBengaliNumeral(budget, lang)}
              </span>
            </div>

            {/* Quick Preset Pills */}
            <div className="flex flex-wrap gap-2 mb-3">
              {[1000, 1500, 2000, 2500, 3000].map((amount) => (
                <button
                  key={amount}
                  type="button"
                  onClick={() => setBudget(amount)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-mono transition-all border ${
                    budget === amount
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200'
                  }`}
                >
                  ৳ {toBengaliNumeral(amount, lang)}
                </button>
              ))}
            </div>

            <div className="relative">
              <input
                type="number"
                min="500"
                max="10000"
                step="100"
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value) || 500)}
                className="w-full bg-slate-50 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-2.5 text-sm font-mono font-bold text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
              />
              <span className="absolute right-4 top-2.5 text-xs text-slate-400 font-medium">BDT</span>
            </div>
          </div>

          {/* 3. Generated Balanced Basket Preview */}
          {isInfeasible ? (
            <div className="border border-amber-300 dark:border-amber-800/60 rounded-xl p-4 bg-amber-50/60 dark:bg-amber-950/20 text-center space-y-2">
              <span className="text-amber-700 dark:text-amber-400 font-bold text-sm block">
                {lang === 'bn' ? '⚠️ বাজেট অপর্যাপ্ত' : '⚠️ Insufficient Budget'}
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {lang === 'bn'
                  ? `ন্যূনতম ১ কেজি/প্যাক হিসেবে ৭টি মৌলিক পণ্য কেনার জন্য কমপক্ষে ৳ ${toBengaliNumeral(minRequiredCost, lang)} প্রয়োজন। অনুগ্রহ করে বাজেট বাড়িয়ে চেষ্টা করুন।`
                  : `Minimum ৳ ${minRequiredCost} is required to cover baseline minimum pack units across all essential staples. Please increase your budget.`}
              </p>
            </div>
          ) : (
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-slate-50/50 dark:bg-slate-800/30">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  {lang === 'bn' ? 'সুপারিশকৃত অপ্টিমাইজড ফর্দ:' : 'Optimized Essential Breakdown:'}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {optimizedItems.length} {lang === 'bn' ? 'টি মূল পণ্য' : 'Staples'}
                </span>
              </div>

              <div className="divide-y divide-slate-200 dark:divide-slate-800/80 text-xs">
                {optimizedItems.map((item) => (
                  <div key={item.id} className="py-2 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      <span className="font-medium text-slate-800 dark:text-slate-200">
                        {lang === 'bn' ? item.bnName : item.name}
                      </span>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                        ({toBengaliNumeral(item.quantity, lang)} {item.unit})
                      </span>
                    </div>
                    <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                      ৳ {toBengaliNumeral(item.totalCost, lang)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Total and Remaining Budget Bar */}
              <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700/80 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-500 dark:text-slate-400 block">{lang === 'bn' ? 'মোট বরাদ্দকৃত খরচ:' : 'Total Allocated:'}</span>
                  <span className="text-base font-extrabold text-slate-900 dark:text-white font-mono">
                    ৳ {toBengaliNumeral(totalCalculated, lang)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-semibold flex items-center justify-end gap-1">
                    <Wallet className="w-3.5 h-3.5 text-emerald-500" />
                    {lang === 'bn' ? 'বাজেট অবশিষ্ট:' : 'Budget Surplus:'}
                  </span>
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                    ৳ {toBengaliNumeral(budgetRemaining, lang)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Actions */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/80 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200 dark:hover:bg-slate-800 transition"
          >
            {lang === 'bn' ? 'বাতিল' : 'Cancel'}
          </button>

          <button
            type="button"
            onClick={handleApply}
            disabled={applied || isInfeasible}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
              isInfeasible
                ? 'bg-slate-300 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950/20 hover:scale-[1.02] active:scale-[0.98]'
            }`}
          >
            {applied ? (
              <>
                <Check className="w-4 h-4" />
                <span>{lang === 'bn' ? 'যুক্ত হয়েছে!' : 'Added!'}</span>
              </>
            ) : (
              <>
                <ShoppingBasket className="w-4 h-4" />
                <span>{lang === 'bn' ? 'এই ফর্দটি বাস্কেটে যুক্ত করুন' : 'Add This List to Active Basket'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
