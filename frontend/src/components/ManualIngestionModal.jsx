import React, { useState, useEffect } from 'react';
import { 
  X, 
  Send, 
  CheckCircle, 
  AlertCircle, 
  ShieldAlert, 
  Sparkles,
  Info,
  Calendar
} from 'lucide-react';
import { submitManualObservation, getLocationHierarchy } from '../api/endpoints';

export default function ManualIngestionModal({ isOpen, onClose, commodities = [], onSuccess }) {
  const [commodityId, setCommodityId] = useState('');
  const [marketId, setMarketId] = useState('');
  const [price, setPrice] = useState('');
  const [rawUnit, setRawUnit] = useState('কেজি');
  const [marketTier, setMarketTier] = useState('retail');
  const [reporterName, setReporterName] = useState('');
  const [reporterNote, setReporterNote] = useState('');
  const [hierarchy, setHierarchy] = useState([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successData, setSuccessData] = useState(null);

  // Unit options supported by the normalization engine
  const unitOptions = [
    { label: 'কেজি (Kilogram)', value: 'কেজি', base: 'kg', div: 1 },
    { label: 'হালি (4 Pieces)', value: 'হালি', base: 'pc', div: 4 },
    { label: 'ডজন (12 Pieces)', value: 'ডজন', base: 'pc', div: 12 },
    { label: 'লিটার (Liter)', value: 'লিটার', base: 'liter', div: 1 },
    { label: 'মণ (40 kg Wholesale)', value: 'মণ', base: 'kg', div: 40 },
    { label: 'গ্রাম (1000g = 1kg)', value: 'গ্রাম', base: 'kg', div: 0.001 },
  ];

  // Fetch location hierarchy for markets dropdown
  useEffect(() => {
    if (isOpen) {
      getLocationHierarchy()
        .then((res) => {
          const divs = res?.divisions || res?.data?.divisions || [];
          setHierarchy(divs);
          // Auto select first market once hierarchy loaded
          const mkts = [];
          divs.forEach((d) => (d.districts || []).forEach((dist) => (dist.markets || []).forEach((m) => mkts.push(m))));
          if (mkts.length > 0 && !marketId) {
            setMarketId(mkts[0].id);
          }
        })
        .catch((err) => {
          console.error('Failed to load locations', err);
        });
      // Reset form on open
      setErrorMsg(null);
      setSuccessData(null);
      if (commodities.length > 0 && !commodityId) {
        setCommodityId(commodities[0].id);
      }
    }
  }, [isOpen, commodities]);

  if (!isOpen) return null;

  // Flatten all markets from hierarchy
  const allMarkets = [];
  hierarchy.forEach((div) => {
    (div.districts || []).forEach((dist) => {
      (dist.markets || []).forEach((mkt) => {
        allMarkets.push({
          id: mkt.id,
          name: mkt.name,
          banglaName: mkt.bangla_name,
          district: dist.name,
          division: div.name,
        });
      });
    });
  });

  // Calculate live preview of normalized price
  const selectedUnit = unitOptions.find((u) => u.value === rawUnit) || unitOptions[0];
  const numPrice = parseFloat(price);
  const estimatedNormalizedPrice = !isNaN(numPrice) && numPrice > 0 
    ? (numPrice / selectedUnit.div).toFixed(2) 
    : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessData(null);

    if (!commodityId) {
      setErrorMsg('Please select a valid commodity.');
      return;
    }
    if (!marketId) {
      setErrorMsg('Please select a physical market location.');
      return;
    }
    if (isNaN(numPrice) || numPrice <= 0) {
      setErrorMsg('Quoted price must be greater than zero.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        commodity_id: parseInt(commodityId, 10),
        market_id: parseInt(marketId, 10),
        price: numPrice,
        raw_unit: rawUnit,
        market_tier: marketTier,
        reporter_note: reporterNote.trim() || null,
        reporter_name: reporterName.trim() || null,
      };

      const res = await submitManualObservation(payload);
      setSuccessData(res?.data || res);
      if (onSuccess) onSuccess(res?.data || res);
    } catch (err) {
      console.error(err);
      const detail = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to submit observation';
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Report Spot Market Price</h3>
              <p className="text-xs text-slate-400">Human-in-the-Loop Field Observation Ingestion</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success Banner */}
        {successData && (
          <div className="p-6 bg-emerald-950/40 border-b border-emerald-800/40">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-emerald-300">Observation Successfully Recorded</h4>
                <p className="text-xs text-emerald-400/90 mt-1">
                  Normalized to <strong className="text-white font-mono">{successData.normalized_price} BDT/{successData.normalized_unit}</strong>
                  {' '}with initial confidence score of <strong className="text-white font-mono">{(successData.confidence_score * 100).toFixed(1)}%</strong> (Tier 4 Field Baseline).
                </p>
                <div className="mt-4 flex space-x-2">
                  <button
                    onClick={() => {
                      setSuccessData(null);
                      setPrice('');
                      setReporterNote('');
                    }}
                    className="px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold"
                  >
                    Submit Another Quote
                  </button>
                  <button
                    onClick={onClose}
                    className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Close Modal
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        {!successData && (
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {/* Commodity Select */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Target Commodity <span className="text-rose-400">*</span>
              </label>
              <select
                value={commodityId}
                onChange={(e) => setCommodityId(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                required
              >
                <option value="">-- Choose Essential Staple --</option>
                {commodities.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.canonical_name} ({c.bangla_name}) • [{c.category}]
                  </option>
                ))}
              </select>
            </div>

            {/* Market Select */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Market Location <span className="text-rose-400">*</span>
              </label>
              <select
                value={marketId}
                onChange={(e) => setMarketId(e.target.value)}
                className="w-full bg-slate-800/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                required
              >
                <option value="">-- Select Market Hub --</option>
                {allMarkets.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.district}) — {m.division}
                  </option>
                ))}
              </select>
            </div>

            {/* Price and Unit Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Observed Price (BDT) <span className="text-rose-400">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.1"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="e.g. 52.00"
                  className="w-full bg-slate-800/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white font-mono placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Unit Specification <span className="text-rose-400">*</span>
                </label>
                <select
                  value={rawUnit}
                  onChange={(e) => setRawUnit(e.target.value)}
                  className="w-full bg-slate-800/90 border border-slate-700/80 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  {unitOptions.map((u) => (
                    <option key={u.value} value={u.value}>
                      {u.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Market Tier Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Market Channel</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setMarketTier('retail')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                    marketTier === 'retail'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-sm'
                      : 'bg-slate-800/50 text-slate-400 border-slate-700/60 hover:text-slate-300'
                  }`}
                >
                  Physical Retail (কাঁচাবাজার)
                </button>
                <button
                  type="button"
                  onClick={() => setMarketTier('wholesale')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                    marketTier === 'wholesale'
                      ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/40 shadow-sm'
                      : 'bg-slate-800/50 text-slate-400 border-slate-700/60 hover:text-slate-300'
                  }`}
                >
                  Wholesale Hub (পাইকারি আড়ত)
                </button>
              </div>
            </div>

            {/* Live Normalization Preview Box */}
            {estimatedNormalizedPrice && (
              <div className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2 text-slate-300">
                  <Info className="w-4 h-4 text-emerald-400" />
                  <span>Standardized Equivalent:</span>
                </div>
                <div className="text-right">
                  <span className="font-mono text-emerald-400 font-bold text-sm">
                    {estimatedNormalizedPrice} BDT/{selectedUnit.base}
                  </span>
                  <span className="block text-[10px] text-slate-400">
                    Confidence: ~84.0% (Tier 4 Dampener)
                  </span>
                </div>
              </div>
            )}

            {/* Optional Reporter Info */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Reporter Name (Optional)
                </label>
                <input
                  type="text"
                  value={reporterName}
                  onChange={(e) => setReporterName(e.target.value)}
                  placeholder="e.g. Inspector Rahim"
                  className="w-full bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Observation Context (Optional)
                </label>
                <input
                  type="text"
                  value={reporterNote}
                  onChange={(e) => setReporterNote(e.target.value)}
                  placeholder="e.g. Supply low due to transit rain"
                  className="w-full bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-500"
                />
              </div>
            </div>

            {/* Field Integrity Notice */}
            <div className="flex items-start space-x-2 text-[11px] text-slate-400 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
              <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>
                Manual submissions are logged under <code className="text-amber-300">source_id='field_report'</code> with a calibrated 0.60 reliability scalar to prevent outlier poisoning until peer corroborated.
              </span>
            </div>

            {/* Submit Button */}
            <div className="pt-2 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center space-x-1.5 px-5 py-2 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-all disabled:opacity-50 shadow-md shadow-emerald-900/30"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{isSubmitting ? 'Verifying & Saving...' : 'Submit Quote'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
