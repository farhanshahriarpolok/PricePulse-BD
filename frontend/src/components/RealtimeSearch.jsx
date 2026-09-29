import React, { useState, useEffect, useRef } from 'react';
import { Search, Loader2, Sparkles, AlertCircle, ArrowRight, Mic, MicOff } from 'lucide-react';
import { searchRealtime } from '../api/endpoints';

export default function RealtimeSearch({ onSelectCommodity, lang = 'bn' }) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);

  // Quick preset search tags
  const presets = [
    { label: 'Onion (দেশি পেঁয়াজ)', query: 'onion' },
    { label: 'Potato (ডায়মন্ড আলু)', query: 'potato' },
    { label: 'Miniket Rice (মিনিকেট চাল)', query: 'miniket' },
    { label: 'Soybean Oil (সয়াবিন তেল)', query: 'soybean' },
    { label: 'Eggs (ডিম)', query: 'egg' },
  ];

  // Initialize Speech Recognition for native Bangla Voice Search
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'bn-BD';

        recognition.onstart = () => {
          setIsListening(true);
        };
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          if (transcript) {
            setQuery(transcript);
          }
          setIsListening(false);
        };
        recognition.onerror = () => {
          setIsListening(false);
        };
        recognition.onend = () => {
          setIsListening(false);
        };
        recognitionRef.current = recognition;
      }
    }
  }, []);

  const toggleVoiceSearch = () => {
    if (!recognitionRef.current) {
      alert(lang === 'bn' ? 'আপনার ব্রাউজারে ভয়েস সার্চ সমর্থিত নয়।' : 'Voice search is not supported in this browser.');
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
      } catch (err) {
        console.warn('Voice recognition start error:', err);
      }
    }
  };

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 400);
    return () => clearTimeout(handler);
  }, [query]);

  useEffect(() => {
    if (!debouncedQuery) {
      setResult(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    searchRealtime(debouncedQuery)
      .then((data) => {
        if (isMounted) setResult(data);
      })
      .catch((err) => {
        if (isMounted) {
          setResult(null);
          setError(err.message || 'No matching commodity found in taxonomy');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [debouncedQuery]);

  return (
    <div className="bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-4 sm:p-5 mb-6 shadow-sm dark:shadow-xl backdrop-blur-md transition-colors duration-150">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3.5">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-outfit flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>{lang === 'bn' ? 'রিয়েলটাইম পণ্য অনুসন্ধান ও দাম যাচাই' : 'Realtime Commodity Discovery'}</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {lang === 'bn'
              ? 'বাংলা বা ইংরেজিতে সার্চ করুন (যেমন: "পেঁয়াজ", "আলু", "Miniket Rice") অথবা মাইক চাপুন।'
              : 'Search in English or Bengali, or tap the mic for native voice search.'}
          </p>
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap gap-1.5">
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuery(p.query)}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600/50 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input Box with Bangla Voice Search */}
      <div className="relative flex items-center">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={lang === 'bn' ? 'পণ্য সার্চ করুন (যেমন: আলু, দেশি পেঁয়াজ, মিনিকেট চাল)...' : 'Search staple commodity (e.g. potato, onion, rice)...'}
          className="w-full bg-slate-50 dark:bg-slate-900/90 text-slate-900 dark:text-white placeholder-slate-400 pl-11 pr-24 py-3 rounded-xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm font-medium transition shadow-inner"
        />
        <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
        
        {/* Right action icons: Voice mic button + Loader */}
        <div className="absolute right-3 top-2 flex items-center space-x-1.5">
          {loading && <Loader2 className="w-5 h-5 text-emerald-500 animate-spin mr-1" />}
          
          <button
            type="button"
            onClick={toggleVoiceSearch}
            title={lang === 'bn' ? 'বাংলা ভয়েস সার্চ (বলুন)' : 'Bangla Voice Search'}
            className={`p-1.5 rounded-lg transition-all ${
              isListening
                ? 'bg-rose-500 text-white animate-pulse'
                : 'text-slate-500 dark:text-slate-400 hover:text-emerald-600 hover:bg-slate-200 dark:hover:bg-slate-800'
            }`}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Voice listening status banner */}
      {isListening && (
        <div className="mt-2 text-xs text-rose-600 dark:text-rose-400 font-medium flex items-center gap-1.5 animate-fadeIn">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
          <span>{lang === 'bn' ? 'শুনছি... পণ্যের নাম বলুন (যেমন: পেঁয়াজ, আলু)' : 'Listening... Speak commodity name'}</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mt-3 p-3 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Result Card */}
      {result && (
        <div className="mt-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-900/80 border border-emerald-500/40 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-base font-bold text-slate-900 dark:text-white">{result.canonical_name}</span>
              <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">({result.bangla_name})</span>
              <span className="text-[11px] px-2 py-0.5 rounded-md bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                {result.category}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wide ${
                result.freshness?.status === 'realtime_ingested' 
                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/20 dark:text-amber-300 border border-amber-300 dark:border-amber-500/30' 
                  : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-500/30'
              }`}>
                {result.freshness?.status === 'realtime_ingested' ? 'Live Ingested' : 'Cached Fresh'}
              </span>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-600 dark:text-slate-300">
              <div>
                <span className="text-slate-500">Benchmark Avg: </span>
                <span className="font-extrabold text-slate-900 dark:text-white font-mono text-sm">
                  BDT {result.price_summary?.avg_price?.toFixed(2) || '--'}
                </span>
                <span className="text-slate-500">/{result.unit || 'কেজি'}</span>
              </div>
              <div>
                <span className="text-slate-500">Market Range: </span>
                <span className="text-slate-700 dark:text-slate-200 font-mono">
                  BDT {result.price_summary?.min_price} – {result.price_summary?.max_price}
                </span>
              </div>
              {result.channels?.markup_percentage && (
                <div>
                  <span className="text-slate-500">Retail Markup: </span>
                  <span className="font-bold text-amber-600 dark:text-amber-400">+{result.channels.markup_percentage}%</span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => onSelectCommodity && onSelectCommodity(result)}
            className="w-full md:w-auto px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-colors shadow-md shadow-emerald-950/20"
          >
            <span>{lang === 'bn' ? 'বিস্তারিত ও হিস্ট্রি দেখুন' : 'Explore Trends & Spreads'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
