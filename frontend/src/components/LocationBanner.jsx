import React, { useState, useRef, useEffect } from 'react';
import { MapPin, ArrowLeftRight, X, Check, Sparkles, ChevronDown } from 'lucide-react';
import { 
  PHYSICAL_MARKETS, 
  getMarketById, 
  calculateDistrictSpreadInsight 
} from '../utils/markets';

export default function LocationBanner({
  selectedMarketId,
  onSelectMarket,
  lang = 'bn',
}) {
  const [isOpen, setIsOpen] = useState(false);
  const modalRef = useRef(null);

  const activeMarket = getMarketById(selectedMarketId);
  const insightText = calculateDistrictSpreadInsight(activeMarket.districtId, lang);

  // Close modal when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Group markets by district
  const marketsByDistrict = PHYSICAL_MARKETS.reduce((acc, m) => {
    const key = m.districtId;
    if (!acc[key]) {
      acc[key] = {
        districtBn: m.districtBn,
        districtEn: m.districtEn,
        markets: [],
      };
    }
    acc[key].markets.push(m);
    return acc;
  }, {});

  const handleChooseMarket = (marketId) => {
    onSelectMarket(marketId);
    setIsOpen(false);
  };

  return (
    <div className="relative mb-5">
      {/* Banner Card Container */}
      <div className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 sm:p-5 shadow-xs transition-all">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3.5">
          {/* Left: Location Pin & Active Market Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 flex-shrink-0 shadow-xs">
              <MapPin className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  {lang === 'bn' ? 'আপনার নির্বাচিত বাজার' : 'Selected Market Hub'}
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              </div>
              <h2 className="text-base sm:text-lg font-extrabold text-slate-900 dark:text-white font-outfit tracking-tight">
                {activeMarket.districtBn} — {lang === 'bn' ? activeMarket.nameBn : activeMarket.nameEn}
              </h2>
            </div>
          </div>

          {/* Right: Quick Switcher Button */}
          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              type="button"
              onClick={() => setIsOpen(true)}
              className="px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200/80 dark:bg-slate-800 dark:hover:bg-slate-700/80 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition-all flex items-center gap-1.5 shadow-xs active:scale-95 cursor-pointer"
            >
              <ArrowLeftRight className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>{lang === 'bn' ? '⇄ বাজার পরিবর্তন করুন' : '⇄ Switch Market'}</span>
            </button>
          </div>
        </div>

        {/* Inter-Market Savings Callout Micro-Insight */}
        <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/70 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400 select-none">
          <span className="font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-200/60 dark:border-emerald-800/40 truncate">
            {insightText}
          </span>
        </div>
      </div>

      {/* Market Selector Modal / Popover */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div 
            ref={modalRef}
            className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden p-5 sm:p-6"
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3.5 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <MapPin className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white font-outfit">
                    {lang === 'bn' ? 'নিত্যপণ্যের কাঁচাবাজার নির্বাচন করুন' : 'Select Local Commodity Market'}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {lang === 'bn' ? 'নির্দিষ্ট স্থানীয় বাজারের লাইভ খুচরা ও পাইকারি দর দেখতে সিলেক্ট করুন' : 'Choose a specific market to view localized pricing'}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Markets List by District */}
            <div className="mt-4 max-h-[60vh] overflow-y-auto space-y-4 pr-1 scrollbar-thin">
              {Object.entries(marketsByDistrict).map(([distKey, distData]) => (
                <div key={distKey} className="space-y-2">
                  <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span>{lang === 'bn' ? distData.districtBn : distData.districtEn}</span>
                    <span className="text-[10px] text-slate-400 font-normal">
                      ({distData.markets.length} {lang === 'bn' ? 'টি বাজার' : 'markets'})
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {distData.markets.map((m) => {
                      const isSelected = m.id === selectedMarketId;
                      const isHub = m.type === 'wholesale_hub';

                      return (
                        <button
                          key={m.id}
                          type="button"
                          onClick={() => handleChooseMarket(m.id)}
                          className={`p-3 rounded-xl border text-left transition-all flex items-start justify-between gap-2 cursor-pointer ${
                            isSelected
                              ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 text-emerald-900 dark:text-emerald-200 ring-1 ring-emerald-500/20 shadow-xs'
                              : 'bg-slate-50/70 hover:bg-slate-100 dark:bg-slate-800/40 dark:hover:bg-slate-800/80 border-slate-200/80 dark:border-slate-700/80 text-slate-800 dark:text-slate-200'
                          }`}
                        >
                          <div className="min-w-0 flex-1">
                            <span className="font-bold text-xs sm:text-sm block truncate">
                              {lang === 'bn' ? m.nameBn : m.nameEn}
                            </span>
                            <span className="text-[10px] text-slate-500 dark:text-slate-400 block mt-0.5">
                              {isHub 
                                ? (lang === 'bn' ? 'পাইকারি আড়ত হাব' : 'Wholesale Hub')
                                : (lang === 'bn' ? 'খুচরা কাঁচাবাজার' : 'Retail Market')
                              }
                            </span>
                          </div>
                          {isSelected && (
                            <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Modal Footer */}
            <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition"
              >
                {lang === 'bn' ? 'বন্ধ করুন' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
