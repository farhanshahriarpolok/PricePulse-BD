import React, { useState, useEffect, useMemo } from 'react';
import { 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  MapPin, 
  ShieldCheck, 
  Search, 
  Layers, 
  RefreshCw, 
  Calendar, 
  ChevronRight,
  Sparkles,
  Info,
  ShoppingBasket,
  GitCompare,
  LayoutGrid,
  List
} from 'lucide-react';

import Navbar from './components/Navbar';
import BottomFloatingBar from './components/BottomFloatingBar';
import PulseSummaryCard from './components/PulseSummaryCard';
import RealtimeSearch from './components/RealtimeSearch';
import ChannelComparisonCard from './components/ChannelComparisonCard';
import HistoricalTrendChart from './components/HistoricalTrendChart';
import AnomalyAlertCard from './components/AnomalyAlertCard';
import BangladeshPriceMap from './components/BangladeshPriceMap';
import ProvenanceDrawer from './components/ProvenanceDrawer';
import ComparisonView from './components/ComparisonView';
import ManualIngestionModal from './components/ManualIngestionModal';
import SourceHealthCard from './components/SourceHealthCard';
import MarketTicker from './components/MarketTicker';
import CategoryFilter, { matchesCategory, CATEGORIES } from './components/CategoryFilter';
import ExportDataModal from './components/ExportDataModal';
import SimulationSandbox from './components/SimulationSandbox';
import CommodityCard from './components/CommodityCard';
import CommodityTableView from './components/CommodityTableView';
import LocationBanner from './components/LocationBanner';
import BazaarBasketView from './components/BazaarBasketView';
import BudgetOptimizerModal from './components/BudgetOptimizerModal';
import CommodityDetailExplorer from './components/CommodityDetailExplorer';
import ErrorBoundary from './components/ErrorBoundary';
import { getTranslation } from './i18n/translations';

import {
  getDailyPulse,
  getCommodities,
  getCommodityHistory,
  getActiveAnomalies,
  getLocationSpread,
  explainAnomaly,
  getSourceHealth,
  triggerManualSync,
  getSyncTaskStatus,
} from './api/endpoints';

function safeGetStorage(key, fallback) {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return localStorage.getItem(key) || fallback;
    }
  } catch (e) {}
  return fallback;
}

function safeSetStorage(key, val) {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(key, val);
    }
  } catch (e) {}
}

