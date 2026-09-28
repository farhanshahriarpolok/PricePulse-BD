import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileCode, CheckCircle, X, Layers } from 'lucide-react';

export default function ExportDataModal({
  isOpen,
  onClose,
  pulseItems = [],
  selectedCommodity,
  commodityHistory = [],
}) {
  if (!isOpen) return null;

  const [exportScope, setExportScope] = useState('pulse'); // 'pulse' | 'history'
  const [downloadSuccess, setDownloadSuccess] = useState(null);

  const downloadFile = (content, filename, mimeType) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setDownloadSuccess(filename);
    setTimeout(() => setDownloadSuccess(null), 3500);
  };

  const handleExportCSV = () => {
    const todayStr = new Date().toISOString().split('T')[0];

    if (exportScope === 'pulse') {
      const headers = ['Commodity ID', 'Canonical Name', 'Bangla Name', 'Category', 'Unit', 'Avg Price (BDT)', 'Min Price', 'Max Price', 'Samples', 'Status', 'Date'];
      const rows = pulseItems.map((item) => [
        item.commodity_id,
        `"${item.canonical_name || ''}"`,
        `"${item.bangla_name || ''}"`,
        `"${item.category || ''}"`,
        `"${item.unit || ''}"`,
        item.price_summary?.avg_price?.toFixed(2) || '0.00',
        item.price_summary?.min_price?.toFixed(2) || '0.00',
        item.price_summary?.max_price?.toFixed(2) || '0.00',
        item.price_summary?.sample_count || 0,
        `"${item.price_status || 'Normal'}"`,
        todayStr,
      ]);

      const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
      downloadFile(csvContent, `pricepulse_daily_pulse_${todayStr}.csv`, 'text/csv;charset=utf-8;');
    } else {
      const commName = (selectedCommodity?.canonical_name || 'commodity').replace(/\s+/g, '_').toLowerCase();
      const headers = ['Date', 'Avg Price (BDT)', 'Min Price', 'Max Price', 'Wholesale Price', 'Retail Price', 'Online Price', 'Sample Count'];
      const rows = commodityHistory.map((h) => [
        h.date,
        h.avg_price?.toFixed(2) || '0.00',
        h.min_price?.toFixed(2) || '0.00',
        h.max_price?.toFixed(2) || '0.00',
        h.wholesale_avg?.toFixed(2) || '',
        h.retail_avg?.toFixed(2) || '',
        h.online_avg?.toFixed(2) || '',
        h.sample_count || 1,
      ]);

      const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
      downloadFile(csvContent, `pricepulse_${commName}_history_${todayStr}.csv`, 'text/csv;charset=utf-8;');
    }
  };

  const handleExportJSON = () => {
    const todayStr = new Date().toISOString().split('T')[0];

    if (exportScope === 'pulse') {
      const payload = {
        platform: 'PricePulse BD',
        exported_at: new Date().toISOString(),
        total_items: pulseItems.length,
        items: pulseItems,
      };
      downloadFile(JSON.stringify(payload, null, 2), `pricepulse_daily_pulse_${todayStr}.json`, 'application/json');
    } else {
      const payload = {
        platform: 'PricePulse BD',
        commodity: selectedCommodity,
        exported_at: new Date().toISOString(),
        total_days: commodityHistory.length,
        history: commodityHistory,
      };
      const commName = (selectedCommodity?.canonical_name || 'commodity').replace(/\s+/g, '_').toLowerCase();
      downloadFile(JSON.stringify(payload, null, 2), `pricepulse_${commName}_history_${todayStr}.json`, 'application/json');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl p-6 relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-outfit">Export Market Intelligence Data</h3>
              <p className="text-xs text-slate-400">Download canonical prices in standard CSV or structured JSON formats</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="py-5 space-y-4">
          {/* Scope Selector */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-2">Export Scope:</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setExportScope('pulse')}
                className={`p-3 rounded-xl border text-left transition ${
                  exportScope === 'pulse'
                    ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                    : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:bg-slate-800'
                }`}
              >
                <div className="font-semibold text-xs text-emerald-400 mb-0.5">Today's Pulse Basket</div>
                <div className="text-[11px] text-slate-400">
                  {pulseItems.length} active commodities across retail & wholesale
                </div>
              </button>

              <button
                type="button"
                onClick={() => setExportScope('history')}
                className={`p-3 rounded-xl border text-left transition ${
                  exportScope === 'history'
                    ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                    : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:bg-slate-800'
                }`}
              >
                <div className="font-semibold text-xs text-emerald-400 mb-0.5">
                  {selectedCommodity?.canonical_name || 'Selected Item'} History
                </div>
                <div className="text-[11px] text-slate-400">
                  {commodityHistory.length} daily observations with channel spreads
                </div>
              </button>
            </div>
          </div>

          {/* Download Buttons */}
          <div className="pt-2">
            <label className="text-xs font-semibold text-slate-300 block mb-2">Choose Format:</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleExportCSV}
                className="flex items-center justify-center gap-2 p-3 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 hover:border-emerald-500/40 text-white text-xs font-semibold transition group shadow-sm"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                <span>Export as CSV (.csv)</span>
              </button>

              <button
                onClick={handleExportJSON}
                className="flex items-center justify-center gap-2 p-3 rounded-xl bg-slate-800 hover:bg-slate-750 border border-slate-700 hover:border-teal-500/40 text-white text-xs font-semibold transition group shadow-sm"
              >
                <FileCode className="w-4 h-4 text-teal-400 group-hover:scale-110 transition-transform" />
                <span>Export as JSON (.json)</span>
              </button>
            </div>
          </div>

          {/* Success Banner */}
          {downloadSuccess && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs animate-fade-in">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Downloaded: <strong className="font-mono text-white">{downloadSuccess}</strong></span>
            </div>
          )}

          {/* Metadata Note */}
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
            Exports include UTF-8 BOM encoding for seamless display in Microsoft Excel, Google Sheets, and pandas.
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
