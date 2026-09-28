import React, { useState, useEffect } from 'react';
import { 
  GitCompare, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle2, 
  MapPin, 
  Layers, 
  ArrowRight,
  Filter,
  BarChart3
} from 'lucide-react';
import { getComparisonData, getLocationHierarchy } from '../api/endpoints';

export default function ComparisonView({ commodities = [], onSelectCommodity }) {
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [districts, setDistricts] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize with top 3 commodities when loaded
  useEffect(() => {
    if (commodities.length > 0 && selectedIds.length === 0) {
      const initial = commodities.slice(0, 3).map((c) => c.id);
      setSelectedIds(initial);
    }
  }, [commodities]);

  // Load districts from location hierarchy
  useEffect(() => {
    getLocationHierarchy()
      .then((res) => {
        const distList = [];
        const divisions = res?.divisions || res?.data?.divisions || [];
        divisions.forEach((div) => {
          (div.districts || []).forEach((dist) => {
            distList.push({ id: dist.id, name: dist.name, division: div.name });
          });
        });
        setDistricts(distList);
      })
      .catch((err) => console.error('Failed to load districts', err));
  }, []);

  // Fetch comparison data whenever selectedIds or selectedDistrict change
  useEffect(() => {
    if (selectedIds.length === 0) {
      setComparisonData([]);
      return;
    }

    setIsLoading(true);
    const params = {
      ids: selectedIds.join(','),
      district_id: selectedDistrict ? parseInt(selectedDistrict, 10) : undefined,
    };

    getComparisonData(params)
      .then((res) => {
        const items = res?.items || res?.data?.items || (Array.isArray(res) ? res : []);
        setComparisonData(items);
      })
      .catch((err) => {
        console.error('Failed to fetch comparison data', err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [selectedIds, selectedDistrict]);

  const toggleCommodity = (id) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length > 1) {
        setSelectedIds(selectedIds.filter((item) => item !== id));
      }
    } else {
      if (selectedIds.length < 3) {
        setSelectedIds([...selectedIds, id]);
      } else {
        // Replace oldest selection
        setSelectedIds([...selectedIds.slice(1), id]);
      }
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header and Controls */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-indigo-400">
              <GitCompare className="w-5 h-5" />
              <h2 className="text-base font-bold text-white tracking-tight">Multi-Commodity Market Comparison Matrix</h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Analyze wholesale vs. retail price transmission spreads, 14-day trends, and volatility side-by-side (Select up to 3 staples).
            </p>
          </div>

          {/* District Filter Dropdown */}
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-slate-400" />
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">National Wholesale/Retail Average</option>
              {districts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.division})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Commodity Selector Pills */}
        <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap gap-2">
          {commodities.map((c) => {
            const isSelected = selectedIds.includes(c.id);
            return (
              <button
                key={c.id}
                onClick={() => toggleCommodity(c.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-950/40 ring-1 ring-indigo-400'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700/50'
                }`}
              >
                <span>{c.canonical_name}</span>
                <span className="text-[10px] opacity-75">({c.bangla_name})</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Loading Indicator */}
      {isLoading && (
        <div className="py-12 flex justify-center items-center space-x-2 text-indigo-400 text-sm">
          <div className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin"></div>
          <span>Computing side-by-side matrix metrics...</span>
        </div>
      )}

      {/* Side-by-Side Cards Matrix */}
      {!isLoading && comparisonData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {comparisonData.map((item) => {
            const isAnomaly = item.is_anomaly;
            const isPositiveDelta = (item.delta_pct || 0) > 0;
            return (
              <div
                key={item.commodity_id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg relative flex flex-col justify-between hover:border-slate-700 transition-all"
              >
                <div>
                  {/* Card Title & Status Tag */}
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {item.category}
                      </span>
                      <h3 className="text-base font-bold text-white mt-1.5">{item.canonical_name}</h3>
                      <p className="text-xs text-slate-400">{item.bangla_name}</p>
                    </div>
                    {isAnomaly ? (
                      <span className="px-2 py-1 rounded text-[10px] font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse">
                        {item.severity} {item.direction}
                      </span>
                    ) : (
                      <span className="px-2 py-1 rounded text-[10px] font-semibold uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Normal</span>
                      </span>
                    )}
                  </div>

                  {/* Primary Price Metric */}
                  <div className="mt-4 pt-3 border-t border-slate-800">
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-slate-400 font-medium">Retail Price:</span>
                      <span className="text-2xl font-black font-mono text-white">
                        {item.retail_price ? `${item.retail_price} BDT` : 'N/A'}
                        <span className="text-xs font-normal text-slate-400">/{item.unit}</span>
                      </span>
                    </div>

                    <div className="flex items-baseline justify-between mt-1 text-xs text-slate-400">
                      <span>Wholesale Hub:</span>
                      <span className="font-mono text-slate-300">
                        {item.wholesale_price ? `${item.wholesale_price} BDT/${item.unit}` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Markup Spread Bar */}
                  <div className="mt-3 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                    <div className="flex justify-between items-center text-xs mb-1">
                      <span className="text-slate-400">Wholesale Spread:</span>
                      <span className="font-mono font-bold text-indigo-400">
                        {item.spread_pct !== null ? `+${item.spread_pct}%` : 'N/A'}
                        {item.spread_bdt !== null && ` (+${item.spread_bdt} BDT)`}
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          (item.spread_pct || 0) > 30 ? 'bg-rose-500' : (item.spread_pct || 0) > 15 ? 'bg-amber-500' : 'bg-indigo-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(10, (item.spread_pct || 0) * 2))}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* 14-Day Baseline and Volatility Metrics */}
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded bg-slate-800/50 border border-slate-700/50">
                      <span className="text-[10px] text-slate-400 block">14d SMA Baseline</span>
                      <span className="font-mono text-slate-200 font-semibold">
                        {item.baseline_sma_14d ? `${item.baseline_sma_14d} BDT` : 'N/A'}
                      </span>
                      {item.delta_pct !== null && (
                        <span className={`text-[10px] block font-mono font-medium ${isPositiveDelta ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {isPositiveDelta ? '▲' : '▼'} {Math.abs(item.delta_pct)}%
                        </span>
                      )}
                    </div>

                    <div className="p-2 rounded bg-slate-800/50 border border-slate-700/50">
                      <span className="text-[10px] text-slate-400 block">Volatility (CV%)</span>
                      <span className="font-mono text-slate-200 font-semibold">
                        {item.volatility_cv !== null ? `${item.volatility_cv}%` : 'N/A'}
                      </span>
                      <span className="text-[10px] text-slate-400 block">
                        {(item.volatility_cv || 0) < 5 ? 'Stable' : (item.volatility_cv || 0) < 15 ? 'Moderate' : 'High'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Drilldown Trigger */}
                <button
                  onClick={() => onSelectCommodity && onSelectCommodity(item.commodity_id)}
                  className="mt-4 w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700/80 text-xs font-semibold text-slate-300 hover:text-white transition-all flex items-center justify-center space-x-1.5 border border-slate-700"
                >
                  <span>View Full 30d Historical Trend</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Side-by-Side Comparison Structured Table */}
      {!isLoading && comparisonData.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
          <div className="px-5 py-3.5 bg-slate-800/60 border-b border-slate-800 flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Comparative Analytical Matrix Breakdown
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/40 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Analytical Indicator</th>
                  {comparisonData.map((c) => (
                    <th key={c.commodity_id} className="py-3 px-4 font-semibold text-slate-200">
                      {c.canonical_name} <span className="text-[11px] text-slate-400 block font-normal">({c.bangla_name})</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">Base Metric Unit</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono font-semibold text-white">
                      1 {c.unit}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">Physical Retail Average</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono font-bold text-emerald-400">
                      {c.retail_price ? `${c.retail_price} BDT/${c.unit}` : 'N/A'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">Wholesale Terminal Price</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono text-slate-300">
                      {c.wholesale_price ? `${c.wholesale_price} BDT/${c.unit}` : 'N/A'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">Channel Markup Spread</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        (c.spread_pct || 0) > 30 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-indigo-500/20 text-indigo-400'
                      }`}>
                        {c.spread_pct !== null ? `+${c.spread_pct}%` : 'N/A'}
                      </span>
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">14-Day SMA Equilibrium</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono text-slate-200">
                      {c.baseline_sma_14d ? `${c.baseline_sma_14d} BDT` : 'N/A'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">14-Day Relative Departure (Δ%)</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono font-semibold">
                      {c.delta_pct !== null ? (
                        <span className={c.delta_pct > 0 ? 'text-rose-400' : 'text-emerald-400'}>
                          {c.delta_pct > 0 ? '+' : ''}{c.delta_pct}%
                        </span>
                      ) : 'N/A'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">Volatility Index (CV%)</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4 font-mono text-slate-200">
                      {c.volatility_cv !== null ? `${c.volatility_cv}%` : 'N/A'}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-medium text-slate-400">Statistical Anomaly Status</td>
                  {comparisonData.map((c) => (
                    <td key={c.commodity_id} className="py-2.5 px-4">
                      {c.is_anomaly ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/30">
                          {c.severity} {c.direction}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase bg-emerald-500/10 text-emerald-400">
                          Normal
                        </span>
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
