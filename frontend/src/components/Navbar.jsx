import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Mic, 
  MicOff, 
  X, 
  Sun, 
  Moon, 
  Globe, 
  ShoppingBasket, 
  Loader2, 
  TrendingUp, 
  ArrowRight,
  MapPinned
} from 'lucide-react';
import { searchRealtime } from '../api/endpoints';
import { getTranslation } from '../i18n/translations';

export const DISTRICT_HUBS = [
  { id: 'dhaka_karwan', nameBn: 'ঢাকা - কারওয়ান বাজার', nameEn: 'Dhaka - Karwan Bazar' },
  { id: 'chittagong_khatunganj', nameBn: 'চট্টগ্রাম - খাতুনগঞ্জ', nameEn: 'Chattogram - Khatunganj' },
  { id: 'sylhet_sobhani', nameBn: 'সিলেট - সোবহানীঘাট', nameEn: 'Sylhet - Sobhanighat' },
  { id: 'rajshahi_shaheb', nameBn: 'রাজশাহী - সাহেব বাজার', nameEn: 'Rajshahi - Shaheb Bazar' },
  { id: 'khulna_boro', nameBn: 'খুলনা - বড় বাজার', nameEn: 'Khulna - Boro Bazar' },
  { id: 'barishal_notullabad', nameBn: 'বরিশাল - নতুল্লাবাদ', nameEn: 'Barishal - Notullabad' },
  { id: 'rangpur_city', nameBn: 'রংপুর - সিটি বাজার', nameEn: 'Rangpur - City Bazar' },
  { id: 'mymensingh_mechua', nameBn: 'ময়মনসিংহ - মেছুয়া বাজার', nameEn: 'Mymensingh - Mechua Bazar' },
  { id: 'bogura_fateh', nameBn: 'বগুড়া - ফতেহ আলী বাজার', nameEn: 'Bogura - Fateh Ali Bazar' },
  { id: 'jashore_boro', nameBn: 'যশোর - বড় বাজার', nameEn: 'Jashore - Boro Bazar' },
  { id: 'cumilla_chawk', nameBn: 'কুমিল্লা - চকবাজার', nameEn: 'Cumilla - Chawkbazar' },
];

