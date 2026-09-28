import React, { useState, useRef, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  MapPin, 
  ShieldCheck, 
  RefreshCw,
  Database,
  GitCompare,
  PlusCircle,
  Server,
  Download,
  Sliders,
  ShoppingBasket,
  Globe,
  ChevronDown
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  anomalyCount = 0,
  basketCount = 0,
  onRefresh, 
  isRefreshing = false,
  onOpenReportModal,
  onOpenExportModal,
  onTriggerSync,
  isSyncing = false,
  syncToast = null,
  lang = 'bn',
  onToggleLang,
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

  // Secondary technical views moved to 'More' dropdown
  const secondaryNavItems = [
    { id: 'explorer', label: t('nav_explorer'), icon: TrendingUp },
    { id: 'simulator', label: t('nav_simulator'), icon: Sliders },
    { id: 'sources', label: t('nav_sources'), icon: Server },
    { id: 'provenance', label: t('nav_provenance'), icon: ShieldCheck },
  ];

  const isSecondaryActive = secondaryNavItems.some((item) => item.id === activeTab);

  return (
    <header className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-[72px] py-2">
          {/* Brand Header with Vector Logo */}
          <div className="flex items-center space-x-3 cursor-pointer select-none py-1" onClick={() => setActiveTab('pulse')}>
            <img 
              src="/logo.svg" 
              alt="PricePulse BD Logo" 
              className="w-10 h-10 object-contain drop-shadow-md transition-transform hover:scale-105" 
            />
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white font-outfit">PricePulse</span>
                <span className="px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded">BD</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">
                {t('app_subtitle')}
              </p>
            </div>
          </div>

          {/* Desktop Navigation Links (>= lg screen): 5 Primary Tabs + More Dropdown */}
          <nav className="hidden lg:flex items-center space-x-1.5">
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
                        ? 'bg-amber-500/15 text-amber-400 border border-amber-500/40 shadow-sm'
                        : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/70 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${
                    isActive
                      ? item.isBasket ? 'text-amber-400' : 'text-emerald-400'
                      : 'text-slate-400'
                  }`} />
                  <span>{item.label}</span>
                  {item.count > 0 && (
                    <span className={`ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full text-white ${
                      item.isBasket ? 'bg-amber-500' : 'bg-rose-500 animate-pulse'
                    }`}>
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}

            {/* More / অন্যান্য Dropdown */}
            <div className="relative" ref={moreRef}>
              <button
                onClick={() => setIsMoreOpen(!isMoreOpen)}
                className={`flex items-center space-x-1 px-3 py-2 rounded-xl text-xs font-semibold transition-all border ${
                  isSecondaryActive
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/70 border-transparent'
                }`}
              >
                <span>{t('nav_more')}</span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isMoreOpen ? 'rotate-180' : ''}`} />
              </button>

              {isMoreOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl py-1.5 z-50 animate-fadeIn">
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
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }`}
                      >
                        <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </nav>

          {/* System Status & Ingestion Trigger */}
          <div className="flex items-center space-x-2">
            {/* Live Indicator Dot */}
            <div className="hidden sm:flex items-center space-x-1.5 px-2 py-1 rounded-md bg-emerald-950/40 border border-emerald-500/30 text-[11px] text-emerald-400 font-mono select-none">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-semibold tracking-wider text-[10px]">LIVE</span>
            </div>

            {/* Language Toggle Button */}
            <button
              onClick={onToggleLang}
              id="lang-toggle-btn"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 hover:text-emerald-300 text-xs font-bold border border-slate-700 hover:border-emerald-500/40 transition-all shadow-sm"
              title={lang === 'bn' ? 'Switch to English' : 'বাংলায় পরিবর্তন করুন'}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>{lang === 'bn' ? 'EN' : 'বাংলা'}</span>
            </button>

            {/* Dynamic Sync Live Data Button */}
            <button
              onClick={onTriggerSync}
              disabled={isSyncing}
              title="Harvest live market data from DAM and Chaldal"
              className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-md shadow-teal-950/40 transition-all border border-teal-500/40 disabled:opacity-60"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? t('btn_syncing') : t('btn_sync_live')}</span>
            </button>

            {/* Export Data Button */}
            <button
              onClick={onOpenExportModal}
              title="Export Market Intelligence Data (CSV / JSON)"
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 transition-all"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">{t('btn_export')}</span>
            </button>

            {/* Primary Report Price Button */}
            <button
              onClick={onOpenReportModal}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950/40 transition-all border border-emerald-500/40"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span className="hidden xs:inline">{t('btn_report_price')}</span>
            </button>

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title={t('btn_refresh')}
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Dynamic Sync Status Toast */}
        {syncToast && (
          <div className="bg-slate-800/95 border border-teal-500/40 px-4 py-2 text-xs flex items-center justify-between rounded-lg mb-2 shadow-lg animate-fadeIn">
            <span className="text-white font-medium">{syncToast.message}</span>
            {syncToast.details && (
              <span className="text-teal-300 text-[11px] font-mono">{syncToast.details}</span>
            )}
          </div>
        )}

        {/* Mobile & Tablet Navigation Row (< lg screen) */}
        <div className="flex lg:hidden overflow-x-auto py-2.5 space-x-1.5 border-t border-slate-800/80 scrollbar-none">
          {[...primaryNavItems, ...secondaryNavItems].map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  isActive
                    ? item.isBasket
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
                {item.count > 0 && (
                  <span className="px-1 text-[10px] rounded-full bg-rose-500 text-white font-bold">
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
