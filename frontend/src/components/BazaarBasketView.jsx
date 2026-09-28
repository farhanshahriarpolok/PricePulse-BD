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
} from 'lucide-react';
import { getCommodities, calculateBasket, getBasketPresets } from '../api/endpoints';

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
  // ── State ────────────────────────────────────────────────────────────────
  const [commodities, setCommodities] = useState([]);
  const [presets, setPresets] = useState([]);
  const [basket, setBasket] = useState([]); // {commodity_id, commodity_name, bangla_name, quantity, unit}
  const [result, setResult] = useState(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState(null);
  const [presetsLoaded, setPresetsLoaded] = useState(false);

  // Item adder state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommodity, setSelectedCommodity] = useState(null);
  const [adderQty, setAdderQty] = useState(1);
  const [adderUnit, setAdderUnit] = useState('kg');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  // ── Load commodities and presets on mount ─────────────────────────────────
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
  }, []);

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

  // ─────────────────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="bazaar-basket-root">

      {/* ── Page Header ──────────────────────────────────────────────── */}
      <div className="bb-page-header">
        <div className="bb-header-icon">
          <ShoppingBasket className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="bb-page-title">বাজার বাস্কেট ক্যালকুলেটর</h1>
          <p className="bb-page-subtitle">
            আপনার কাস্টম বাজারের খরচ তুলনা করুন — পাইকারি · খুচরা · অনলাইন
          </p>
        </div>
        <div className="bb-basket-count-badge">
          <ShoppingBasket className="w-3.5 h-3.5" />
          <span>Basket ({validBasketCount})</span>
        </div>
      </div>

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
