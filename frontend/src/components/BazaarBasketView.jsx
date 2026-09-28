import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ShoppingBasket,
  Plus,
  Minus,
  Trash2,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Store,
  Smartphone,
  ShoppingCart,
  ChevronRight,
  AlertCircle,
  Lightbulb,
  Printer,
  Share2,
  RotateCcw,
  CheckCircle,
  Search,
  X,
  Bookmark,
  BookmarkCheck,
  History,
  LineChart,
  Calendar,
  Save,
  Clock,
  ArrowRight,
  BarChart2,
} from 'lucide-react';
import {
  getCommodities,
  calculateBasket,
  getBasketPresets,
  saveBasket,
  getSavedBaskets,
  getSavedBasketDetail,
  deleteSavedBasket,
  getSavedBasketTrend,
} from '../api/endpoints';

// ─── Unit options available for selection ────────────────────────────────────
const UNITS = [
  { value: 'kg', label: 'কেজি (kg)' },
  { value: 'liter', label: 'লিটার' },
  { value: 'হালি', label: 'হালি (4 পিস)' },
  { value: 'পিস', label: 'পিস' },
  { value: 'পোয়া', label: 'পোয়া (250g)' },
  { value: 'g', label: 'গ্রাম' },
  { value: 'ml', label: 'মিলিলিটার' },
];

// ─── Preset button definitions ────────────────────────────────────────────────
const PRESET_BUTTONS = [
  { id: 'weekly_essentials', icon: '🛒', label: 'সাপ্তাহিক বাজার' },
  { id: 'bachelor_fast_basket', icon: '👨‍🎓', label: 'ব্যাচেলর বাস্কেট' },
  { id: 'family_weekend_feast', icon: '🍖', label: 'উইকেন্ড ফিস্ট' },
];

// ─── Channel config ────────────────────────────────────────────────────────────
const CHANNEL_CONFIG = {
  wholesale: {
    icon: Store,
    color: 'emerald',
    label: '🏪 পাইকারি বাজার',
    sublabel: 'কারওয়ান বাজার / আড়ত',
  },
  retail: {
    icon: ShoppingCart,
    color: 'sky',
    label: '🛒 খুচরা বাজার',
    sublabel: 'স্থানীয় কাঁচাবাজার',
  },
  online: {
    icon: Smartphone,
    color: 'amber',
    label: '📱 অনলাইন / সুপারশপ',
    sublabel: 'চালডাল / শপআপ',
  },
};

