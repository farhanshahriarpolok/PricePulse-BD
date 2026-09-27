import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { Calendar, TrendingUp } from 'lucide-react';

export default function HistoricalTrendChart({ historyData, commodityName, unit = 'kg' }) {
  if (!historyData || historyData.length === 0) {
    return (
      <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-6 text-center text-slate-400 text-sm">
        No historical time-series observations available for this commodity.
      </div>
    );
  }

  // Calculate 14-day rolling SMA on the client for smooth charting
  const formattedData = historyData.map((item, index, arr) => {
    // 14-day slice
    const sliceStart = Math.max(0, index - 13);
    const windowSlice = arr.slice(sliceStart, index + 1);
    const windowAvg = windowSlice.reduce((sum, curr) => sum + curr.avg_price, 0) / windowSlice.length;

    return {
      date: item.date,
      price: item.avg_price,
      sma14: Number(windowAvg.toFixed(2)),
      min: item.min_price,
      max: item.max_price,
      samples: item.sample_count,
    };
  });

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const pData = payload[0].payload;
      return (
        <div className="p-3 bg-slate-900 border border-slate-700 rounded-lg shadow-xl text-xs text-slate-200">
          <p className="font-semibold text-white mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-emerald-400" />
            {label}
          </p>
          <div className="space-y-1">
            <p className="flex justify-between gap-4">
              <span className="text-emerald-400">Daily Average:</span>
              <span className="font-bold text-white">BDT {pData.price.toFixed(2)}/{unit}</span>
            </p>
            <p className="flex justify-between gap-4">
              <span className="text-amber-400">14-Day SMA:</span>
              <span className="font-bold text-white">BDT {pData.sma14.toFixed(2)}/{unit}</span>
            </p>
            <p className="flex justify-between gap-4 text-slate-400">
              <span>Spread Range:</span>
              <span>{pData.min} – {pData.max} BDT</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800/60 border border-slate-700/80 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-base font-bold text-white font-outfit flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            30-Day Historical Trend & Moving Average Baseline
          </h3>
          <p className="text-xs text-slate-400">
            Evaluating price action for <strong className="text-slate-200">{commodityName}</strong> against 14-day statistical equilibrium.
          </p>
        </div>
        <div className="text-xs font-mono px-2.5 py-1 rounded bg-slate-900 text-slate-300 border border-slate-700">
          N = {historyData.length} Days
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickFormatter={(str) => str.slice(5)} // MM-DD
              tickLine={false}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              domain={['auto', 'auto']}
              tickLine={false}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="price"
              name="Daily Average Price"
              stroke="#10b981"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#10b981' }}
              activeDot={{ r: 6, fill: '#34d399' }}
            />
            <Line
              type="monotone"
              dataKey="sma14"
              name="14-Day SMA Baseline"
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
