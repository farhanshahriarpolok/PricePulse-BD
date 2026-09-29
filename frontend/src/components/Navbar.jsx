import React, { useState, useRef, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  MapPin, 
  ShieldCheck, 
  RefreshCw,
  GitCompare,
  PlusCircle,
  Server,
  Download,
  Sliders,
  ShoppingBasket,
  Globe,
  ChevronDown,
  Sun,
  Moon,
  Sparkles,
  MapPinned
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export const DISTRICT_HUBS = [
  { id: 'dhaka_karwan', nameBn: 'ঢাকা - কারওয়ান বাজার', nameEn: 'Dhaka - Karwan Bazar' },
  { id: 'chittagong_khatunganj', nameBn: 'চট্টগ্রাম - খাতুনগঞ্জ', nameEn: 'Chattogram - Khatunganj' },
  { id: 'sylhet_sobhani', nameBn: 'সিলেট - সোবহানীঘাট', nameEn: 'Sylhet - Sobhanighat' },
  { id: 'rajshahi_shaheb', nameBn: 'রাজশাহী - সাহেব বাজার', nameEn: 'Rajshahi - Shaheb Bazar' },
  { id: 'khulna_boro', nameBn: 'খুলনা - বড় বাজার', nameEn: 'Khulna - Boro Bazar' },
  { id: 'barishal_notullabad', nameBn: 'বরিশাল - নতুল্লাবাদ', nameEn: 'Barishal - Notullabad' },
  { id: 'rangpur_city', nameBn: 'রংপুর - সিটি বাজার', nameEn: 'Rangpur - City Bazar' },
  { id: 'mymensingh_mechua', nameBn: 'ময়মনসিংহ - মেছুয়া বাজার', nameEn: 'Mymensingh - Mechua Bazar' },
  { id: 'bogura_fateh', nameBn: 'বগুড়া - ফতেহ আলী বাজার', nameEn: 'Bogura - Fateh Ali Bazar' },
  { id: 'jashore_boro', nameBn: 'যশোর - বড় বাজার', nameEn: 'Jashore - Boro Bazar' },
  { id: 'cumilla_chawk', nameBn: 'কুমিল্লা - চকবাজার', nameEn: 'Cumilla - Chawkbazar' },
];

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  anomalyCount = 0,
  basketCount = 0,
  onRefresh, 
  isRefreshing = false,
  onOpenReportModal,
  onOpenExportModal,
  onOpenBudgetModal,
  onTriggerSync,
  isSyncing = false,
  syncToast = null,
  lang = 'bn',
  onToggleLang,
  theme = 'light',
  onToggleTheme,
  selectedDistrict = 'dhaka_karwan',
  onSelectDistrict,
}) {
  const t = (k) => getTranslation(k, lang);
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const moreRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (moreRef.current && !moreRef.current.contains(event.target)) {
        setIsMoreOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 5 Essential Consumer Tabs
  const primaryNavItems = [
    { id: 'pulse', label: t('nav_pulse'), icon: Activity },
    { id: 'basket', label: t('nav_basket'), icon: ShoppingBasket, count: basketCount, isBasket: true },
    { id: 'compare', label: t('nav_compare'), icon: GitCompare },
    { id: 'anomalies', label: t('nav_anomalies'), icon: AlertTriangle, count: anomalyCount },
    { id: 'map', label: t('nav_map'), icon: MapPin },
  ];

  // Secondary technical views in 'More' dropdown
  const secondaryNavItems = [
    { id: 'explorer', label: t('nav_explorer'), icon: TrendingUp },
    { id: 'simulator', label: t('nav_simulator'), icon: Sliders },
    { id: 'sources', label: t('nav_sources'), icon: Server },
    { id: 'provenance', label: t('nav_provenance'), icon: ShieldCheck },
  ];

  const isSecondaryActive = secondaryNavItems.some((item) => item.id === activeTab);

  return (
    <header className="sticky top-0 z-50 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-sm transition-colors duration-150">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-[70px] py-2 gap-3">
          
          {/* Left: Brand Logo + Vector + Sticky District Selector */}
          <div className="flex items-center space-x-3">
            <div 
              className="flex items-center space-x-2.5 cursor-pointer select-none py-1" 
              onClick={() => setActiveTab('pulse')}
            >
              <img 
                src="/logo.svg" 
                alt="PricePulse BD Logo" 
                className="w-9 h-9 object-contain drop-shadow-sm transition-transform hover:scale-105" 
              />
              <div>
                <div className="flex items-center space-x-1.5">
                  <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white font-outfit">PricePulse</span>
                  <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 rounded">BD</span>
                </div>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium hidden sm:block">
                  {t('app_subtitle')}
                </p>
              </div>
            </div>

            {/* Sticky District Selector Dropdown */}
            <div className="relative hidden md:flex items-center">
              <div className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-800 dark:text-slate-200 shadow-sm">
                <MapPinned className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                <select
                  value={selectedDistrict}
                  onChange={(e) => onSelectDistrict && onSelectDistrict(e.target.value)}
                  className="bg-transparent border-none text-xs font-medium text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pr-1"
                >
                  {DISTRICT_HUBS.map((dist) => (
                    <option key={dist.id} value={dist.id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                      {lang === 'bn' ? dist.nameBn : dist.nameEn}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Desktop Navigation Links: 5 Primary Tabs + More */}
          <nav className="hidden lg:flex items-center space-x-1">
            {primaryNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`relative flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? item.isBasket
                        ? 'bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-500/40 shadow-sm font-bold'
                        : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/40 shadow-sm font-bold'
                      : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/70 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${
                    isActive
                      ? item.isBasket ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'
                      : 'text-slate-400 dark:text-slate-500'
                  }`} />
                  <span>{item.label}</span>
                  {item.count > 0 && (
                    <span className={`ml-1 px-1.5 py-0.2 text-[10px] font-bold rounded-full text-white ${
                      item.isBasket ? 'bg-amber-500 animate-pulse' : 'bg-rose-500 animate-pulse'
                    }`}>
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}

            {/* More Dropdown */}
            <div className="relative" ref={moreRef}>
              <button
                onClick={() => setIsMoreOpen(!isMoreOpen)}
                className={`flex items-center space-x-1 px-2.5 py-2 rounded-xl text-xs font-semibold transition-all border ${
                  isSecondaryActive
                    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/40 shadow-sm'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/70 border-transparent'
                }`}
              >
                <span>{t('nav_more')}</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isMoreOpen ? 'rotate-180' : ''}`} />
              </button>

              {isMoreOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 rounded-xl shadow-xl py-1.5 z-50 animate-fadeIn">
                  {secondaryNavItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          setActiveTab(item.id);
                          setIsMoreOpen(false);
                        }}
                        className={`w-full flex items-center space-x-2.5 px-3 py-2 text-xs font-medium transition-colors text-left ${
                          isActive
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-bold'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                        }`}
                      >
                        <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}`} />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </nav>

          {/* Right Action Controls: Budget Optimizer + Theme Switcher + Lang + Sync */}
          <div className="flex items-center space-x-1.5 sm:space-x-2">
            
            {/* Quick Family Budget Optimizer Button */}
            {onOpenBudgetModal && (
              <button
                onClick={onOpenBudgetModal}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/30 text-xs font-bold transition-all shadow-sm"
                title={lang === 'bn' ? 'সাপ্তাহিক বাজেট অপ্টিমাইজার' : 'Family Budget Optimizer'}
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                <span className="hidden sm:inline">{lang === 'bn' ? 'বাজেট অপ্টিমাইজার' : 'Budget'}</span>
              </button>
            )}

            {/* Dynamic Theme Toggle: [☀️ / 🌙] */}
            <button
              id="theme-toggle-btn"
              onClick={onToggleTheme}
              className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-all shadow-sm"
              title={theme === 'dark' ? 'লাইট মোডে পরিবর্তন করুন' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4 text-amber-400 animate-spin-slow" />
              ) : (
                <Moon className="w-4 h-4 text-slate-700" />
              )}
            </button>

            {/* Language Toggle Button */}
            <button
              onClick={onToggleLang}
              id="lang-toggle-btn"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-emerald-700 dark:text-emerald-400 text-xs font-bold border border-slate-200 dark:border-slate-700 transition-all shadow-sm"
              title={lang === 'bn' ? 'Switch to English' : 'বাংলায় দেখুন'}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>{lang === 'bn' ? 'EN' : 'বাংলা'}</span>
            </button>

            {/* Dynamic Sync Live Data Button */}
            <button
              onClick={onTriggerSync}
              disabled={isSyncing}
              title="Harvest live market data from DAM and Chaldal"
              className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-60"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? t('btn_syncing') : t('btn_sync_live')}</span>
            </button>

            {/* Primary Report Price Button */}
            <button
              onClick={onOpenReportModal}
              className="hidden xs:flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-950/20 transition-all"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>{t('btn_report_price')}</span>
            </button>

            {/* Refresh Data Button */}
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title={t('btn_refresh')}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-600 dark:text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Dynamic Sync Status Toast */}
        {syncToast && (
          <div className="bg-slate-900/95 text-white border border-teal-500/40 px-4 py-2 text-xs flex items-center justify-between rounded-xl mb-2 shadow-lg animate-fadeIn">
            <span className="font-medium">{syncToast.message}</span>
            {syncToast.details && (
              <span className="text-teal-300 text-[11px] font-mono">{syncToast.details}</span>
            )}
          </div>
        )}

        {/* Mobile Sub-header: District dropdown for mobile */}
        <div className="flex md:hidden items-center justify-between pb-2 pt-1 border-t border-slate-200 dark:border-slate-800 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-700 dark:text-slate-300">
            <MapPinned className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <select
              value={selectedDistrict}
              onChange={(e) => onSelectDistrict && onSelectDistrict(e.target.value)}
              className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
            >
              {DISTRICT_HUBS.map((dist) => (
                <option key={dist.id} value={dist.id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                  {lang === 'bn' ? dist.nameBn : dist.nameEn}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={onOpenExportModal}
            className="flex items-center space-x-1 px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[11px] font-medium"
          >
            <Download className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
            <span>{t('btn_export')}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
