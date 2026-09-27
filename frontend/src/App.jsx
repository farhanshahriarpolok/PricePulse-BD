import React, { useState, useEffect } from 'react';
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

import {
  getDailyPulse,
  getCommodities,
  getCommodityHistory,
  getActiveAnomalies,
  getLocationSpread,
  explainAnomaly,
} from './api/endpoints';

export default function App() {
  const [activeTab, setActiveTab] = useState('pulse');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);

  // Global State
  const [pulseData, setPulseData] = useState(null);
  const [commodities, setCommodities] = useState([]);
  const [selectedCommodity, setSelectedCommodity] = useState(null);
  const [commodityHistory, setCommodityHistory] = useState([]);
  const [anomaliesData, setAnomaliesData] = useState(null);
  const [spatialData, setSpatialData] = useState(null);
  const [activeProvenance, setActiveProvenance] = useState(null);


  // Load initial datasets
  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [pulseRes, commsRes, anomaliesRes] = await Promise.all([
        getDailyPulse().catch(() => null),
        getCommodities().catch(() => ({ items: [] })),
        getActiveAnomalies().catch(() => ({ anomalies: [] })),
      ]);

      setPulseData(pulseRes);
      setCommodities(commsRes?.items || []);
      setAnomaliesData(anomaliesRes);

      // Default select the first commodity (or Onion)
      const initialComm = commsRes?.items?.find((c) => c.canonical_name.includes('Onion')) || commsRes?.items?.[0];
      if (initialComm) {
        setSelectedCommodity(initialComm);
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

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        anomalyCount={activeAnomalyCount}
        onRefresh={loadData}
        isRefreshing={isRefreshing}
        onOpenReportModal={() => setIsManualModalOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* TAB 1: MARKET PULSE */}
        {activeTab === 'pulse' && (
          <div>
            <PulseSummaryCard pulseData={pulseData} anomalyCount={activeAnomalyCount} />

            <RealtimeSearch
              onSelectCommodity={(searched) => {
                const matched = commodities.find((c) => c.canonical_name === searched.canonical_name);
                if (matched) setSelectedCommodity(matched);
                setActiveTab('explorer');
              }}
            />


            {/* Daily Staples Grid */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-white font-outfit">Today's Essential Staples Pulse</h3>
                  <p className="text-xs text-slate-400">Canonical market benchmark prices across wholesale and retail tiers.</p>
                </div>
                <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded border border-slate-700">
                  {pulseData?.date || 'Live Today'}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {pulseData?.items?.map((item) => (
                  <div
                    key={item.commodity_id}
                    onClick={() => {
                      const c = commodities.find((x) => x.id === item.commodity_id);
                      if (c) setSelectedCommodity(c);
                      setActiveTab('explorer');
                    }}
                    className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/80 hover:border-emerald-500/50 cursor-pointer transition shadow-sm hover:shadow-emerald-950/20 group"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                        {item.category}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        item.price_status === 'High'
                          ? 'bg-rose-500/20 text-rose-300'
                          : item.price_status === 'Elevated'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {item.price_status}
                      </span>
                    </div>

                    <div className="text-base font-bold text-white group-hover:text-emerald-400 transition-colors">
                      {item.canonical_name}
                    </div>
                    <div className="text-xs text-slate-400 mb-3 font-bengali">
                      {item.bangla_name}
                    </div>

                    <div className="pt-2 border-t border-slate-700/60 flex items-baseline justify-between">
                      <div>
                        <span className="text-xs text-slate-400">Avg Benchmark:</span>
                        <div className="text-xl font-bold font-outfit text-white">
                          BDT {item.price_summary.avg_price.toFixed(2)}
                          <span className="text-xs font-normal text-slate-400"> /{item.unit}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: COMPARE MARKETS */}
        {activeTab === 'compare' && (
          <ComparisonView
            commodities={commodities}
            onSelectCommodity={(id) => {
              const matched = commodities.find((c) => c.id === id);
              if (matched) setSelectedCommodity(matched);
              setActiveTab('explorer');
            }}
          />
        )}

        {/* TAB 3: COMMODITY EXPLORER */}
        {activeTab === 'explorer' && (

          <div>
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
                    <span>{comm.canonical_name}</span>
                    <span className="ml-1.5 opacity-60 font-bengali">({comm.bangla_name})</span>
                  </button>
                );
              })}
            </div>

            {selectedCommodity && (
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
            )}
          </div>
        )}

        {/* TAB 3: ANOMALY MONITOR */}
        {activeTab === 'anomalies' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white font-outfit flex items-center gap-2">
                <AlertTriangle className="w-6 h-6 text-rose-400" />
                Active Commodity Price Anomaly Monitor
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Deterministic detection via rolling 14-day Z-scores (|Z| ≥ 1.5) and compound percentage deviation (|Δ%| ≥ 10%).
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
                <h3 className="text-base font-bold text-white">All Commodities in Statistical Equilibrium</h3>
                <p className="text-xs text-slate-400 mt-1">No anomalous price spikes or sudden declines detected today.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: SPATIAL MAP */}
        {activeTab === 'map' && (
          <div>
            <div className="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold text-white font-outfit flex items-center gap-2">
                  <MapPin className="w-6 h-6 text-emerald-400" />
                  Bangladesh Inter-District Geospatial Price Map
                </h2>
                <p className="text-xs text-slate-400">
                  OpenStreetMap Leaflet visualization of spatial price dispersion across wholesale and retail centers.
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
                    {c.canonical_name} ({c.bangla_name})
                  </option>
                ))}
              </select>
            </div>

            {spatialData && (
              <BangladeshPriceMap
                spatialData={spatialData}
                commodityName={selectedCommodity?.canonical_name}
                unit={selectedCommodity?.default_unit}
              />
            )}
          </div>
        )}

        {/* TAB 5: DATA PROVENANCE */}
        {activeTab === 'provenance' && (
          <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/20">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white font-outfit">Auditable Data Provenance & Architecture</h2>
                <p className="text-xs text-slate-400">Undergraduate CSE Final Year Project • Transparent Local-First Pipeline</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60">
                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Storage Engine</h4>
                <p className="text-sm font-bold text-white">SQLite 3 (WAL Mode)</p>
                <p className="text-xs text-slate-400 mt-1">Non-blocking concurrent writes with high-frequency WAL checkpoints.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60">
                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Confidence Scoring</h4>
                <p className="text-sm font-bold text-white">4-Factor Linear Model</p>
                <p className="text-xs text-slate-400 mt-1">40% Source + 30% Alias Precision + 15% Freshness + 15% Completeness.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60">
                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Active Collectors</h4>
                <p className="text-sm font-bold text-white">DAM Daily & Chaldal Retail</p>
                <p className="text-xs text-slate-400 mt-1">Deterministic bulletin extraction and package size metric normalization.</p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-700/80 text-xs text-slate-300 leading-relaxed">
              <strong className="text-white block mb-1">Academic & Research Transparency:</strong>
              PricePulse BD standardizes fragmented agricultural reports from the Department of Agricultural Marketing (DAM) and consumer grocery platforms. Every record is stored with verbatim raw prices and canonical metric conversions to prevent data tampering.
            </div>
          </div>
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

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/80 py-4 text-center text-xs text-slate-500">
        <p>PricePulse BD • CSE Final Year Project • Academic Research Platform</p>
      </footer>
    </div>
  );
}

