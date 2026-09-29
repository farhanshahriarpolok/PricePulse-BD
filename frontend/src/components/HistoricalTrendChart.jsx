import React, { useState, useMemo } from 'react';
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
import { toBengaliNumeral } from './CommodityCard';

export default function HistoricalTrendChart({
  historyData = [],
  commodityName,
  banglaName,
  unit = 'kg',
  lang = 'bn',
}) {
  const [dayRange, setDayRange] = useState(30);

  const toFixedSafe = (val, d = 1) => (val != null && !isNaN(val)) ? Number(val).toFixed(d) : '0';

  // Process and slice history data by active range filter
  const activeSlice = useMemo(() => {
    if (!historyData || historyData.length === 0) return [];
    return historyData.slice(-dayRange);
  }, [historyData, dayRange]);

  const chartData = useMemo(() => {
    return activeSlice.map((item) => ({
      date: item.date,
      price: item.avg_price != null ? Number(item.avg_price) : null,
      min: item.min_price != null ? Number(item.min_price) : null,
      max: item.max_price != null ? Number(item.max_price) : null,
    }));
  }, [activeSlice]);

  // Dynamic plain Bangla summary calculation
  const summaryText = useMemo(() => {
    const validPrices = activeSlice
      .map((x) => x.avg_price)
      .filter((p) => p != null && !isNaN(p) && p > 0);

    if (validPrices.length < 2) {
      return lang === 'bn' 
        ? 'সাম্প্রতিক বাজার পর্যবেক্ষণে দাম স্বাভাবিক সীমায় রয়েছে।'
        : 'Prices remain steady within historical baseline.';
    }

    const maxP = Math.round(Math.max(...validPrices));
    const minP = Math.round(Math.min(...validPrices));
    const firstP = validPrices[0];
    const lastP = validPrices[validPrices.length - 1];
    const diff = Math.round(Math.abs(lastP - firstP));

    if (lang === 'bn') {
      const rangeWord = dayRange === 7 ? 'গত ৭ দিনে' : dayRange === 15 ? 'গত ১৫ দিনে' : 'গত ১ মাসে';
      if (lastP < firstP) {
        return `${rangeWord} দাম সর্বোচ্চ ৳${toBengaliNumeral(maxP, lang)} এবং সর্বনিম্ন ৳${toBengaliNumeral(minP, lang)} পর্যন্ত নেমেছিল (গড়ে ${toBengaliNumeral(diff, lang)} টাকা কমেছে)`;
      } else if (lastP > firstP) {
        return `${rangeWord} দাম সর্বোচ্চ ৳${toBengaliNumeral(maxP, lang)} এবং সর্বনিম্ন ৳${toBengaliNumeral(minP, lang)} পর্যন্ত উঠেছিল (গড়ে ${toBengaliNumeral(diff, lang)} টাকা বেড়েছে)`;
      }
      return `${rangeWord} দাম সর্বোচ্চ ৳${toBengaliNumeral(maxP, lang)} ও সর্বনিম্ন ৳${toBengaliNumeral(minP, lang)} এর মধ্যে স্থিতিশীল রয়েছে`;
    } else {
      const rangeWord = dayRange === 7 ? 'In the last 7 days' : dayRange === 15 ? 'In the last 15 days' : 'In the past month';
      const changeWord = lastP < firstP ? `dropped by BDT ${diff}` : lastP > firstP ? `rose by BDT ${diff}` : 'remained steady';
      return `${rangeWord}, prices peaked at BDT ${maxP} and troughed at BDT ${minP} (${changeWord} on average)`;
    }
  }, [activeSlice, dayRange, lang]);

  if (!historyData || historyData.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 text-center text-slate-500 dark:text-slate-400 text-sm">
        {lang === 'bn' ? 'এই পণ্যের কোনো ঐতিহাসিক মূল্য তালিকা পাওয়া যায়নি।' : 'No historical price data available.'}
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const pData = payload[0].payload;
      return (
        <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl text-xs text-slate-800 dark:text-slate-200">
          <p className="font-bold text-slate-900 dark:text-white mb-1.5 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>{label}</span>
          </p>
          <div className="space-y-1">
            <p className="flex justify-between gap-4 font-mono">
              <span className="text-emerald-600 dark:text-emerald-400 font-sans">{lang === 'bn' ? 'দৈনিক গড় দর:' : 'Daily Average:'}</span>
              <span className="font-bold text-slate-900 dark:text-white">৳ {toBengaliNumeral(toFixedSafe(pData.price, 1), lang)}/{unit}</span>
            </p>
            {pData.min != null && pData.max != null && (
              <p className="flex justify-between gap-4 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                <span className="font-sans">{lang === 'bn' ? 'দামের পরিধি:' : 'Range:'}</span>
                <span>৳ {toBengaliNumeral(pData.min, lang)} – {toBengaliNumeral(pData.max, lang)}</span>
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-outfit flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>
              {lang === 'bn' 
                ? `📈 গত ${toBengaliNumeral(dayRange, lang)} দিনের দামের ওঠানামা` 
                : `📈 ${dayRange}-Day Price Movement`}
            </span>
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium">
            "{summaryText}"
          </p>
        </div>

        {/* Range Selector Chips: [৭ দিন] | [১৫ দিন] | [৩০ দিন] */}
        <div className="flex items-center space-x-1.5 p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 w-fit">
          {[
            { days: 7, labelBn: '৭ দিন', labelEn: '7 Days' },
            { days: 15, labelBn: '১৫ দিন', labelEn: '15 Days' },
            { days: 30, labelBn: '৩০ দিন', labelEn: '30 Days' },
          ].map((chip) => {
            const isSelected = dayRange === chip.days;
            return (
              <button
                key={chip.days}
                type="button"
                onClick={() => setDayRange(chip.days)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  isSelected
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {lang === 'bn' ? chip.labelBn : chip.labelEn}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-64 sm:h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.2} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={11}
              tickFormatter={(str) => (str ? str.slice(5) : '')}
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
              name={lang === 'bn' ? 'দৈনিক গড় দর' : 'Daily Average Price'}
              stroke="#059669"
              strokeWidth={3}
              dot={{ r: 3, fill: '#059669' }}
              activeDot={{ r: 6, fill: '#10b981' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
