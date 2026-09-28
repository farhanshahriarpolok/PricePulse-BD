import React from 'react';
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
  CheckCircle,
  Radio,
  Download
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  anomalyCount = 0, 
  onRefresh, 
  isRefreshing = false,
  onOpenReportModal,
  onOpenExportModal,
  onTriggerSync,
  isSyncing = false,
  syncToast = null,
}) {
  const navItems = [
    { id: 'pulse', label: 'Market Pulse', icon: Activity },
    { id: 'compare', label: 'Compare Markets', icon: GitCompare },
    { id: 'explorer', label: 'Commodity Explorer', icon: TrendingUp },
    { id: 'anomalies', label: 'Anomaly Monitor', icon: AlertTriangle, count: anomalyCount },
    { id: 'map', label: 'Spatial Map', icon: MapPin },
    { id: 'sources', label: 'Source Health', icon: Server },
    { id: 'provenance', label: 'Data Provenance', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Header */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('pulse')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-900/30">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white font-outfit">PricePulse</span>
                <span className="px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded">BD</span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">CSE Research Capstone • Live Intelligence</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.count > 0 && (
                    <span className="ml-1 px-1.5 py-0.2 text-[10px] font-bold rounded-full bg-rose-500 text-white animate-pulse">
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* System Status & Ingestion Trigger */}
          <div className="flex items-center space-x-2.5">
            {/* Dynamic Sync Live Data Button */}
            <button
              onClick={onTriggerSync}
              disabled={isSyncing}
              title="Harvest live market data from DAM and Chaldal"
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold shadow-md shadow-teal-950/40 transition-all border border-teal-500/40 disabled:opacity-60"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Syncing...' : 'Sync Live Data'}</span>
            </button>

            {/* Export Data Button */}
            <button
              onClick={onOpenExportModal}
              title="Export Market Intelligence Data (CSV / JSON)"
              className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 transition-all"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Export</span>
            </button>

            {/* Primary Action Button */}
            <button
              onClick={onOpenReportModal}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-950/40 transition-all border border-emerald-500/40"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Report Price</span>
            </button>

            <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <Database className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-mono text-slate-300 text-[11px]">SQLite WAL</span>
            </div>

            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Refresh Market Data"
              className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/50 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
            </button>
          </div>
        </div>

        {/* Dynamic Sync Status Toast */}
        {syncToast && (
          <div className="bg-slate-800/95 border border-teal-500/40 px-4 py-2 text-xs flex items-center justify-between rounded-lg mb-2 shadow-lg animate-fadeIn">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-teal-400 animate-pulse" />
              <span className="text-white font-medium">{syncToast.message}</span>
            </div>
            {syncToast.details && (
              <span className="text-teal-300 text-[11px] font-mono">{syncToast.details}</span>
            )}
          </div>
        )}


        {/* Mobile Navigation Row */}
        <div className="flex md:hidden overflow-x-auto py-2 space-x-1 border-t border-slate-800/80 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  isActive
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
                {item.count > 0 && (
                  <span className="px-1 text-[10px] rounded-full bg-rose-500 text-white">
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