// ─── Bengla number formatter ──────────────────────────────────────────────────
const BDT = (amount) =>
  `৳${Number(amount).toLocaleString('en-BD', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;

export default function BazaarBasketView({ onBasketCountChange }) {
  const [activeSubTab, setActiveSubTab] = useState(() => {
    if (typeof window !== 'undefined' && window.location.hash.includes('saved')) {
      return 'saved';
    }
    return 'calculator';
  });
  const [commodities, setCommodities] = useState([]);
  const [presets, setPresets] = useState([]);
  const [basket, setBasket] = useState([]); // {commodity_id, commodity_name, bangla_name, quantity, unit}
  const [result, setResult] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState(null);
  const [presetsLoaded, setPresetsLoaded] = useState(false);

  // Saved Baskets state
  const [savedBaskets, setSavedBaskets] = useState([]);
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveBanglaName, setSaveBanglaName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);

  // Trend modal state
  const [trendModal, setTrendModal] = useState(null);

  // Item adder state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommodity, setSelectedCommodity] = useState(null);
  const [adderQty, setAdderQty] = useState(1);
  const [adderUnit, setAdderUnit] = useState('kg');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // ── Load commodities, presets and saved baskets on mount ───────────────────
  const fetchSavedBaskets = useCallback(() => {
    setIsLoadingSaved(true);
    getSavedBaskets()
      .then((res) => {
        setSavedBaskets(res || []);
        setIsLoadingSaved(false);
      })
      .catch(() => {
        setSavedBaskets([]);
        setIsLoadingSaved(false);
      });
  }, []);

  useEffect(() => {
    getCommodities()
      .then((res) => setCommodities(res?.items || []))
      .catch(() => setCommodities([]));

    getBasketPresets()
      .then((res) => {
        setPresets(res?.presets || []);
        setPresetsLoaded(true);
      })
      .catch(() => setPresetsLoaded(true));

    fetchSavedBaskets();
  }, [fetchSavedBaskets]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Emit basket count to parent (for Navbar badge)
  useEffect(() => {
    if (onBasketCountChange) {
      onBasketCountChange(basket.filter((i) => i.matched).length);
    }
  }, [basket, onBasketCountChange]);

  // ── Commodity search filtering ────────────────────────────────────────────
  const filteredCommodities = searchQuery.trim().length >= 1
    ? commodities.filter(
        (c) =>
          c.canonical_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (c.bangla_name && c.bangla_name.includes(searchQuery))
      ).slice(0, 8)
    : [];

  // ── Preset loader ─────────────────────────────────────────────────────────
  const loadPreset = useCallback(
    (presetId) => {
      const preset = presets.find((p) => p.id === presetId);
      if (!preset) return;

      const newItems = preset.items.map((item, idx) => {
        const matched = commodities.find(
          (c) =>
            c.canonical_name === item.commodity_name ||
            (c.bangla_name && c.bangla_name === item.bangla_name)
        );
        return {
          id: `preset-${presetId}-${idx}`,
          commodity_id: matched?.id || null,
          commodity_name: item.commodity_name,
          bangla_name: item.bangla_name || item.commodity_name,
          quantity: item.quantity,
          unit: item.unit,
          matched: !!matched,
        };
      });

      setBasket(newItems);
      setResult(null);
      setError(null);
    },
    [presets, commodities]
  );

  // ── Add item to basket ────────────────────────────────────────────────────
  const addItem = () => {
    if (!selectedCommodity) return;
    const newItem = {
      id: `item-${Date.now()}`,
      commodity_id: selectedCommodity.id,
      commodity_name: selectedCommodity.canonical_name,
      bangla_name: selectedCommodity.bangla_name || selectedCommodity.canonical_name,
      quantity: adderQty,
      unit: adderUnit,
      matched: true,
    };
    setBasket((prev) => [...prev, newItem]);
    setSelectedCommodity(null);
    setSearchQuery('');
    setAdderQty(1);
    setAdderUnit('kg');
    setResult(null);
  };

  // ── Remove item ───────────────────────────────────────────────────────────
  const removeItem = (id) => {
    setBasket((prev) => prev.filter((item) => item.id !== id));
    setResult(null);
  };

  // ── Update quantity ───────────────────────────────────────────────────────
  const updateQty = (id, delta) => {
    setBasket((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, quantity: Math.max(0.25, parseFloat((item.quantity + delta).toFixed(2))) }
          : item
      )
    );
    setResult(null);
  };

  // ── Calculate basket ──────────────────────────────────────────────────────
  const calculate = async () => {
    const validItems = basket.filter((item) => item.commodity_id != null && item.matched);
    if (validItems.length === 0) {
      setError('বাস্কেটে কোনো বৈধ পণ্য নেই। অনুগ্রহ করে পণ্য যোগ করুন।');
      return;
    }
    setIsCalculating(true);
    setError(null);
    try {
      const payload = {
        items: validItems.map((item) => ({
          commodity_id: item.commodity_id,
          quantity: item.quantity,
          raw_unit: item.unit,
        })),
      };
      const res = await calculateBasket(payload);
      setResult(res);
    } catch (err) {
      setError('বাস্কেট হিসাব করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।');
    } finally {
      setIsCalculating(false);
    }
  };

  // ── Print handler ─────────────────────────────────────────────────────────
  const handlePrint = () => {
    window.print();
  };

  // ── Clear basket ──────────────────────────────────────────────────────────
  const clearBasket = () => {
    setBasket([]);
    setResult(null);
    setError(null);
  };

  const validBasketCount = basket.filter((i) => i.matched).length;

  // ── Saved Baskets Handlers ────────────────────────────────────────────────
  const handleSaveBasket = async (e) => {
    e.preventDefault();
    if (!saveName.trim() || basket.length === 0) return;
    setIsSaving(true);
    try {
      const payload = {
        name: saveName.trim(),
        bangla_name: saveBanglaName.trim() || null,
        description: saveDescription.trim() || null,
        items: basket
          .filter((item) => item.commodity_id)
          .map((item) => ({
            commodity_id: item.commodity_id,
            quantity: Number(item.quantity),
            unit: item.unit,
          })),
      };
      await saveBasket(payload);
      setSaveSuccessMsg('বাস্কেট সফলভাবে সংরক্ষিত হয়েছে!');
      fetchSavedBaskets();
      setTimeout(() => {
        setShowSaveModal(false);
        setSaveSuccessMsg(null);
        setSaveName('');
        setSaveBanglaName('');
        setSaveDescription('');
      }, 1200);
    } catch (err) {
      setError('বাস্কেট সংরক্ষণ করতে সমস্যা হয়েছে।');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLoadSavedBasket = async (savedBasketId) => {
    try {
      const detail = await getSavedBasketDetail(savedBasketId);
      if (detail && detail.items) {
        const loadedItems = detail.items.map((item) => ({
          id: `${item.commodity_id}-${Date.now()}-${Math.random()}`,
          commodity_id: item.commodity_id,
          commodity_name: item.canonical_name,
          bangla_name: item.bangla_name,
          quantity: item.quantity,
          unit: item.unit,
          matched: true,
        }));
        setBasket(loadedItems);
        setActiveSubTab('calculator');

        // Automatically trigger calculation
        const calcPayload = {
          items: loadedItems.map((i) => ({
            commodity_id: i.commodity_id,
            quantity: i.quantity,
            raw_unit: i.unit,
          })),
        };
        setIsCalculating(true);
        calculateBasket(calcPayload)
          .then((res) => {
            setResult(res);
            setIsCalculating(false);
          })
          .catch(() => setIsCalculating(false));
      }
    } catch (err) {
      setError('সংরক্ষিত বাস্কেট লোড করতে ব্যর্থ হয়েছে।');
    }
  };

  const handleDeleteSavedBasket = async (savedBasketId) => {
    if (!window.confirm('আপনি কি এই সংরক্ষিত বাস্কেটটি মুছে ফেলতে চান?')) return;
    try {
      await deleteSavedBasket(savedBasketId);
      setSavedBaskets((prev) => prev.filter((b) => b.id !== savedBasketId));
    } catch (err) {
      setError('বাস্কেট মুছতে সমস্যা হয়েছে।');
    }
  };

  const handleOpenTrendModal = async (savedBasketId, name, banglaName) => {
    setTrendModal({
      basketId: savedBasketId,
      basketName: name,
      banglaName: banglaName,
      trendData: null,
      loading: true,
    });
    try {
      const trend = await getSavedBasketTrend(savedBasketId, 30);
      setTrendModal((prev) => ({
        ...prev,
        trendData: trend,
        loading: false,
      }));
    } catch (err) {
      setTrendModal((prev) => ({
        ...prev,
        error: 'ট্রেন্ড ডাটা লোড করতে ব্যর্থ হয়েছে।',
        loading: false,
      }));
    }
  };

  // Auto-open trend modal if requested in URL hash (e.g., #basket-trend)
  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.hash.includes('trend') && savedBaskets.length > 0 && !trendModal) {
      handleOpenTrendModal(savedBaskets[0].id, savedBaskets[0].name, savedBaskets[0].bangla_name);
    }
  }, [savedBaskets, trendModal]);

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="bazaar-basket-root">

      {/* ── Page Header ──────────────────────────────────────────────── */}
      <div className="bb-page-header">
        <div className="flex items-center space-x-3">
          <div className="bb-header-icon">
            <ShoppingBasket className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="bb-page-title">বাজার বাস্কেট ও জীবনযাত্রার খরচ ট্র্যাকার</h1>
            <p className="bb-page-subtitle">
              কাস্টম বাজার অপটিমাইজেশন, পাইকারি বনাম খুচরা সাশ্রয় এবং ব্যক্তিগত ৩০ দিনের মুদ্রাস্ফীতি ইনডেক্স
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-2 mt-3 sm:mt-0">
          <button
            onClick={() => setActiveSubTab('calculator')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'calculator'
                ? 'bg-amber-500 text-slate-950 font-bold shadow'
                : 'bg-slate-800 text-slate-300 hover:text-white border border-slate-700'
            }`}
          >
            <ShoppingBasket className="w-3.5 h-3.5" />
            <span>বাজার ক্যালকুলেটর ({validBasketCount})</span>
          </button>

          <button
            onClick={() => {
              setActiveSubTab('saved');
              fetchSavedBaskets();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              activeSubTab === 'saved'
                ? 'bg-amber-500 text-slate-950 font-bold shadow'
                : 'bg-slate-800 text-slate-300 hover:text-white border border-slate-700'
            }`}
          >
            <BookmarkCheck className="w-3.5 h-3.5" />
            <span>সংরক্ষিত বাস্কেট ({savedBaskets.length})</span>
          </button>
        </div>
      </div>

      {/* ── Calculator SubTab ────────────────────────────────────────── */}
      {activeSubTab === 'calculator' && (
        <>
          {/* ── Preset Buttons ────────────────────────────────────────────── */}
          <div className="bb-presets-row">
        <span className="bb-presets-label">দ্রুত লোড করুন:</span>
        {PRESET_BUTTONS.map((preset) => (
          <button
            key={preset.id}
            onClick={() => loadPreset(preset.id)}
            disabled={!presetsLoaded}
            className="bb-preset-btn"
            id={`preset-btn-${preset.id}`}
          >
            <span>{preset.icon}</span>
            <span>{preset.label}</span>
          </button>
        ))}
        {basket.length > 0 && (
          <button onClick={clearBasket} className="bb-clear-btn">
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* ── Main Grid ─────────────────────────────────────────────────── */}
      <div className="bb-main-grid">

        {/* LEFT: Item Adder + Basket Table */}
        <div className="bb-left-panel">

          {/* ── Item Adder Card ────────────────────────────────────────── */}
          <div className="bb-card">
            <h3 className="bb-card-title">
              <Plus className="w-4 h-4 text-emerald-400" />
              পণ্য যোগ করুন
            </h3>

            <div className="bb-adder-row" ref={dropdownRef}>
              {/* Searchable Commodity Dropdown */}
              <div className="bb-search-wrap">
                <div className="bb-search-input-wrap">
                  <Search className="bb-search-icon" />
                  <input
                    id="basket-commodity-search"
                    type="text"
                    placeholder="পণ্যের নাম টাইপ করুন (বাংলা/English)..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setShowDropdown(true);
                      if (!e.target.value) setSelectedCommodity(null);
                    }}
                    onFocus={() => setShowDropdown(true)}
                    className="bb-search-input"
                  />
                  {selectedCommodity && (
                    <button
                      onClick={() => { setSelectedCommodity(null); setSearchQuery(''); }}
                      className="bb-search-clear"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                {showDropdown && filteredCommodities.length > 0 && (
                  <div className="bb-dropdown">
                    {filteredCommodities.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => {
                          setSelectedCommodity(c);
                          setSearchQuery(c.bangla_name || c.canonical_name);
                          setShowDropdown(false);
                          // Auto-set unit from commodity default
                          if (c.default_unit === 'liter') setAdderUnit('liter');
                          else if (c.default_unit === 'pc') setAdderUnit('পিস');
                          else setAdderUnit('kg');
                        }}
                        className="bb-dropdown-item"
                      >
                        <span className="bb-dropdown-bn">{c.bangla_name}</span>
                        <span className="bb-dropdown-en">{c.canonical_name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Quantity Stepper */}
              <div className="bb-qty-stepper">
                <button
                  onClick={() => setAdderQty((q) => Math.max(0.25, parseFloat((q - 0.5).toFixed(2))))}
                  className="bb-qty-btn"
                  id="basket-qty-decrease"
                >
                  <Minus className="w-3.5 h-3.5" />
                </button>
                <span className="bb-qty-display">{adderQty}</span>
                <button
                  onClick={() => setAdderQty((q) => parseFloat((q + 0.5).toFixed(2)))}
                  className="bb-qty-btn"
                  id="basket-qty-increase"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Unit Selector */}
              <select
                value={adderUnit}
                onChange={(e) => setAdderUnit(e.target.value)}
                className="bb-unit-select"
                id="basket-unit-select"
              >
                {UNITS.map((u) => (
                  <option key={u.value} value={u.value}>{u.label}</option>
                ))}
              </select>

              {/* Add Button */}
              <button
                onClick={addItem}
                disabled={!selectedCommodity}
                className="bb-add-btn"
                id="basket-add-item-btn"
              >
                <Plus className="w-4 h-4" />
                <span>যোগ করুন</span>
              </button>
            </div>
          </div>

          {/* ── Active Basket Table ─────────────────────────────────────── */}
          <div className="bb-card">
            <div className="bb-basket-header-row">
              <h3 className="bb-card-title">
                <ShoppingBasket className="w-4 h-4 text-emerald-400" />
                আপনার বাস্কেট
              </h3>
              {basket.length > 0 && (
                <span className="bb-basket-item-count">{basket.length} পণ্য</span>
              )}
            </div>

            {basket.length === 0 ? (
              <div className="bb-empty-basket">
                <ShoppingBasket className="w-12 h-12 text-slate-600 mb-3" />
                <p className="text-slate-400 text-sm">বাস্কেট খালি আছে।</p>
                <p className="text-slate-500 text-xs mt-1">উপরের প্রিসেট বোতাম বা পণ্য অনুসন্ধান ব্যবহার করুন।</p>
              </div>
            ) : (
              <div className="bb-basket-table-wrap">
                <table className="bb-basket-table">
                  <thead>
                    <tr className="bb-table-head">
                      <th className="bb-th text-left">পণ্য</th>
                      <th className="bb-th text-center">পরিমাণ</th>
                      <th className="bb-th text-right">একক</th>
                      {result && <th className="bb-th text-right">মূল্য</th>}
                      <th className="bb-th text-right">মুছুন</th>
                    </tr>
                  </thead>
                  <tbody>
                    {basket.map((item) => {
                      const detail = result?.item_details?.find(
                        (d) => d.commodity_id === item.commodity_id
                      );
                      return (
                        <tr key={item.id} className="bb-table-row">
                          <td className="bb-td-name">
                            <div className="bb-item-name-block">
                              <span className="bb-item-bn">{item.bangla_name}</span>
                              <span className="bb-item-en">{item.commodity_name}</span>
                            </div>
                            {!item.matched && (
                              <span className="bb-unmatched-badge">
                                <AlertCircle className="w-3 h-3" /> অমিল
                              </span>
                            )}
                          </td>
                          <td className="bb-td-qty">
                            <div className="bb-inline-stepper">
                              <button
                                onClick={() => updateQty(item.id, -0.5)}
                                className="bb-inline-btn"
                              >
                                <Minus className="w-3 h-3" />
                              </button>
                              <span className="bb-inline-qty">{item.quantity}</span>
                              <button
                                onClick={() => updateQty(item.id, 0.5)}
                                className="bb-inline-btn"
                              >
                                <Plus className="w-3 h-3" />
                              </button>
                            </div>
                          </td>
                          <td className="bb-td-unit">
                            <span className="bb-unit-pill">{item.unit}</span>
                          </td>
                          {result && (
                            <td className="bb-td-price">
                              {detail ? (
                                <div className="bb-price-col">
                                  <span className="bb-line-total">{BDT(detail.line_total)}</span>
                                  <span className="bb-unit-price text-slate-500 text-[10px]">
                                    @{BDT(detail.unit_price)}/{detail.standard_unit}
                                  </span>
                                </div>
                              ) : (
                                <span className="text-slate-500">—</span>
                              )}
                            </td>
                          )}
                          <td className="bb-td-del">
                            <button
                              onClick={() => removeItem(item.id)}
                              className="bb-del-btn"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Calculate CTA */}
            {basket.length > 0 && (
              <div className="bb-calculate-row">
                <button
                  onClick={calculate}
                  disabled={isCalculating || validBasketCount === 0}
                  className="bb-calculate-btn"
                  id="basket-calculate-btn"
                >
                  {isCalculating ? (
                    <>
                      <span className="bb-spinner" />
                      <span>হিসাব হচ্ছে...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>বাজার হিসাব করুন</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {error && (
              <div className="bb-error-banner">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Results Panel */}
        <div className="bb-right-panel">
          {!result ? (
            <div className="bb-results-placeholder">
              <ShoppingBasket className="w-16 h-16 text-slate-700 mb-4" />
              <p className="text-slate-400 font-medium">ফলাফল দেখতে</p>
              <p className="text-slate-500 text-sm">"বাজার হিসাব করুন" বোতাম চাপুন</p>
            </div>
          ) : (
            <div className="bb-results-wrap">

              {/* ── Hero Total ───────────────────────────────────────────── */}
              <div className="bb-hero-total">
                <div>
                  <p className="bb-hero-label">আজকের মোট বাজার</p>
                  <p className="bb-hero-amount">{BDT(result.benchmark_total)}</p>
                </div>
                <div className="bb-shift-tag" data-positive={result.cost_shift_7d_bdt > 0}>
                  {result.cost_shift_7d_bdt > 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : result.cost_shift_7d_bdt < 0 ? (
                    <TrendingDown className="w-4 h-4" />
                  ) : null}
                  <div>
                    <span className="block font-bold">
                      {result.cost_shift_7d_pct > 0 ? '+' : ''}{result.cost_shift_7d_pct}%
                    </span>
                    <span className="text-[10px] opacity-80">গত সপ্তাহ থেকে</span>
                  </div>
                </div>
              </div>

              {/* ── 7-Day Shift Banner ───────────────────────────────────── */}
              {result.cost_shift_7d_bdt !== 0 && (
                <div className="bb-shift-banner" data-up={result.cost_shift_7d_bdt > 0}>
                  {result.cost_shift_7d_bdt > 0 ? (
                    <TrendingUp className="w-4 h-4 flex-shrink-0" />
                  ) : (
                    <TrendingDown className="w-4 h-4 flex-shrink-0" />
                  )}
                  <span>
                    গত সপ্তাহের চেয়ে এই বাজারের খরচ{' '}
                    {result.cost_shift_7d_bdt > 0 ? '+' : ''}
                    {result.cost_shift_7d_pct}% ({BDT(Math.abs(result.cost_shift_7d_bdt))})
                    {result.cost_shift_7d_bdt > 0 ? ' বেড়েছে।' : ' কমেছে।'}
                  </span>
                </div>
              )}

              {/* ── Channel Comparison ───────────────────────────────────── */}
              <div className="bb-card">
                <h3 className="bb-card-title">
                  <Store className="w-4 h-4 text-emerald-400" />
                  চ্যানেল মূল্য তুলনা
                </h3>

                <div className="bb-channels-grid">
                  {/* Wholesale */}
                  <ChannelCard
                    label="🏪 পাইকারি বাজার"
                    sublabel="কারওয়ান বাজার"
                    total={result.wholesale_total}
                    benchmark={result.benchmark_total}
                    colorClass="emerald"
                    isBest={result.best_channel.includes('পাইকারি')}
                  />
                  {/* Retail */}
                  <ChannelCard
                    label="🛒 খুচরা বাজার"
                    sublabel="স্থানীয় কাঁচাবাজার"
                    total={result.retail_total}
                    benchmark={result.benchmark_total}
                    colorClass="sky"
                    isBaseline
                    isBest={result.best_channel.includes('খুচরা')}
                  />
                  {/* Online */}
                  <ChannelCard
                    label="📱 অনলাইন / সুপারশপ"
                    sublabel="চালডাল · শপআপ"
                    total={result.online_total}
                    benchmark={result.benchmark_total}
                    colorClass="amber"
                    isBest={result.best_channel.includes('অনলাইন')}
                  />
                </div>

                {/* Savings Explanation */}
                <div className="bb-savings-explanation">
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {result.savings_explanation}
                  </p>
                </div>
              </div>

              {/* ── Smart Saving Tips ────────────────────────────────────── */}
              {result.smart_saving_tips?.length > 0 && (
                <div className="bb-tips-card">
                  <div className="bb-tips-header">
                    <Lightbulb className="w-4 h-4 text-amber-400" />
                    <span>স্মার্ট সাশ্রয় পরামর্শ</span>
                  </div>
                  <ul className="bb-tips-list">
                    {result.smart_saving_tips.map((tip, i) => (
                      <li key={i} className="bb-tip-item">
                        <span className="bb-tip-bullet">💡</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* ── Actions Row ──────────────────────────────────────────── */}
              <div className="bb-actions-row">
                <button
                  onClick={() => {
                    setSaveName(`বাস্কেট #${savedBaskets.length + 1}`);
                    setSaveBanglaName(`বাজার বাস্কেট #${savedBaskets.length + 1}`);
                    setSaveDescription('');
                    setShowSaveModal(true);
                  }}
                  className="bb-action-btn bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40"
                  id="basket-save-modal-btn"
                >
                  <Save className="w-4 h-4" />
                  <span>বাস্কেট সংরক্ষণ</span>
                </button>
                <button onClick={handlePrint} className="bb-action-btn bb-print-btn" id="basket-print-btn">
                  <Printer className="w-4 h-4" />
                  <span>বাজার লিস্ট প্রিন্ট</span>
                </button>
                <button
                  onClick={() => {
                    const text = `PricePulse BD বাজার বাস্কেট\nমোট: ${BDT(result.benchmark_total)}\nপাইকারি: ${BDT(result.wholesale_total)}\n${result.savings_explanation}`;
                    if (navigator.share) {
                      navigator.share({ title: 'বাজার হিসাব', text });
                    } else {
                      navigator.clipboard.writeText(text);
                    }
                  }}
                  className="bb-action-btn bb-share-btn"
                  id="basket-share-btn"
                >
                  <Share2 className="w-4 h-4" />
                  <span>শেয়ার</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )}

      {/* ── Saved Baskets SubTab ────────────────────────────────────────── */}
      {activeSubTab === 'saved' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <BookmarkCheck className="w-5 h-5 text-amber-400" />
                <span>সংরক্ষিত বাজার বাস্কেট ও ৩০ দিনের CPI ট্র্যাকিং</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                আপনার নিত্যপ্রয়োজনীয় বাস্কেটের ঐতিহাসিক দামের তারতম্য এবং মুদ্রাস্ফীতি পর্যবেক্ষণ করুন
              </p>
            </div>
            <button
              onClick={() => setActiveSubTab('calculator')}
              className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center space-x-1.5 border border-emerald-500/30 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>নতুন বাস্কেট তৈরি</span>
            </button>
          </div>

          {isLoadingSaved ? (
            <div className="p-12 text-center">
              <div className="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-slate-400">সংরক্ষিত বাস্কেট লোড হচ্ছে...</p>
            </div>
          ) : savedBaskets.length === 0 ? (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-10 text-center">
              <ShoppingBasket className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h4 className="text-sm font-semibold text-slate-300 mb-1">
                কোনো সংরক্ষিত বাস্কেট পাওয়া যায়নি
              </h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
                ক্যালকুলেটরে আপনার পছন্দের পণ্য যোগ করে 'বাস্কেট সংরক্ষণ' বাটনে ক্লিক করে এখানে সেভ করুন
              </p>
              <button
                onClick={() => setActiveSubTab('calculator')}
                className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs inline-flex items-center space-x-2 transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>প্রথম বাস্কেট তৈরি করুন</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedBaskets.map((b) => (
                <div
                  key={b.id}
                  className="bg-slate-800/60 border border-slate-700/80 hover:border-slate-600 rounded-2xl p-5 flex flex-col justify-between transition-all group hover:shadow-xl hover:shadow-slate-900/50"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <h3 className="text-sm font-bold text-white group-hover:text-amber-400 transition-colors">
                          {b.bangla_name || b.name}
                        </h3>
                        {b.bangla_name && b.name !== b.bangla_name && (
                          <span className="text-[10px] text-slate-400">{b.name}</span>
                        )}
                      </div>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-700/80 text-slate-300 border border-slate-600 flex-shrink-0">
                        {b.item_count} টি পণ্য
                      </span>
                    </div>

                    {b.description && (
                      <p className="text-xs text-slate-400 mb-3 line-clamp-2">{b.description}</p>
                    )}

                    {/* Price Breakdown */}
                    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-3 space-y-1.5 my-3 text-xs">
                      <div className="flex justify-between items-center text-slate-300">
                        <span>খুচরা বাজার দর:</span>
                        <span className="font-semibold text-sky-400">
                          {BDT(b.current_retail_total ?? b.retail_total ?? 0)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-slate-300">
                        <span>পাইকারি দর:</span>
                        <span className="font-semibold text-emerald-400">
                          {BDT(b.current_wholesale_total ?? b.wholesale_total ?? 0)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center text-emerald-400 font-bold pt-1 border-t border-slate-800">
                        <span>সম্ভাব্য সাশ্রয়:</span>
                        <span>{BDT(b.max_savings_bdt ?? b.savings_bdt ?? 0)}</span>
                      </div>
                    </div>

                    {/* 30-Day Inflation Pill */}
                    {((b.shift_30d_pct !== undefined && b.shift_30d_pct !== null) || (b.inflation_30d_pct !== undefined && b.inflation_30d_pct !== null)) && (
                      <div className="mb-4">
                        {(() => {
                          const shift = b.shift_30d_pct ?? b.inflation_30d_pct ?? 0;
                          return (
                            <div
                              className={`flex items-center space-x-1.5 text-xs px-2.5 py-1 rounded-lg ${
                                shift > 0
                                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                                  : shift < 0
                                  ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                                  : 'bg-slate-800 text-slate-300 border border-slate-700'
                              }`}
                            >
                              {shift > 0 ? (
                                <TrendingUp className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
                              ) : shift < 0 ? (
                                <TrendingDown className="w-3.5 h-3.5 flex-shrink-0 text-emerald-400" />
                              ) : null}
                              <span className="font-semibold">
                                ৩০ দিনে {shift > 0 ? `+${shift}% বৃদ্ধি` : shift < 0 ? `${shift}% হ্রাস` : 'অপরিবর্তিত'}
                              </span>
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 pt-3 border-t border-slate-700/60">
                    <button
                      onClick={() => handleLoadSavedBasket(b.id)}
                      className="flex-1 py-1.5 px-3 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center justify-center space-x-1 transition-all"
                    >
                      <ShoppingCart className="w-3.5 h-3.5" />
                      <span>হিসাবে লোড</span>
                    </button>
                    <button
                      onClick={() => handleOpenTrendModal(b.id, b.name, b.bangla_name)}
                      className="p-2 rounded-lg bg-slate-700/80 hover:bg-slate-700 text-sky-300 border border-slate-600 transition-all"
                      title="৩০ দিনের ট্রেন্ড দেখুন"
                    >
                      <LineChart className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDeleteSavedBasket(b.id)}
                      className="p-2 rounded-lg bg-slate-700/80 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-600 transition-all"
                      title="মুছে ফেলুন"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Save Basket Modal ───────────────────────────────────────────── */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <BookmarkCheck className="w-5 h-5 text-amber-400" />
                <span>বাজার বাস্কেট সংরক্ষণ</span>
              </h3>
              <button
                onClick={() => setShowSaveModal(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              ভবিষ্যতে পুনরায় ব্যবহার এবং ৩০ দিনের মুদ্রাস্ফীতি (Personal CPI) ট্র্যাক করার জন্য বর্তমান বাস্কেটটি সংরক্ষণ করুন।
            </p>

            {saveSuccessMsg ? (
              <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs font-semibold flex items-center space-x-2">
                <CheckCircle className="w-4 h-4" />
                <span>{saveSuccessMsg}</span>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    বাস্কেটের নাম (বাংলায়) *
                  </label>
                  <input
                    type="text"
                    value={saveBanglaName}
                    onChange={(e) => setSaveBanglaName(e.target.value)}
                    placeholder="যেমন: মাসিক পরিবারের বাজার"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    বাস্কেটের কোড / ইংরেজি নাম
                  </label>
                  <input
                    type="text"
                    value={saveName}
                    onChange={(e) => setSaveName(e.target.value)}
                    placeholder="e.g. Monthly Family Essentials"
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-400"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    সংক্ষিপ্ত বিবরণ (ঐচ্ছিক)
                  </label>
                  <textarea
                    rows={2}
                    value={saveDescription}
                    onChange={(e) => setSaveDescription(e.target.value)}
                    placeholder="পরিবারের ৪ জনের সাপ্তাহিক খাবার তালিকা..."
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs focus:outline-none focus:border-amber-400"
                  />
                </div>

                {/* Items preview pills */}
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">
                    নির্বাচিত পণ্য ({basket.filter((i) => i.matched).length} টি):
                  </label>
                  <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                    {basket.filter((i) => i.matched).map((i) => (
                      <span
                        key={i.id}
                        className="px-2 py-0.5 rounded bg-slate-700 text-[11px] text-slate-300 border border-slate-600"
                      >
                        {i.bangla_name} ({i.quantity} {i.unit})
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex items-center space-x-2 pt-3">
                  <button
                    onClick={() => setShowSaveModal(false)}
                    className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all"
                  >
                    বাতিল
                  </button>
                  <button
                    onClick={handleSaveBasket}
                    disabled={isSaving || (!saveBanglaName.trim() && !saveName.trim())}
                    className="flex-1 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center justify-center space-x-1.5 transition-all shadow-lg shadow-amber-950/40"
                  >
                    {isSaving ? (
                      <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Save className="w-3.5 h-3.5" />
                    )}
                    <span>সংরক্ষণ করুন</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── 30-Day Personal CPI Trend Modal ─────────────────────────────── */}
      {trendModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl max-w-4xl w-full max-h-[92vh] overflow-y-auto p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <LineChart className="w-5 h-5 text-amber-400" />
                  <h2 className="text-lg font-bold text-white">
                    {trendModal.banglaName || trendModal.trendData?.bangla_name || trendModal.basketName}
                  </h2>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  ব্যক্তিগত ৩০ দিনের CPI ট্রেন্ড, দৈনিক ব্যয় তারতম্য ও চ্যানেল বিশ্লেষণ
                </p>
              </div>
              <button
                onClick={() => setTrendModal(null)}
                className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700 transition-all"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {trendModal.loading ? (
              <div className="p-16 text-center">
                <div className="w-9 h-9 border-3 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-xs text-slate-400">৩০ দিনের ট্রেন্ড ক্যালকুলেট হচ্ছে...</p>
              </div>
            ) : trendModal.error ? (
              <div className="p-4 bg-rose-500/20 border border-rose-500/40 rounded-xl text-rose-300 text-xs">
                {trendModal.error}
              </div>
            ) : trendModal.trendData ? (
              <div className="space-y-5">
                {/* 6 KPI Metric Cards */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3">
                    <span className="text-[11px] text-slate-400 block mb-1">বর্তমান খুচরা ব্যয়</span>
                    <span className="text-sm font-bold text-sky-400">
                      {BDT(trendModal.trendData.current_cost ?? trendModal.trendData.current_retail_cost ?? 0)}
                    </span>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3">
                    <span className="text-[11px] text-slate-400 block mb-1">বর্তমান পাইকারি ব্যয়</span>
                    <span className="text-sm font-bold text-emerald-400">
                      {BDT(
                        trendModal.trendData.current_wholesale_cost ??
                        (trendModal.trendData.trend_points?.length
                          ? trendModal.trendData.trend_points[trendModal.trendData.trend_points.length - 1].wholesale_total
                          : 0)
                      )}
                    </span>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3">
                    <span className="text-[11px] text-slate-400 block mb-1">৩০ দিনের মুদ্রাস্ফীতি</span>
                    {(() => {
                      const inf30 = trendModal.trendData.inflation_30d_pct ?? trendModal.trendData.cpi_inflation_30d_pct ?? 0;
                      return (
                        <span
                          className={`text-sm font-bold ${
                            inf30 > 0 ? 'text-rose-400' : inf30 < 0 ? 'text-emerald-400' : 'text-slate-300'
                          }`}
                        >
                          {inf30 > 0 ? '+' : ''}{inf30}%
                        </span>
                      );
                    })()}
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3">
                    <span className="text-[11px] text-slate-400 block mb-1">৭ দিনের শিফট</span>
                    {(() => {
                      const inf7 = trendModal.trendData.inflation_7d_pct ?? trendModal.trendData.cpi_shift_7d_pct ?? 0;
                      return (
                        <span
                          className={`text-sm font-bold ${
                            inf7 > 0 ? 'text-rose-400' : inf7 < 0 ? 'text-emerald-400' : 'text-slate-300'
                          }`}
                        >
                          {inf7 > 0 ? '+' : ''}{inf7}%
                        </span>
                      );
                    })()}
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3">
                    <span className="text-[11px] text-slate-400 block mb-1">মূল্য অস্থিরতা (CV)</span>
                    <span className="text-sm font-bold text-amber-400">
                      {trendModal.trendData.volatility_cv ?? trendModal.trendData.volatility_cv_pct ?? 0}%
                    </span>
                  </div>

                  <div className="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3">
                    <span className="text-[11px] text-slate-400 block mb-1">সবচেয়ে সাশ্রয়ী দিন</span>
                    <span className="text-xs font-bold text-emerald-400 block truncate" title={trendModal.trendData.cheapest_date}>
                      {trendModal.trendData.cheapest_date || 'N/A'}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {BDT(trendModal.trendData.cheapest_cost ?? trendModal.trendData.min_cost ?? 0)}
                    </span>
                  </div>
                </div>

                {/* Multi-Line Trend Chart (SVG) */}
                <div className="bg-slate-800/50 border border-slate-700/70 rounded-2xl p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                    <div className="text-xs font-bold text-white flex items-center space-x-2">
                      <BarChart2 className="w-4 h-4 text-amber-400" />
                      <span>দৈনিক বাস্কেট খরচ পরিবর্তন (গত ৩০ দিন)</span>
                    </div>
                    {/* Legend */}
                    <div className="flex items-center space-x-4 text-xs">
                      <span className="flex items-center space-x-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block" />
                        <span className="text-slate-300">পাইকারি</span>
                      </span>
                      <span className="flex items-center space-x-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-sky-400 inline-block" />
                        <span className="text-slate-300">খুচরা</span>
                      </span>
                      <span className="flex items-center space-x-1.5">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
                        <span className="text-slate-300">অনলাইন</span>
                      </span>
                    </div>
                  </div>

                  <TrendChartSVG points={trendModal.trendData.trend_points || trendModal.trendData.points || []} />
                </div>

                {/* Economic / Academic Narrative */}
                <div className="bg-amber-500/10 border border-amber-500/25 rounded-2xl p-4 space-y-1.5">
                  <div className="flex items-center space-x-2 text-xs font-bold text-amber-300">
                    <Lightbulb className="w-4 h-4" />
                    <span>অর্থনৈতিক মূল্যায়ন ও পর্যবেক্ষণ (Academic Narrative)</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {trendModal.trendData.academic_narrative || trendModal.trendData.narrative}
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* ── Printable Receipt ─────────────────────────────────────────── */}
      {result && (
        <div className="bb-print-receipt">
          <h2 className="text-xl font-bold text-center mb-2">PricePulse BD • বাজার রসিদ</h2>
          <p className="text-center text-sm text-gray-500 mb-4">
            {new Date().toLocaleDateString('bn-BD', { dateStyle: 'full' })}
          </p>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-300">
                <th className="text-left py-1">পণ্য</th>
                <th className="text-right py-1">পরিমাণ</th>
                <th className="text-right py-1">দাম</th>
              </tr>
            </thead>
            <tbody>
              {result.item_details.map((d, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-1">{d.bangla_name}</td>
                  <td className="py-1 text-right">{d.quantity_normalized} {d.standard_unit}</td>
                  <td className="py-1 text-right">{BDT(d.line_total)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-gray-400 font-bold">
                <td colSpan={2} className="py-2">মোট</td>
                <td className="py-2 text-right">{BDT(result.benchmark_total)}</td>
              </tr>
              <tr>
                <td colSpan={2} className="py-1 text-gray-600">পাইকারি বাজারে</td>
                <td className="py-1 text-right text-green-700">{BDT(result.wholesale_total)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Channel Card Sub-Component ────────────────────────────────────────────────
function ChannelCard({ label, sublabel, total, benchmark, colorClass, isBest, isBaseline }) {
  const diff = total - benchmark;
  const diffPct = benchmark > 0 ? ((diff / benchmark) * 100).toFixed(1) : '0.0';
  const isCheaper = diff < 0;
  const isExpensive = diff > 0;

  const BDT = (v) => `৳${Math.abs(v).toLocaleString('en-BD', { maximumFractionDigits: 0 })}`;

  return (
    <div className={`bb-channel-card ${isBest ? 'bb-channel-best' : ''}`}>
      {isBest && (
        <span className="bb-channel-best-badge">
          <CheckCircle className="w-3 h-3" /> সর্বোত্তম
        </span>
      )}
      <div className="bb-channel-label">{label}</div>
      <div className="bb-channel-sublabel">{sublabel}</div>
      <div className="bb-channel-total">
        <span>৳</span>
        {Math.round(total).toLocaleString('en-BD')}
      </div>
      {isBaseline ? (
        <span className="bb-channel-baseline-pill">ভিত্তিমূল্য</span>
      ) : isCheaper ? (
        <span className="bb-channel-save-pill">
          <TrendingDown className="w-3 h-3" />
          সাশ্রয় {BDT(diff)} ({diffPct}%)
        </span>
      ) : isExpensive ? (
        <span className="bb-channel-premium-pill">
          <TrendingUp className="w-3 h-3" />
          +{BDT(diff)} অতিরিক্ত
        </span>
      ) : null}
    </div>
  );
}

// ─── Pure SVG 30-Day Trend Chart Component ──────────────────────────────────
function TrendChartSVG({ points }) {
  if (!points || points.length === 0) {
    return (
      <div className="py-12 text-center text-xs text-slate-500">
        পর্যাপ্ত ঐতিহাসিক ডাটা অনুপস্থিত
      </div>
    );
  }

  const svgWidth = 720;
  const svgHeight = 220;
  const padLeft = 55;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const chartW = svgWidth - padLeft - padRight;
  const chartH = svgHeight - padTop - padBottom;

  // Find min and max across all channels
  let minCost = Infinity;
  let maxCost = -Infinity;
  points.forEach((p) => {
    const w = p.wholesale_total ?? p.wholesale_cost;
    const r = p.retail_total ?? p.retail_cost;
    const o = p.online_total ?? p.online_cost;
    [w, r, o].forEach((val) => {
      if (val !== null && val !== undefined) {
        if (val < minCost) minCost = val;
        if (val > maxCost) maxCost = val;
      }
    });
  });

  if (minCost === Infinity) {
    minCost = 0;
    maxCost = 1000;
  }
  // 8% margin padding
  const margin = Math.max((maxCost - minCost) * 0.08, 10);
  const yMin = Math.max(0, minCost - margin);
  const yMax = maxCost + margin;
  const yRange = yMax - yMin || 1;

  const n = points.length;
  const getX = (idx) => padLeft + (idx / Math.max(n - 1, 1)) * chartW;
  const getY = (val) => padTop + chartH - ((val - yMin) / yRange) * chartH;

  const buildPath = (keys) => {
    return points
      .map((p, idx) => {
        let val = null;
        for (const k of keys) {
          if (p[k] !== undefined && p[k] !== null) {
            val = p[k];
            break;
          }
        }
        if (val === null) return null;
        const x = getX(idx);
        const y = getY(val);
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .filter(Boolean)
      .join(' ');
  };

  const wholesalePath = buildPath(['wholesale_total', 'wholesale_cost']);
  const retailPath = buildPath(['retail_total', 'retail_cost']);
  const onlinePath = buildPath(['online_total', 'online_cost']);

  // Horizontal Gridlines (4 levels)
  const gridLevels = [0, 0.33, 0.66, 1];

  return (
    <div className="w-full overflow-x-auto">
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        className="w-full h-auto min-w-[500px]"
        style={{ fontVariantNumeric: 'tabular-nums' }}
      >
        {/* Gridlines & Y-Axis Labels */}
        {gridLevels.map((frac, i) => {
          const val = yMin + frac * yRange;
          const y = padTop + chartH - frac * chartH;
          return (
            <g key={i}>
              <line
                x1={padLeft}
                y1={y}
                x2={svgWidth - padRight}
                y2={y}
                stroke="#334155"
                strokeDasharray="3 3"
                strokeWidth="1"
              />
              <text
                x={padLeft - 8}
                y={y + 3.5}
                textAnchor="end"
                fontSize="10"
                fill="#94a3b8"
              >
                ৳{Math.round(val)}
              </text>
            </g>
          );
        })}

        {/* Channels Lines */}
        {onlinePath && (
          <path
            d={onlinePath}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="2"
            strokeDasharray="4 3"
            opacity="0.85"
          />
        )}
        {wholesalePath && (
          <path
            d={wholesalePath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        )}
        {retailPath && (
          <path
            d={retailPath}
            fill="none"
            stroke="#38bdf8"
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        )}

        {/* Data points (dots) */}
        {points.map((p, idx) => {
          const x = getX(idx);
          const rVal = p.retail_total ?? p.retail_cost;
          const wVal = p.wholesale_total ?? p.wholesale_cost;
          const yRetail = rVal !== null && rVal !== undefined ? getY(rVal) : null;
          const yWholesale = wVal !== null && wVal !== undefined ? getY(wVal) : null;
          return (
            <g key={idx}>
              {yRetail !== null && (
                <circle cx={x} cy={yRetail} r="3" fill="#38bdf8">
                  <title>{`${p.date}: খুচরা ৳${Math.round(rVal)}`}</title>
                </circle>
              )}
              {yWholesale !== null && (
                <circle cx={x} cy={yWholesale} r="3" fill="#10b981">
                  <title>{`${p.date}: পাইকারি ৳${Math.round(wVal)}`}</title>
                </circle>
              )}
            </g>
          );
        })}

        {/* X-Axis Date Labels (Every ~5-6 points) */}
        {points.map((p, idx) => {
          if (idx % 6 !== 0 && idx !== n - 1) return null;
          const x = getX(idx);
          const shortDate = p.date.length > 5 ? p.date.slice(5) : p.date;
          return (
            <text
              key={idx}
              x={x}
              y={svgHeight - 10}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              {shortDate}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
