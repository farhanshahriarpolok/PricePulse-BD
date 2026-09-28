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
  Info
} from 'lucide-react';

import Navbar from './components/Navbar';
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
import BazaarBasketView from './components/BazaarBasketView';
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

export default function App() {
  // Localization State - Default natural colloquial Bangla
  const [lang, setLang] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('pricepulse_lang') || 'bn';
    }
    return 'bn';
  });

  const toggleLang = () => {
    setLang((prev) => {
      const next = prev === 'bn' ? 'en' : 'bn';
      if (typeof window !== 'undefined') {
        localStorage.setItem('pricepulse_lang', next);
      }
      return next;
    });
  };

  const t = (key) => getTranslation(key, lang);

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
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [basketItemCount, setBasketItemCount] = useState(0);

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

    // Load 30-day history
    getCommodityHistory(selectedCommodity.id)
      .then((res) => setCommodityHistory(res?.series || []))
      .catch(() => setCommodityHistory([]));

    // Load spatial spread
    getLocationSpread(selectedCommodity.id)
      .then((res) => setSpatialData(res))
      .catch(() => setSpatialData(null));
  }, [selectedCommodity]);

  const activeAnomalyCount = anomaliesData?.anomalies_detected || 0;
  const allPulseItems = pulseData?.items || [];

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
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        anomalyCount={activeAnomalyCount}
        basketCount={basketItemCount}
        onRefresh={loadData}
        isRefreshing={isRefreshing}
        onOpenReportModal={() => setIsManualModalOpen(true)}
        onOpenExportModal={() => setIsExportModalOpen(true)}
        onTriggerSync={handleTriggerSync}
        isSyncing={isSyncing}
        syncToast={syncToast}
        lang={lang}
        onToggleLang={toggleLang}
      />

      {/* Horizontal Scrolling Live Market Ticker */}
      <MarketTicker
        items={allPulseItems}
        onSelectItem={(item) => {
          const matched = commodities.find((x) => x.id === item.commodity_id);
          if (matched) setSelectedCommodity(matched);
          setActiveTab('explorer');
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* TAB: BAZAAR BASKET */}
        {activeTab === 'basket' && (
          <ErrorBoundary title={t('nav_basket')}>
            <BazaarBasketView
              lang={lang}
              onBasketCountChange={setBasketItemCount}
            />
          </ErrorBoundary>
        )}

        {/* TAB 1: MARKET PULSE */}
        {activeTab === 'pulse' && (
          <ErrorBoundary title={t('nav_pulse')}>
            <div>
              <PulseSummaryCard pulseData={pulseData} anomalyCount={activeAnomalyCount} />

              <RealtimeSearch
                onSelectCommodity={(searched) => {
                  const matched = commodities.find((c) => c.canonical_name === searched.canonical_name);
                  if (matched) setSelectedCommodity(matched);
                  setActiveTab('explorer');
                }}
              />

              {/* Category Filter Chips */}
              <div className="flex items-center justify-between mt-6 mb-2">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider font-outfit">
                    {t('cat_filter_title')}
                  </h3>
                </div>
                <span className="text-xs font-mono text-slate-400">
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
              />

              {/* Daily Staples Grid */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white font-outfit">{t('pulse_title')}</h3>
                    <p className="text-xs text-slate-400">{t('pulse_subtitle')}</p>
                  </div>
                  <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded border border-slate-700">
                    {pulseData?.date || (lang === 'bn' ? 'আজকের রেট' : 'Live Today')}
                  </span>
                </div>

                {displayedPulseItems.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {/* Top Market Mover Hero Card */}
                    {topMover && selectedCategory === 'all' && (
                      <CommodityCard
                        item={topMover}
                        isHero={true}
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
                        onClick={() => {
                          const c = commodities.find((x) => x.id === item.commodity_id);
                          if (c) setSelectedCommodity(c);
                          setActiveTab('explorer');
                        }}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center rounded-xl bg-slate-800/40 border border-slate-700 text-slate-400 text-xs">
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
            <div>
              <div className="mb-4">
                <h3 className="text-base font-bold text-white font-outfit">{t('explorer_title')}</h3>
                <p className="text-xs text-slate-400">{t('explorer_select')}</p>
              </div>

              {/* Commodity Selector Pills */}
              <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-5 scrollbar-none">
                {commodities.map((comm) => {
                  const isSelected = selectedCommodity?.id === comm.id;
                  return (
                    <button
                      key={comm.id}
                      onClick={() => setSelectedCommodity(comm)}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all border ${
                        isSelected
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50 shadow-sm'
                          : 'bg-slate-800/60 text-slate-300 border-slate-700 hover:bg-slate-800'
                      }`}
                    >
                      <span>{comm.bangla_name || comm.canonical_name}</span>
                      <span className="ml-1.5 opacity-60 text-[10px]">({comm.canonical_name})</span>
                    </button>
                  );
                })}
              </div>

              {selectedCommodity ? (
                <>
                  <HistoricalTrendChart
                    historyData={commodityHistory}
                    commodityName={selectedCommodity.canonical_name}
                    unit={selectedCommodity.default_unit}
                  />

                  {spatialData && (
                    <ChannelComparisonCard
                      channels={spatialData.spread_summary}
                      unit={selectedCommodity.default_unit}
                    />
                  )}
                </>
              ) : (
                <div className="p-8 text-center rounded-xl bg-slate-800/40 border border-slate-700 text-slate-400 text-xs">
                  পণ্য সিলেক্ট করুন।
                </div>
              )}
            </div>
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

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/80 py-4 text-center text-xs text-slate-500">
        <p>{t('footer_text')}</p>
      </footer>
    </div>
  );
}