export default function Navbar({
  activeTab,
  setActiveTab,
  basketCount = 0,
  theme = 'light',
  onToggleTheme,
  lang = 'bn',
  onToggleLang,
  onSelectCommodity,
  commodities = [],
  selectedDistrict = 'dhaka_karwan',
  onSelectDistrict,
}) {
  const t = (k) => getTranslation(k, lang);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const searchContainerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Close search dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Native Bangla Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'bn-BD';

        recognition.onstart = () => setIsListening(true);
        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          if (transcript) {
            setSearchQuery(transcript);
            setIsDropdownOpen(true);
          }
          setIsListening(false);
        };
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
        recognitionRef.current = recognition;
      }
    }
  }, []);

  const toggleVoiceSearch = (e) => {
    e.stopPropagation();
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
        console.warn('Voice start error:', err);
      }
    }
  };

  // Debounced Search Handler
  useEffect(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(() => {
      // 1. First search in-memory commodities
      const matches = commodities.filter((c) => {
        const cName = (c.canonical_name || '').toLowerCase();
        const bName = (c.bangla_name || '').toLowerCase();
        return cName.includes(q) || bName.includes(q);
      }).slice(0, 6);

      setSearchResults(matches);
      setIsSearching(false);
      setIsDropdownOpen(true);

      // 2. Also try realtime backend search
      searchRealtime(q)
        .then((data) => {
          if (data && !matches.some(m => m.canonical_name === data.canonical_name)) {
            setSearchResults(prev => [data, ...prev].slice(0, 6));
          }
        })
        .catch(() => {});
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery, commodities]);

  const handleSelectResult = (item) => {
    setIsDropdownOpen(false);
    setSearchQuery('');
    if (onSelectCommodity) {
      onSelectCommodity(item);
    }
  };

  return (
    <header className="sticky top-2 sm:top-3 z-50 px-2 sm:px-4 lg:px-8 max-w-7xl mx-auto w-full transition-all duration-150">
      <div className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-slate-200/90 dark:border-slate-800/90 shadow-lg dark:shadow-2xl rounded-2xl px-3 sm:px-4 py-2 flex items-center justify-between gap-2 sm:gap-4 transition-colors">
        
        {/* 1. LEFT: Brand Vector Logo + Name ("PricePulse BD") + Live Pulse Dot */}
        <div 
          onClick={() => setActiveTab('pulse')}
          className="flex items-center gap-2 cursor-pointer select-none group shrink-0"
        >
          <div className="relative">
            <img 
              src="/logo.svg" 
              alt="PricePulse BD Logo" 
              className="w-8 h-8 sm:w-9 sm:h-9 object-contain drop-shadow-sm transition-transform group-hover:scale-105" 
            />
            {/* Live Green Pulsing Dot */}
            <span className="absolute -bottom-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-base sm:text-lg font-extrabold tracking-tight text-slate-900 dark:text-white font-outfit leading-tight">
                PricePulse
              </span>
              <span className="px-1.5 py-0.2 text-[9px] sm:text-[10px] font-black uppercase tracking-wider bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 rounded">
                BD
              </span>
            </div>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium hidden md:block leading-none">
              {lang === 'bn' ? 'বাজার মনিটরিং' : 'Market Intelligence'}
            </span>
          </div>
        </div>

        {/* 2. CENTER: Prominent Wide Search Bar with Bangla Voice Search (Desktop & Tablet) */}
        <div ref={searchContainerRef} className="hidden sm:block flex-1 min-w-0 max-w-xl relative">
          <div className="relative flex items-center min-w-0">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => {
                if (searchQuery.trim().length > 0) setIsDropdownOpen(true);
              }}
              placeholder={lang === 'bn' ? 'পণ্য সার্চ করুন...' : 'Search commodities...'}
              className="w-full min-w-0 bg-slate-100/90 dark:bg-slate-800/90 hover:bg-slate-100 dark:hover:bg-slate-800 focus:bg-white dark:focus:bg-slate-900 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 pl-8 sm:pl-10 pr-14 sm:pr-20 py-1.5 sm:py-2.5 rounded-xl border border-slate-200/80 dark:border-slate-700/80 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 text-xs sm:text-sm font-medium transition shadow-inner"
            />
            <Search className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-400 absolute left-2.5 sm:left-3 top-1/2 -translate-y-1/2 pointer-events-none" />

            {/* Clear Button & Voice Search Button */}
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {isSearching && (
                <Loader2 className="w-3.5 h-3.5 text-emerald-500 animate-spin mr-0.5" />
              )}

              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                  aria-label="Clear search"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}

              <button
                type="button"
                onClick={toggleVoiceSearch}
                title={lang === 'bn' ? 'বাংলায় ভয়েস সার্চ করুন' : 'Bangla Voice Search'}
                className={`p-1.5 rounded-lg transition-all ${
                  isListening
                    ? 'bg-rose-500 text-white animate-pulse'
                    : 'text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-slate-200/60 dark:hover:bg-slate-700/60'
                }`}
                aria-label="Voice search"
              >
                {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Quick Realtime Search Results Popover */}
          {isDropdownOpen && searchResults.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 animate-fadeIn">
              <div className="p-2 border-b border-slate-100 dark:border-slate-800 text-[11px] font-semibold text-slate-500 dark:text-slate-400 flex items-center justify-between">
                <span>{lang === 'bn' ? 'অনুসন্ধানের ফলাফল' : 'Search Results'}</span>
                <span>{searchResults.length} টি পণ্য</span>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60">
                {searchResults.map((item, idx) => (
                  <div
                    key={item.id || item.commodity_id || idx}
                    onClick={() => handleSelectResult(item)}
                    className="p-2.5 sm:p-3 hover:bg-emerald-50/60 dark:hover:bg-emerald-950/30 cursor-pointer flex items-center justify-between transition-colors group"
                  >
                    <div>
                      <h5 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                        {lang === 'bn' ? (item.bangla_name || item.canonical_name) : item.canonical_name}
                      </h5>
                      <p className="text-[10px] text-slate-500 dark:text-slate-400">
                        {lang === 'bn' ? item.canonical_name : (item.bangla_name || '')}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">
                        ৳{item.price_summary?.avg_price || item.avg_price || item.benchmark_price || '--'}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-emerald-500 group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 3. RIGHT: Sleek Theme Toggle [☀️/🌙], Language Switcher [বাং|EN], Active Basket Button */}
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          
          {/* District Selector Pill (Desktop / Tablet) */}
          <div className="relative hidden lg:flex items-center">
            <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-medium text-slate-800 dark:text-slate-200">
              <MapPinned className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <select
                value={selectedDistrict}
                onChange={(e) => onSelectDistrict && onSelectDistrict(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer pr-1"
              >
                {DISTRICT_HUBS.map((dist) => (
                  <option key={dist.id} value={dist.id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                    {lang === 'bn' ? dist.nameBn : dist.nameEn}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Theme Toggle Button [☀️ / 🌙] */}
          <button
            id="theme-toggle-btn"
            onClick={onToggleTheme}
            aria-label="Toggle color theme"
            className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700/80 transition-all shadow-xs active:scale-95"
            title={theme === 'dark' ? 'লাইট মোডে পরিবর্তন করুন' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-slate-700" />
            )}
          </button>

          {/* Language Switcher [বাং | EN] */}
          <button
            id="lang-toggle-btn"
            onClick={onToggleLang}
            aria-label="Toggle language"
            className="flex items-center gap-1 px-2 sm:px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-emerald-700 dark:text-emerald-400 text-xs font-bold border border-slate-200/80 dark:border-slate-700/80 transition-all shadow-xs active:scale-95"
            title={lang === 'bn' ? 'Switch to English' : 'বাংলায় দেখুন'}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{lang === 'bn' ? 'EN' : 'বাং'}</span>
          </button>

          {/* Active Basket Cart Trigger Button with Live Counter Badge */}
          <button
            id="basket-trigger-btn"
            onClick={() => setActiveTab('basket')}
            aria-label="Open shopping basket"
            className={`relative flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm active:scale-95 border ${
              activeTab === 'basket'
                ? 'bg-amber-600 text-white border-amber-600 shadow-amber-950/20'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-600 shadow-emerald-950/20'
            }`}
            title={lang === 'bn' ? 'বাজারের ফর্দ দেখুন' : 'View Shopping Basket'}
          >
            <ShoppingBasket className="w-4 h-4" />
            <span className="hidden sm:inline">
              {lang === 'bn' ? 'ফর্দ' : 'Basket'}
            </span>
            {basketCount > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] font-mono font-black rounded-full bg-white text-emerald-800 shadow-xs animate-pulse">
                {basketCount}
              </span>
            )}
          </button>
        </div>

      </div>
    </header>
  );
}
