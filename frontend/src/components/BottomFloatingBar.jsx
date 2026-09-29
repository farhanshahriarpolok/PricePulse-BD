import React, { useState, useRef, useEffect } from 'react';
import { 
  Activity, 
  ShoppingBasket, 
  GitCompare, 
  AlertTriangle, 
  MapPin, 
  MoreHorizontal,
  TrendingUp,
  Sliders,
  Server,
  ShieldCheck,
  Sparkles,
  PlusCircle,
  Download,
  ChevronUp
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function BottomFloatingBar({
  activeTab,
  setActiveTab,
  basketCount = 0,
  anomalyCount = 0,
  lang = 'bn',
  onOpenBudgetModal,
  onOpenReportModal,
  onOpenExportModal,
}) {
  const t = (k) => getTranslation(k, lang);
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const menuRef = useRef(null);

  // Close popover when clicked outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMoreOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 5 Essential Consumer Tabs
  const primaryTabs = [
    { id: 'pulse', labelBn: 'আজকের দর', labelEn: 'Pulse', icon: Activity },
    { id: 'basket', labelBn: 'বাজারের ফর্দ', labelEn: 'Basket', icon: ShoppingBasket, count: basketCount, isBasket: true },
    { id: 'compare', labelBn: 'বাজার তুলনা', labelEn: 'Compare', icon: GitCompare },
    { id: 'anomalies', labelBn: 'সতর্কতা', labelEn: 'Alerts', icon: AlertTriangle, count: anomalyCount },
    { id: 'map', labelBn: 'জেলা ম্যাপ', labelEn: 'Map', icon: MapPin },
  ];

  // Secondary Tools
  const secondaryTabs = [
    { id: 'explorer', labelBn: 'প্রোডাক্ট এক্সপ্লোরার', labelEn: 'Commodity Explorer', icon: TrendingUp },
    { id: 'simulator', labelBn: 'সাপ্লাই শক সিমুলেটর', labelEn: 'Shock Simulator', icon: Sliders },
    { id: 'sources', labelBn: 'ডাটা সোর্স স্বাস্থ্য', labelEn: 'Source Health', icon: Server },
    { id: 'provenance', labelBn: 'ডাটা সততা ও প্রমাণপত্র', labelEn: 'Data Provenance', icon: ShieldCheck },
  ];

  const isSecondaryActive = secondaryTabs.some((tab) => tab.id === activeTab);

  return (
    <div className="fixed bottom-3 sm:bottom-5 left-1/2 -translate-x-1/2 z-40 select-none">
      
      {/* Secondary Tools Popover Menu */}
      {isMoreOpen && (
        <div 
          ref={menuRef}
          className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 w-64 bg-white/95 dark:bg-slate-900/95 backdrop-blur-2xl border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-2 z-50 animate-fadeIn"
        >
          <div className="px-2.5 py-1.5 border-b border-slate-100 dark:border-slate-800 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            {lang === 'bn' ? 'অতিরিক্ত সেবা ও টুলস' : 'Advanced Tools'}
          </div>

          <div className="py-1 space-y-0.5">
            {secondaryTabs.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setIsMoreOpen(false);
                  }}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold transition-colors text-left ${
                    isActive
                      ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}`} />
                  <span>{lang === 'bn' ? item.labelBn : item.labelEn}</span>
                </button>
              );
            })}
          </div>

          {/* Quick Action Modals */}
          <div className="pt-1.5 mt-1 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-1">
            {onOpenBudgetModal && (
              <button
                onClick={() => {
                  onOpenBudgetModal();
                  setIsMoreOpen(false);
                }}
                className="flex items-center gap-1.5 p-2 rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 text-[11px] font-bold hover:bg-amber-100 transition"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                <span>{lang === 'bn' ? 'বাজেট প্ল্যান' : 'Budget'}</span>
              </button>
            )}

            {onOpenReportModal && (
              <button
                onClick={() => {
                  onOpenReportModal();
                  setIsMoreOpen(false);
                }}
                className="flex items-center gap-1.5 p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 text-[11px] font-bold hover:bg-emerald-100 transition"
              >
                <PlusCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span>{lang === 'bn' ? 'দর রিপোর্ট' : 'Report'}</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Floating Island Nav Bar */}
      <nav 
        aria-label="Main Navigation"
        className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-2xl border border-slate-200/90 dark:border-slate-800/90 shadow-2xl rounded-2xl p-1.5 flex items-center gap-1 sm:gap-1.5"
      >
        {primaryTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`relative flex items-center gap-1.5 px-3 sm:px-3.5 py-2 rounded-xl text-xs font-semibold transition-all active:scale-95 ${
                isActive
                  ? tab.isBasket
                    ? 'bg-amber-600 text-white font-bold shadow-md shadow-amber-950/20'
                    : 'bg-emerald-600 text-white font-bold shadow-md shadow-emerald-950/20'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/80'
              }`}
            >
              <div className="relative flex items-center justify-center">
                <Icon className="w-4 h-4 sm:w-4 sm:h-4" />
                {tab.count > 0 && (
                  <span className={`absolute -top-2 -right-2 px-1.5 py-0.2 text-[9px] font-mono font-black rounded-full shadow-xs ${
                    isActive 
                      ? 'bg-white text-emerald-800' 
                      : tab.isBasket 
                      ? 'bg-amber-500 text-white animate-pulse' 
                      : 'bg-rose-500 text-white animate-pulse'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </div>

              <span className="hidden md:inline whitespace-nowrap">
                {lang === 'bn' ? tab.labelBn : tab.labelEn}
              </span>
            </button>
          );
        })}

        {/* Vertical divider */}
        <div className="w-[1px] h-5 bg-slate-200 dark:bg-slate-700/80 mx-0.5" />

        {/* More Tools Button */}
        <button
          onClick={() => setIsMoreOpen(!isMoreOpen)}
          className={`flex items-center gap-1 px-2.5 py-2 rounded-xl text-xs font-semibold transition-all active:scale-95 ${
            isSecondaryActive || isMoreOpen
              ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
              : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80'
          }`}
          title={lang === 'bn' ? 'আরও ফিচার' : 'More Features'}
        >
          <MoreHorizontal className="w-4 h-4" />
          <ChevronUp className={`w-3 h-3 transition-transform ${isMoreOpen ? 'rotate-180' : ''}`} />
        </button>
      </nav>

    </div>
  );
}
