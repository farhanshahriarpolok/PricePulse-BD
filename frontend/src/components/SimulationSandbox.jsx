import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Sliders,
  Play,
  RotateCcw,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ShieldCheck,
  Info,
  Layers,
  Sparkles,
  Activity,
  CheckCircle2,
  FileText
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceArea
} from 'recharts';
import { injectShock } from '../api/endpoints';

export default function SimulationSandbox({ commodities = [] }) {
  const defaultCommodity = commodities.find((c) => c.canonical_name.includes('Onion')) || commodities[0] || { id: 1, canonical_name: 'Onion (Local)', default_unit: 'kg' };

  const [selectedCommodityId, setSelectedCommodityId] = useState(defaultCommodity.id);
  const [shockPercentage, setShockPercentage] = useState(35);
  const [shockDuration, setShockDuration] = useState(4);
  const [shockType, setShockType] = useState('Supply Disruption');
  const [baselineAdjustment, setBaselineAdjustment] = useState(0);
  const [noiseLevel, setNoiseLevel] = useState(2);

  const [simulationResult, setSimulationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Execute simulation API
  const runSimulation = useCallback(async (overrides = {}) => {
    const cId = overrides.commodityId !== undefined ? overrides.commodityId : selectedCommodityId;
    const sPct = overrides.shockPercentage !== undefined ? overrides.shockPercentage : shockPercentage;
    const sDur = overrides.shockDuration !== undefined ? overrides.shockDuration : shockDuration;
    const sType = overrides.shockType !== undefined ? overrides.shockType : shockType;
    const bAdj = overrides.baselineAdjustment !== undefined ? overrides.baselineAdjustment : baselineAdjustment;
    const nLvl = overrides.noiseLevel !== undefined ? overrides.noiseLevel : noiseLevel;

    setIsLoading(true);
    setError(null);
    try {
      const res = await injectShock({
        commodity_id: Number(cId),
        shock_percentage: Number(sPct),
        shock_duration_days: Number(sDur),
        shock_type: sType,
        baseline_adjustment_pct: Number(bAdj),
        noise_level: Number(nLvl),
      });
      setSimulationResult(res);
    } catch (err) {
      console.error('Simulation error:', err);
      setError(err?.message || 'Failed to calculate simulation response.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedCommodityId, shockPercentage, shockDuration, shockType, baselineAdjustment, noiseLevel]);

  // Debounced auto-execution on slider changes
  useEffect(() => {
    const timer = setTimeout(() => {
      runSimulation();
    }, 180);
    return () => clearTimeout(timer);
  }, [selectedCommodityId, shockPercentage, shockDuration, shockType, baselineAdjustment, noiseLevel, runSimulation]);

  // Preset Scenario Handlers
  const applyPreset = (presetName) => {
    if (presetName === 'onion_shock') {
      const onion = commodities.find((c) => c.canonical_name.includes('Onion')) || commodities[0];
      if (onion) setSelectedCommodityId(onion.id);
      setShockPercentage(45);
      setShockDuration(4);
      setShockType('Supply Disruption');
      setBaselineAdjustment(5);
      setNoiseLevel(2);
    } else if (presetName === 'transport_strike') {
      setShockPercentage(25);
      setShockDuration(5);
      setShockType('Transport Strike');
      setBaselineAdjustment(0);
      setNoiseLevel(4);
    } else if (presetName === 'import_tariff') {
      setShockPercentage(30);
      setShockDuration(7);
      setShockType('Import Tariff');
      setBaselineAdjustment(10);
      setNoiseLevel(1);
    } else if (presetName === 'bumper_harvest') {
      const potato = commodities.find((c) => c.canonical_name.includes('Potato')) || commodities[0];
      if (potato) setSelectedCommodityId(potato.id);
      setShockPercentage(-28);
      setShockDuration(4);
      setShockType('Bumper Harvest');
      setBaselineAdjustment(-5);
      setNoiseLevel(2);
    } else if (presetName === 'equilibrium') {
      setShockPercentage(0);
      setShockDuration(3);
      setShockType('Equilibrium');
      setBaselineAdjustment(0);
      setNoiseLevel(0);
    }
  };

  const currentCommodity = useMemo(() => {
    return commodities.find((c) => c.id === Number(selectedCommodityId)) || defaultCommodity;
  }, [commodities, selectedCommodityId, defaultCommodity]);

  // Severity styling
  const getSeverityBadge = (severity, direction) => {
    if (severity === 'Critical') {
      return (
        <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1.5 animate-pulse">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          Critical {direction || 'Anomaly'}
        </span>
      );
    }
    if (severity === 'Severe') {
      return (
        <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-orange-500/20 text-orange-300 border border-orange-500/40 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-orange-400" />
          Severe {direction || 'Anomaly'}
        </span>
      );
    }
    if (severity === 'Moderate') {
      return (
        <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          Moderate {direction || 'Anomaly'}
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        Normal Equilibrium
      </span>
    );
  };

  const chartData = useMemo(() => {
    if (!simulationResult?.time_series) return [];
    return simulationResult.time_series.map((pt) => ({
      date: pt.date ? pt.date.slice(5) : '',
      'Observed Baseline': pt.observed_price,
      'Simulated Series': pt.simulated_price,
      '14d Rolling SMA': pt.baseline_sma_14d,
      is_shock: pt.is_shock_period,
    }));
  }, [simulationResult]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 shadow-xl shadow-indigo-950/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
                <Sliders className="w-5 h-5" />
              </div>
              <h2 className="text-xl font-bold text-white font-outfit tracking-tight">
                Viva Defense Interactive Simulation Sandbox
              </h2>
              <span className="px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full">
                Live Examiner Testbed
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-2 max-w-3xl leading-relaxed">
              Dynamically stress-test the statistical anomaly detection engine. Adjust supply shocks, freight tariffs,
              and volatility sliders to evaluate real-time Rolling SMA, Standard Deviation, Z-Scores, and explainable
              natural language output generation without mutating canonical database records.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => applyPreset('onion_shock')}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 transition-all flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 text-rose-400" />
              Onion Shock (+45%)
            </button>
            <button
              onClick={() => applyPreset('transport_strike')}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 transition-all flex items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5 text-amber-400" />
              Freight Strike (+25%)
            </button>
            <button
              onClick={() => applyPreset('bumper_harvest')}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 transition-all flex items-center gap-1.5"
            >
              <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
              Bumper Crop (-28%)
            </button>
            <button
              onClick={() => applyPreset('equilibrium')}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset (0%)
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Control Sliders (Left) vs Output & Chart (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Simulation Controls
            </h3>

            {/* Commodity Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Target Canonical Commodity
              </label>
              <select
                value={selectedCommodityId}
                onChange={(e) => setSelectedCommodityId(Number(e.target.value))}
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-indigo-500"
              >
                {commodities.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.canonical_name} ({c.bangla_name})
                  </option>
                ))}
              </select>
            </div>

            {/* Shock Archetype Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Economic Shock Archetype
              </label>
              <select
                value={shockType}
                onChange={(e) => setShockType(e.target.value)}
                className="w-full bg-slate-800 text-white border border-slate-700 rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-indigo-500"
              >
                <option value="Supply Disruption">Sudden Supply Disruption (Production Loss / Border Stoppage)</option>
                <option value="Import Tariff">Import Duty Hike / Regulatory Tariff</option>
                <option value="Transport Strike">Inter-District Freight Strike / Blockade</option>
                <option value="Cartel Hoarding">Syndicate / Wholesaler Speculative Hoarding</option>
                <option value="Bumper Harvest">Bumper Harvest Flush (Excess Supply)</option>
                <option value="Equilibrium">Baseline Equilibrium (No Disturbance)</option>
              </select>
            </div>

            {/* Shock Percentage Slider */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-300">Injected Price Shift (Δ%)</span>
                <span className={`font-mono font-bold ${shockPercentage > 0 ? 'text-rose-400' : shockPercentage < 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                  {shockPercentage > 0 ? `+${shockPercentage}%` : `${shockPercentage}%`}
                </span>
              </div>
              <input
                type="range"
                min="-50"
                max="100"
                step="1"
                value={shockPercentage}
                onChange={(e) => setShockPercentage(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                <span>-50% (Crash)</span>
                <span>0%</span>
                <span>+50%</span>
                <span>+100% (Crisis)</span>
              </div>
            </div>

            {/* Shock Duration Slider */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-300">Shock Window Duration</span>
                <span className="font-mono font-bold text-indigo-400">{shockDuration} Days</span>
              </div>
              <input
                type="range"
                min="1"
                max="14"
                step="1"
                value={shockDuration}
                onChange={(e) => setShockDuration(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                <span>1 Day (Flash)</span>
                <span>7 Days</span>
                <span>14 Days (Full Window)</span>
              </div>
            </div>

            {/* Baseline Shift Slider */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-300">Baseline Price Drift</span>
                <span className="font-mono font-bold text-slate-300">{baselineAdjustment > 0 ? `+${baselineAdjustment}%` : `${baselineAdjustment}%`}</span>
              </div>
              <input
                type="range"
                min="-30"
                max="50"
                step="1"
                value={baselineAdjustment}
                onChange={(e) => setBaselineAdjustment(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
            </div>

            {/* Noise Slider */}
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="font-medium text-slate-300">Volatility Noise Level (σ)</span>
                <span className="font-mono font-bold text-slate-300">±{noiseLevel}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="1"
                value={noiseLevel}
                onChange={(e) => setNoiseLevel(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
              />
            </div>

            <div className="pt-2">
              <button
                onClick={() => runSimulation()}
                disabled={isLoading}
                className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-indigo-600 hover:bg-indigo-500 text-white transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-white" />
                {isLoading ? 'Recalculating Model...' : 'Trigger Simulation Recalculation'}
              </button>
            </div>
          </div>
        </div>

        {/* Output & Chart Column */}
        <div className="lg:col-span-8 space-y-6">
          {/* Key Metric Chips */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 block mb-1">Simulated Price</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-xl font-bold text-white font-mono">
                  {simulationResult?.simulated_price ? `${simulationResult.simulated_price.toFixed(2)}` : '--'}
                </span>
                <span className="text-[11px] text-slate-400">BDT/{currentCommodity.default_unit}</span>
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                Baseline: {simulationResult?.baseline_price ? `${simulationResult.baseline_price.toFixed(2)}` : '--'} BDT
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 block mb-1">14-Day Baseline SMA</span>
              <div className="flex items-baseline gap-1.5">
                <span className="text-xl font-bold text-cyan-400 font-mono">
                  {simulationResult?.metrics?.baseline_sma_14d ? `${simulationResult.metrics.baseline_sma_14d.toFixed(2)}` : '--'}
                </span>
                <span className="text-[11px] text-slate-400">BDT</span>
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                Dev: {simulationResult?.metrics?.percentage_change_14d ? `${simulationResult.metrics.percentage_change_14d > 0 ? '+' : ''}${simulationResult.metrics.percentage_change_14d.toFixed(1)}%` : '--'}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 block mb-1">Standard Score (Z)</span>
              <div className="flex items-baseline gap-1.5">
                <span className={`text-xl font-bold font-mono ${
                  Math.abs(simulationResult?.metrics?.z_score_14d || 0) >= 2.0
                    ? 'text-rose-400'
                    : Math.abs(simulationResult?.metrics?.z_score_14d || 0) >= 1.5
                    ? 'text-amber-400'
                    : 'text-emerald-400'
                }`}>
                  {simulationResult?.metrics?.z_score_14d !== undefined ? `${simulationResult.metrics.z_score_14d > 0 ? '+' : ''}${simulationResult.metrics.z_score_14d.toFixed(2)}` : '--'}
                </span>
                <span className="text-[10px] text-slate-500">σ units</span>
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                Threshold: |Z| ≥ 1.50
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800">
              <span className="text-[11px] font-medium text-slate-400 block mb-1">Anomaly State</span>
              <div className="mt-1">
                {simulationResult ? (
                  getSeverityBadge(simulationResult.anomaly_severity, simulationResult.anomaly_direction)
                ) : (
                  <span className="text-xs text-slate-500">Calculating...</span>
                )}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                CV%: {simulationResult?.metrics?.volatility_cv !== undefined ? `${simulationResult.metrics.volatility_cv.toFixed(1)}%` : '--'}
              </div>
            </div>
          </div>

          {/* Time Series Recharts Graph */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  Real-Time Trajectory: Baseline vs Injected Shock Series
                </h4>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Visual comparison showing ground-truth history, simulated shock window, and 14-day rolling SMA.
                </p>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '0.75rem',
                      fontSize: '11px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                  <Line
                    type="monotone"
                    dataKey="Observed Baseline"
                    stroke="#64748b"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="4 4"
                  />
                  <Line
                    type="monotone"
                    dataKey="14d Rolling SMA"
                    stroke="#38bdf8"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="Simulated Series"
                    stroke={shockPercentage > 0 ? '#f43f5e' : shockPercentage < 0 ? '#10b981' : '#818cf8'}
                    strokeWidth={2.5}
                    dot={{ r: 2 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Natural Language Explanation Box */}
          <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                Explainable Natural Language Output (Generated On-The-Fly)
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                Model: Rule-Engine v2.4 (Defensible CSE Standard)
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs text-slate-200 leading-relaxed font-sans">
              {simulationResult?.explanation || 'Awaiting simulation calculation...'}
            </div>

            {/* Economic Impact Assessment */}
            {simulationResult?.impact_assessment && (
              <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs text-indigo-200 leading-relaxed">
                <div className="font-bold text-indigo-300 text-[11px] uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  Policy Impact & Market Equilibrium Assessment:
                </div>
                {simulationResult.impact_assessment}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