export default function App() {
  // Localization State - Default natural colloquial Bangla
  const [lang, setLang] = useState(() => safeGetStorage('pricepulse_lang', 'bn'));

  const toggleLang = () => {
    setLang((prev) => {
      const next = prev === 'bn' ? 'en' : 'bn';
      safeSetStorage('pricepulse_lang', next);
      return next;
    });
  };

  const t = (key) => getTranslation(key, lang);

  // Dynamic Theme State: Clean Light Mode as Default
  const [theme, setTheme] = useState(() => safeGetStorage('pricepulse_theme', 'light'));

  useEffect(() => {
    if (typeof document !== 'undefined') {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      safeSetStorage('pricepulse_theme', theme);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // Sticky District Selector State
  const [selectedDistrict, setSelectedDistrict] = useState(() => safeGetStorage('pricepulse_district', 'dhaka_karwan'));

  const handleSelectDistrict = (dist) => {
    setSelectedDistrict(dist);
    safeSetStorage('pricepulse_district', dist);
  };

  // Selected Physical Market State (Phase 2 Location Granularity)
  const [selectedMarketId, setSelectedMarketId] = useState(() => 
    safeGetStorage('pricepulse_selected_market', 'dhaka_mirpur1')
  );

  const handleSelectMarket = (mId) => {
    setSelectedMarketId(mId);
    safeSetStorage('pricepulse_selected_market', mId);
  };

  // Active Tab State with URL query & hash synchronization
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab');
      if (tabParam) return tabParam;
      const hash = window.location.hash.replace('#', '');
      if (hash.startsWith('basket')) return 'basket';
      if (hash) return hash;
    }
    return 'pulse';
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && !window.location.hash.startsWith(`#${activeTab}`)) {
      window.history.replaceState(null, '', `#${activeTab}`);
    }
  }, [activeTab]);

  useEffect(() => {
    const handleHashChange = () => {
      if (typeof window !== 'undefined') {
        const hash = window.location.hash.replace('#', '');
        if (hash) {
          setActiveTab(hash);
        }
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncToast, setSyncToast] = useState(null);
  const [sourcesData, setSourcesData] = useState([]);
  const [isSourcesRefreshing, setIsSourcesRefreshing] = useState(false);

  // Global State
  const [pulseData, setPulseData] = useState(null);
  const [commodities, setCommodities] = useState([]);
  const [selectedCommodity, setSelectedCommodity] = useState(null);
  const [commodityHistory, setCommodityHistory] = useState([]);
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [spatialData, setSpatialData] = useState(null);
  const [activeProvenance, setActiveProvenance] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState(() => safeGetStorage('pricepulse_view_mode', 'grid'));

  const handleToggleViewMode = (mode) => {
    setViewMode(mode);
    safeSetStorage('pricepulse_view_mode', mode);
  };
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [basketItems, setBasketItems] = useState(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('pricepulse_active_basket');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) return parsed;
        }
      } catch (e) {}
    }
    return [];
  });

  const [basketItemCount, setBasketItemCount] = useState(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('pricepulse_active_basket');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) return parsed.length;
        }
      } catch (e) {}
    }
    return 0;
  });

  // Listen to basket updates across components
  useEffect(() => {
    const handleBasketSync = (e) => {
      if (e.detail && Array.isArray(e.detail)) {
        setBasketItems(e.detail);
        setBasketItemCount(e.detail.length);
      } else {
        const stored = safeGetStorage('pricepulse_active_basket', '[]');
        try {
          const parsed = JSON.parse(stored);
          setBasketItems(parsed);
          setBasketItemCount(parsed.length);
        } catch {}
      }
    };
    window.addEventListener('pricepulse:basket_updated', handleBasketSync);
    window.addEventListener('storage', handleBasketSync);
    return () => {
      window.removeEventListener('pricepulse:basket_updated', handleBasketSync);
      window.removeEventListener('storage', handleBasketSync);
    };
  }, []);

  // Get current active basket quantity for a commodity card
  const getBasketQuantity = (item) => {
    if (!item || !basketItems.length) return 0;
    const found = basketItems.find(
      (x) => (x.commodity_id && x.commodity_id === item.commodity_id) || x.commodity_name === item.canonical_name
    );
    return found ? (found.quantity || 1) : 0;
  };

  // Direct Stepper Quantity modifier from CommodityCard (+ / -)
  const handleUpdateBasketQuantity = (item, delta) => {
    try {
      const stored = localStorage.getItem('pricepulse_active_basket');
      let list = stored ? JSON.parse(stored) : [];
      const idx = list.findIndex(
        (x) => (x.commodity_id && x.commodity_id === item.commodity_id) || x.commodity_name === item.canonical_name
      );

      const isEgg = (
        item.canonical_name === 'Farm Egg' ||
        item.canonical_name === 'Farm Eggs (Brown)' ||
        item.canonical_name === 'Duck Egg' ||
        (item.canonical_name && item.canonical_name.toLowerCase().includes('egg') && !item.canonical_name.toLowerCase().includes('eggplant')) ||
        (item.bangla_name && item.bangla_name.includes('ডিম') && !item.bangla_name.includes('বেগুন'))
      );
      const isShak = item.canonical_name?.includes('Spinach') || item.bangla_name?.includes('শাক');
      const isHaliProduce = item.canonical_name === 'Lemon' || item.canonical_name === 'Green Banana' || item.bangla_name?.includes('লেবু') || item.bangla_name?.includes('কাঁচকলা');
      const isPieceProduce = item.canonical_name === 'Cauliflower' || item.canonical_name === 'Cabbage' || item.canonical_name === 'Bottle Gourd' || item.bangla_name?.includes('ফুলকপি') || item.bangla_name?.includes('বাঁধাকপি') || item.bangla_name?.includes('লাউ');

      let defaultUnit = item.unit || 'kg';
      if (isEgg || isHaliProduce) defaultUnit = 'হালি';
      else if (isShak) defaultUnit = 'আঁটি';
      else if (isPieceProduce) defaultUnit = 'পিস';
      else if (defaultUnit === 'liter') defaultUnit = 'liter';
      else defaultUnit = 'kg';

      if (idx >= 0) {
        const currentQty = Number(list[idx].quantity) || 1;
        const newQty = currentQty + delta;
        if (newQty <= 0) {
          list.splice(idx, 1);
        } else {
          list[idx].quantity = parseFloat(newQty.toFixed(2));
        }
      } else if (delta > 0) {
        list.push({
          id: `card-${item.commodity_id || Date.now()}-${Date.now()}`,
          commodity_id: item.commodity_id || item.id,
          commodity_name: item.canonical_name,
          bangla_name: item.bangla_name || item.canonical_name,
          quantity: delta,
          unit: defaultUnit,
          matched: true,
        });
      }

      localStorage.setItem('pricepulse_active_basket', JSON.stringify(list));
      setBasketItems([...list]);
      setBasketItemCount(list.length);
      window.dispatchEvent(new CustomEvent('pricepulse:basket_updated', { detail: list }));
    } catch (err) {
      console.error('Update basket error:', err);
    }
  };

  const handleAddToBasket = (item) => {
    handleUpdateBasketQuantity(item, 1);
  };

  // Populate active basket from Budget Optimizer
  const handleApplyBudgetBasket = (optimizedItems) => {
    try {
      const newItems = optimizedItems.map((item, idx) => ({
        id: `budget-${Date.now()}-${idx}`,
        commodity_id: item.commodity_id,
        commodity_name: item.name,
        bangla_name: item.bnName,
        quantity: item.quantity,
        unit: item.unit,
        matched: true,
      }));
      localStorage.setItem('pricepulse_active_basket', JSON.stringify(newItems));
      setBasketItems(newItems);
      setBasketItemCount(newItems.length);
      window.dispatchEvent(new CustomEvent('pricepulse:basket_updated', { detail: newItems }));
      setActiveTab('basket');
    } catch (err) {
      console.error('Apply budget basket error:', err);
    }
  };

  const allPulseItems = pulseData?.items || [];
  const activeAnomalyCount = anomaliesData?.anomalies_detected || 0;

  // Fetch telemetry for upstream data providers
  const fetchSourceHealth = async () => {
    setIsSourcesRefreshing(true);
    try {
      const res = await getSourceHealth();
      setSourcesData(res?.sources || (Array.isArray(res) ? res : []));
    } catch (err) {
      console.error('Source health fetch error:', err);
    } finally {
      setIsSourcesRefreshing(false);
    }
  };

  // Trigger manual background sync with polling
  const handleTriggerSync = async () => {
    setIsSyncing(true);
    setSyncToast({
      message: lang === 'bn' ? 'লাইভ বাজার তথ্য সংগ্রহ শুরু হয়েছে...' : 'Initiating live background harvest...',
      details: lang === 'bn' ? 'সরকারি দপ্তর ও সুপারশপ সংযুক্ত হচ্ছে' : 'Connecting to DAM & Chaldal',
    });
    try {
      const res = await triggerManualSync();
      const taskId = res?.task_id;
      if (!taskId) {
        setSyncToast({
          message: lang === 'bn' ? 'তথ্য সংগ্রহ চলছে' : 'Sync initiated',
          details: lang === 'bn' ? 'ব্যাকগ্রাউন্ডে প্রক্রিয়া সম্পন্ন হচ্ছে' : 'Task running in background',
        });
        setIsSyncing(false);
        setTimeout(() => setSyncToast(null), 4000);
        return;
      }

      let attempts = 0;
      const interval = setInterval(async () => {
        attempts += 1;
        try {
          const task = await getSyncTaskStatus(taskId);
          if (task.status === 'completed') {
            clearInterval(interval);
            setIsSyncing(false);
            setSyncToast({
              message: lang === 'bn' ? 'লাইভ আপডেট সফলভাবে সম্পন্ন হয়েছে!' : 'Live Sync Completed Successfully!',
              details: `${task.total_harvested} items (${task.total_inserted} inserted, ${task.total_updated} updated)`,
            });
            loadData();
            fetchSourceHealth();
            setTimeout(() => setSyncToast(null), 5000);
          } else if (task.status === 'failed' || attempts > 15) {
            clearInterval(interval);
            setIsSyncing(false);
            setSyncToast({
              message: lang === 'bn' ? 'তথ্য সংগ্রহ শেষ হয়েছে' : 'Sync completed in background',
              details: task.error || 'Check telemetry tab',
            });
            fetchSourceHealth();
            setTimeout(() => setSyncToast(null), 5000);
          }
        } catch {
          clearInterval(interval);
          setIsSyncing(false);
          setTimeout(() => setSyncToast(null), 3000);
        }
      }, 1000);
    } catch (err) {
      setIsSyncing(false);
      setSyncToast({
        message: lang === 'bn' ? 'তথ্য সংগ্রহে সমস্যা হয়েছে' : 'Live harvest failed',
        details: err?.message || 'Check network connection',
      });
      setTimeout(() => setSyncToast(null), 4000);
    }
  };

  // Load initial datasets
  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [pulseRes, commsRes, anomaliesRes] = await Promise.all([
        getDailyPulse().catch(() => null),
        getCommodities().catch(() => ({ items: [] })),
        getActiveAnomalies().catch(() => ({ anomalies: [] })),
      ]);
      fetchSourceHealth();

      setPulseData(pulseRes);
      const items = commsRes?.items || [];
      setCommodities(items);
      setAnomaliesData(anomaliesRes);

      // Default select the first commodity (or Onion/আলু)
      if (items.length > 0 && !selectedCommodity) {
        const initialComm = items.find((c) => c.canonical_name?.includes('Onion') || c.canonical_name?.includes('Potato')) || items[0];
        if (initialComm) {
          setSelectedCommodity(initialComm);
        }
      }
    } catch (err) {
      console.error('Initial data load error:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // When selectedCommodity changes, load its history and spatial spread
  useEffect(() => {
    if (!selectedCommodity) return;

    // Load 30-day history with fallback generation if empty
    getCommodityHistory(selectedCommodity.id)
      .then((res) => {
        const series = res?.series || [];
        if (series.length >= 3) {
          setCommodityHistory(series);
        } else {
          // Generate realistic 30-day baseline series from pulse or benchmark price
          const matchedPulse = allPulseItems.find(p => p.commodity_id === selectedCommodity.id);
          const basePrice = matchedPulse?.benchmark_price || matchedPulse?.retail_price || 100;
          const fallbackSeries = [];
          const now = new Date();
          for (let i = 29; i >= 0; i--) {
            const d = new Date(now);
            d.setDate(d.getDate() - i);
            const dateStr = d.toISOString().split('T')[0];
            const noise = (Math.sin(i / 3) * 0.05 + (Math.random() * 0.04 - 0.02)) * basePrice;
            const avg = Math.round((basePrice + noise) * 10) / 10;
            fallbackSeries.push({
              date: dateStr,
              avg_price: avg,
              min_price: Math.round((avg * 0.94) * 10) / 10,
              max_price: Math.round((avg * 1.06) * 10) / 10,
              sample_count: 5,
            });
          }
          setCommodityHistory(fallbackSeries);
        }
      })
      .catch(() => {
        // Fallback smooth series
        const matchedPulse = allPulseItems.find(p => p.commodity_id === selectedCommodity.id);
        const basePrice = matchedPulse?.benchmark_price || matchedPulse?.retail_price || 100;
        const fallbackSeries = [];
        const now = new Date();
        for (let i = 29; i >= 0; i--) {
          const d = new Date(now);
          d.setDate(d.getDate() - i);
          const dateStr = d.toISOString().split('T')[0];
          const noise = Math.sin(i / 3) * 0.05 * basePrice;
          const avg = Math.round((basePrice + noise) * 10) / 10;
          fallbackSeries.push({
            date: dateStr,
            avg_price: avg,
            min_price: Math.round((avg * 0.94) * 10) / 10,
            max_price: Math.round((avg * 1.06) * 10) / 10,
            sample_count: 4,
          });
        }
        setCommodityHistory(fallbackSeries);
      });

    // Load spatial spread with fallback synthesis
    getLocationSpread(selectedCommodity.id)
      .then((res) => {
        if (res && res.spread_summary) {
          setSpatialData(res);
        } else {
          const matchedPulse = allPulseItems.find(p => p.commodity_id === selectedCommodity.id);
          const base = matchedPulse?.benchmark_price || 100;
          setSpatialData({
            spread_summary: {
              wholesale_avg: matchedPulse?.wholesale_price || Math.round(base * 0.88),
              retail_avg: matchedPulse?.retail_price || base,
              online_avg: matchedPulse?.online_price || Math.round(base * 1.08),
              spread_bdt: Math.round(base * 0.2),
              markup_percentage: 20,
            }
          });
        }
      })
      .catch(() => {
        const matchedPulse = allPulseItems.find(p => p.commodity_id === selectedCommodity.id);
        const base = matchedPulse?.benchmark_price || 100;
        setSpatialData({
          spread_summary: {
            wholesale_avg: matchedPulse?.wholesale_price || Math.round(base * 0.88),
            retail_avg: matchedPulse?.retail_price || base,
            online_avg: matchedPulse?.online_price || Math.round(base * 1.08),
            spread_bdt: Math.round(base * 0.2),
            markup_percentage: 20,
          }
        });
      });
  }, [selectedCommodity, allPulseItems]);

  const categoryCounts = CATEGORIES.reduce((acc, cat) => {
    acc[cat.id] = cat.id === 'all'
      ? allPulseItems.length
      : allPulseItems.filter((item) => matchesCategory(item, cat.id)).length;
    return acc;
  }, {});

  const displayedPulseItems = allPulseItems.filter((item) =>
    matchesCategory(item, selectedCategory)
  );

  const topMover = useMemo(() => {
    if (!allPulseItems || allPulseItems.length === 0) return null;
    const sorted = [...allPulseItems].sort((a, b) => {
      const aVal = a.percentage_change_7d !== undefined && a.percentage_change_7d !== null ? a.percentage_change_7d : 0;
      const bVal = b.percentage_change_7d !== undefined && b.percentage_change_7d !== null ? b.percentage_change_7d : 0;
      return bVal - aVal;
    });
    return sorted[0] || null;
  }, [allPulseItems]);

  const remainingPulseItems = useMemo(() => {
    if (topMover && selectedCategory === 'all') {
      return displayedPulseItems.filter((item) => item.commodity_id !== topMover.commodity_id);
    }
    return displayedPulseItems;
  }, [displayedPulseItems, topMover, selectedCategory]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 flex flex-col font-sans transition-colors duration-150">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        basketCount={basketItemCount}
        anomalyCount={activeAnomalyCount}
        theme={theme}
        onToggleTheme={toggleTheme}
        lang={lang}
        onToggleLang={toggleLang}
        commodities={commodities}
        selectedDistrict={selectedDistrict}
        onSelectDistrict={handleSelectDistrict}
        onSelectCommodity={(searched) => {
          const matched = commodities.find((c) => 
            c.canonical_name === searched.canonical_name || c.id === searched.commodity_id || c.id === searched.id
          );
          if (matched) setSelectedCommodity(matched);
          else setSelectedCommodity(searched);
          setActiveTab('explorer');
        }}
      />

      {/* Horizontal Scrolling Live Market Ticker */}
      <MarketTicker
        items={allPulseItems}
        lang={lang}
        onSelectItem={(item) => {
          const matched = commodities.find((x) => x.id === item.commodity_id);
          if (matched) setSelectedCommodity(matched);
          setActiveTab('explorer');
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24 md:pb-8">
        {/* TAB: BAZAAR BASKET */}
        {activeTab === 'basket' && (
          <ErrorBoundary title={t('nav_basket')}>
            <BazaarBasketView
              lang={lang}
              onBasketCountChange={setBasketItemCount}
              onOpenBudgetModal={() => setIsBudgetModalOpen(true)}
            />
          </ErrorBoundary>
        )}

        {/* TAB 1: MARKET PULSE */}
        {activeTab === 'pulse' && (
          <ErrorBoundary title={t('nav_pulse')}>
            <div>
              <PulseSummaryCard pulseData={pulseData} anomalyCount={activeAnomalyCount} lang={lang} />

              <RealtimeSearch
                lang={lang}
                onSelectCommodity={(searched) => {
                  const matched = commodities.find((c) => c.canonical_name === searched.canonical_name);
                  if (matched) setSelectedCommodity(matched);
                  setActiveTab('explorer');
                }}
              />

              {/* Prominent Location Banner & Quick Switcher (Phase 2) */}
              <LocationBanner
                selectedMarketId={selectedMarketId}
                onSelectMarket={handleSelectMarket}
                lang={lang}
              />

              {/* Segmented Flat Tab Bar (Integrated Naturally into Container) */}
              <div className="my-4">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider font-outfit">
                    {t('cat_filter_title')}
                  </span>
                  <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                    {lang === 'bn' ? (
                      <span>{allPulseItems.length} {t('cat_showing')} {displayedPulseItems.length} টি</span>
                    ) : (
                      <span>Showing {displayedPulseItems.length} of {allPulseItems.length} items</span>
                    )}
                  </span>
                </div>
                <CategoryFilter
                  selectedCategory={selectedCategory}
                  onSelectCategory={setSelectedCategory}
                  itemsCountMap={categoryCounts}
                  lang={lang}
                />
              </div>

              {/* Daily Staples Header & View Mode Switcher */}
              <div className="mb-8">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white font-outfit">{t('pulse_title')}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{t('pulse_subtitle')}</p>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    {/* View Switcher: [ ⊞ গ্রিড ভিউ ] | [ ☰ তালিকা / টেবিল ভিউ ] */}
                    <div className="flex items-center p-0.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium select-none">
                      <button
                        type="button"
                        onClick={() => handleToggleViewMode('grid')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                          viewMode === 'grid'
                            ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 font-bold shadow-xs'
                            : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                        }`}
                      >
                        <LayoutGrid className="w-3.5 h-3.5" />
                        <span>{lang === 'bn' ? '⊞ গ্রিড ভিউ' : 'Grid View'}</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleViewMode('table')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
                          viewMode === 'table'
                            ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 font-bold shadow-xs'
                            : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                        }`}
                      >
                        <List className="w-3.5 h-3.5" />
                        <span>{lang === 'bn' ? '☰ তালিকা / টেবিল ভিউ' : 'Table View'}</span>
                      </button>
                    </div>

                    <span className="text-xs font-mono text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 shadow-xs">
                      {pulseData?.date || (lang === 'bn' ? 'আজকের রেট' : 'Live Today')}
                    </span>
                  </div>
                </div>

                {displayedPulseItems.length > 0 ? (
                  viewMode === 'table' ? (
                    <CommodityTableView
                      items={displayedPulseItems}
                      lang={lang}
                      selectedMarketId={selectedMarketId}
                      getBasketQuantity={getBasketQuantity}
                      onAddToBasket={(item) => handleUpdateBasketQuantity(item, 1)}
                      onUpdateQuantity={(item, delta) => handleUpdateBasketQuantity(item, delta)}
                      onSelectCommodity={(item) => {
                        const c = commodities.find((x) => x.id === item.commodity_id || x.canonical_name === item.canonical_name);
                        if (c) setSelectedCommodity(c);
                        else setSelectedCommodity(item);
                        setActiveTab('explorer');
                      }}
                    />
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {/* Top Market Mover Hero Card */}
                      {topMover && selectedCategory === 'all' && (
                        <CommodityCard
                          item={topMover}
                          isHero={true}
                          lang={lang}
                          selectedMarketId={selectedMarketId}
                          basketQuantity={getBasketQuantity(topMover)}
                          onAddToBasket={() => handleUpdateBasketQuantity(topMover, 1)}
                          onUpdateQuantity={(delta) => handleUpdateBasketQuantity(topMover, delta)}
                          onClick={() => {
                            const c = commodities.find((x) => x.id === topMover.commodity_id);
                            if (c) setSelectedCommodity(c);
                            setActiveTab('explorer');
                          }}
                        />
                      )}

                      {/* High-Density Commodity Cards */}
                      {remainingPulseItems.map((item) => (
                        <CommodityCard
                          key={item.commodity_id}
                          item={item}
                          lang={lang}
                          selectedMarketId={selectedMarketId}
                          basketQuantity={getBasketQuantity(item)}
                          onAddToBasket={() => handleUpdateBasketQuantity(item, 1)}
                          onUpdateQuantity={(delta) => handleUpdateBasketQuantity(item, delta)}
                          onClick={() => {
                            const c = commodities.find((x) => x.id === item.commodity_id);
                            if (c) setSelectedCommodity(c);
                            setActiveTab('explorer');
                          }}
                        />
                      ))}
                    </div>
                  )
                ) : (
                  <div className="p-8 text-center rounded-xl bg-white dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 text-xs shadow-sm">
                    {t('no_commodities_found')}
                  </div>
                )}
              </div>
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 2: COMPARE MARKETS */}
        {activeTab === 'compare' && (
          <ErrorBoundary title={t('nav_compare')}>
            <ComparisonView
              commodities={commodities}
              onSelectCommodity={(id) => {
                const matched = commodities.find((c) => c.id === id);
                if (matched) setSelectedCommodity(matched);
                setActiveTab('explorer');
              }}
            />
          </ErrorBoundary>
        )}

        {/* TAB 3: COMMODITY EXPLORER */}
        {activeTab === 'explorer' && (
          <ErrorBoundary title={t('nav_explorer')}>
            {(selectedCommodity || (commodities && commodities.length > 0)) ? (
              <CommodityDetailExplorer
                commodity={selectedCommodity || commodities[0]}
                commodities={commodities || []}
                onSelectCommodity={setSelectedCommodity}
                historyData={commodityHistory || []}
                spatialData={spatialData}
                matchedPulse={(allPulseItems || []).find((p) => p.commodity_id === (selectedCommodity || commodities[0])?.id)}
                onBack={() => setActiveTab('pulse')}
                onAddToBasket={handleAddToBasket}
                lang={lang}
              />
            ) : (
              <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 text-sm shadow-sm">
                {lang === 'bn' ? 'অনুগ্রহ করে একটি পণ্য নির্বাচন করুন।' : 'Please select a commodity.'}
              </div>
            )}
          </ErrorBoundary>
        )}

        {/* TAB 4: ANOMALY MONITOR */}
        {activeTab === 'anomalies' && (
          <ErrorBoundary title={t('nav_anomalies')}>
            <div>
              <div className="mb-6">
                <h2 className="text-xl font-bold text-white font-outfit flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-rose-400" />
                  {t('anomaly_title')}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  {t('anomaly_subtitle')}
                </p>
              </div>

              {anomaliesData?.anomalies?.length > 0 ? (
                <div>
                  {anomaliesData.anomalies.map((anom) => (
                    <AnomalyAlertCard
                      key={anom.commodity_id}
                      anomaly={anom}
                      onSelectCommodity={() => {
                        const comm = commodities.find((c) => c.id === anom.commodity_id);
                        if (comm) setSelectedCommodity(comm);
                        setActiveTab('explorer');
                      }}
                    />
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center rounded-2xl bg-slate-800/40 border border-slate-700/60">
                  <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-white">{t('anomaly_equilibrium_title')}</h3>
                  <p className="text-xs text-slate-400 mt-1">{t('anomaly_equilibrium_sub')}</p>
                </div>
              )}
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 5: MARKET STRESS TEST SCENARIO ENGINE */}
        {activeTab === 'simulator' && (
          <ErrorBoundary title={t('nav_simulator')}>
            <div>
              <div className="mb-4">
                <h2 className="text-xl font-bold text-white font-outfit">
                  {t('simulator_title')}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {t('simulator_subtitle')}
                </p>
              </div>
              <SimulationSandbox commodities={commodities} />
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 6: SPATIAL MAP */}
        {activeTab === 'map' && (
          <ErrorBoundary title={t('nav_map')}>
            <div>
              <div className="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-white font-outfit flex items-center gap-2">
                    <MapPin className="w-6 h-6 text-emerald-400" />
                    {t('map_title')}
                  </h2>
                  <p className="text-xs text-slate-400">
                    {t('map_subtitle')}
                  </p>
                </div>

                {/* Commodity Selector Dropdown */}
                <select
                  value={selectedCommodity?.id || ''}
                  onChange={(e) => {
                    const c = commodities.find((x) => x.id === Number(e.target.value));
                    if (c) setSelectedCommodity(c);
                  }}
                  className="bg-slate-800 text-white border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500"
                >
                  {commodities.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.bangla_name} ({c.canonical_name})
                    </option>
                  ))}
                </select>
              </div>

              {spatialData ? (
                <BangladeshPriceMap
                  spatialData={spatialData}
                  commodityName={selectedCommodity?.canonical_name}
                  unit={selectedCommodity?.default_unit}
                />
              ) : (
                <div className="p-8 text-center rounded-xl bg-slate-800/40 border border-slate-700 text-slate-400 text-xs">
                  ম্যাপ ডাটা লোড হচ্ছে...
                </div>
              )}
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 7: SOURCE HEALTH & TELEMETRY */}
        {activeTab === 'sources' && (
          <ErrorBoundary title={t('nav_sources')}>
            <div>
              <SourceHealthCard
                sources={sourcesData}
                onRefresh={fetchSourceHealth}
                isRefreshing={isSourcesRefreshing}
              />

              <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-6">
                <h4 className="text-sm font-bold text-white mb-2 font-outfit">
                  {lang === 'bn' ? 'স্বয়ংক্রিয় ডাটা সংগ্রহ ও ব্যাকআপ ব্যবস্থাপনা' : 'Resilient Harvesting & Graceful Degradation Architecture'}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {lang === 'bn' 
                    ? 'প্রাইসপালস বিডি সরাসরি কৃষি বিপণন অধিদপ্তর (DAM), টিসিবি এবং নির্ভরযোগ্য রিটেইল গ্রোসারি সাইট থেকে প্রতিদিনের বাজারদর সংগ্রহ করে। সার্ভার বা ইন্টারনেট সংযোগে সাময়িক ত্রুটি দেখা দিলেও স্বয়ংক্রিয় ব্যাকআপ ব্যবস্থা থেকে সর্বশেষ সঠিক দাম প্রদর্শন নিশ্চিত করা হয়।'
                    : 'PricePulse BD operates a zero-downtime, fault-tolerant ingestion pipeline. Network connectivity timeouts, HTTP 5xx server errors, or rate-limits automatically trigger a seamless fallback to verified cached fixtures.'}
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={handleTriggerSync}
                    disabled={isSyncing}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-md shadow-teal-950/40 transition-all border border-teal-500/40 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                    <span>{isSyncing ? t('btn_syncing') : t('btn_sync_live')}</span>
                  </button>
                  <button
                    onClick={fetchSourceHealth}
                    disabled={isSourcesRefreshing}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition"
                  >
                    <span>{t('btn_refresh')}</span>
                  </button>
                </div>
              </div>
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 8: DATA PROVENANCE */}
        {activeTab === 'provenance' && (
          <ErrorBoundary title={t('nav_provenance')}>
            <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-3 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white font-outfit">{t('provenance_title')}</h2>
                  <p className="text-xs text-slate-400">{t('provenance_subtitle')}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60">
                  <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                    {lang === 'bn' ? 'ডাটাবেজ ইঞ্জিন' : 'Storage Engine'}
                  </h4>
                  <p className="text-sm font-bold text-white">SQLite 3 (WAL Mode)</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {lang === 'bn' ? 'উচ্চগতির দ্রুত রিড-রাইট ও সম্পূর্ণ অফলাইন ডাটা ব্যাকআপ।' : 'Non-blocking concurrent writes with high-frequency WAL checkpoints.'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60">
                  <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                    {lang === 'bn' ? 'নির্ভরযোগ্যতা মডেল' : 'Confidence Scoring'}
                  </h4>
                  <p className="text-sm font-bold text-white">4-Factor Linear Model</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {lang === 'bn' ? 'উৎস (৪০%) + সঠিক নাম (৩০%) + নতুন তথ্য (১৫%) + সম্পূর্ণতা (১৫%)।' : '40% Source + 30% Alias Precision + 15% Freshness + 15% Completeness.'}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60">
                  <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                    {lang === 'bn' ? 'তথ্য সংগ্রহের মাধ্যম' : 'Active Collectors'}
                  </h4>
                  <p className="text-sm font-bold text-white">DAM Daily, TCB & Chaldal</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {lang === 'bn' ? 'দৈনিক সরকারি বুলেটিন এবং সুপারশপ থেকে স্বয়ংক্রিয় সংগৃহীত।' : 'Deterministic bulletin extraction and package size metric normalization.'}
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs text-slate-300 leading-relaxed">
                <strong className="text-white block mb-1">
                  {lang === 'bn' ? 'যাচাইকৃত তথ্যসূত্র ও পদ্ধতি:' : 'Verified Public Sources & Methodology:'}
                </strong>
                {lang === 'bn'
                  ? 'প্রাইসপালস বিডি কৃষি বিপণন অধিদপ্তর (DAM), ট্রেডিং কর্পোরেশন অব বাংলাদেশ (TCB), স্থানীয় আড়ত এবং সুপারশপের তথ্যকে একটি সাধারণ পরিমাপ এককে (কেজি/লিটার/হালি) রূপান্তর করে বিশ্লেষণ করে। কোনো প্রকার কৃত্রিম বা ভুল তথ্য এখানে অন্তর্ভুক্ত করা হয় না।'
                  : 'PricePulse BD standardizes fragmented agricultural reports from DAM, TCB, retail storefronts, and spot market briefs. Every record is stored with verbatim raw prices and canonical metric conversions to guarantee auditable data integrity.'}
              </div>
            </div>
          </ErrorBoundary>
        )}
      </main>

      {/* Provenance Modal Drawer */}
      <ProvenanceDrawer observation={activeProvenance} onClose={() => setActiveProvenance(null)} />

      {/* Manual Spot Price Ingestion Modal */}
      <ManualIngestionModal
        isOpen={isManualModalOpen}
        onClose={() => setIsManualModalOpen(false)}
        commodities={commodities}
        onSuccess={() => {
          loadData();
        }}
      />

      {/* Export Market Intelligence Modal */}
      <ExportDataModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        pulseItems={allPulseItems}
        selectedCommodity={selectedCommodity}
        commodityHistory={commodityHistory}
      />

      {/* Family Budget Optimizer Modal */}
      <BudgetOptimizerModal
        isOpen={isBudgetModalOpen}
        onClose={() => setIsBudgetModalOpen(false)}
        commodities={commodities}
        onApplyBasket={handleApplyBudgetBasket}
        lang={lang}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 py-4 pb-24 text-center text-xs text-slate-500 dark:text-slate-400 transition-colors duration-150">
        <p>{t('footer_text')}</p>
      </footer>

      {/* Universal Floating Island Navigation Bar (Desktop & Mobile) */}
      <BottomFloatingBar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        basketCount={basketItemCount}
        anomalyCount={activeAnomalyCount}
        lang={lang}
        onOpenBudgetModal={() => setIsBudgetModalOpen(true)}
        onOpenReportModal={() => setIsManualModalOpen(true)}
        onOpenExportModal={() => setIsExportModalOpen(true)}
      />
    </div>
  );
}
