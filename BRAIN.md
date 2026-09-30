# BRAIN.md — Compressed Project Intelligence & State of Truth

This file stores high-density, durable project intelligence for **PricePulse BD**. It represents the active technical reality of the platform and serves as the primary context repository for architectural reasoning.

---

## 1. What PricePulse BD Is

**PricePulse BD** is an academically grounded, local-first commodity market intelligence and anomaly detection platform for Bangladesh's essential agricultural goods.

- **Primary Goal**: Bridge the information asymmetry between agricultural growers, wholesale traders (arathdars), retail wet markets (kacha bazaars), and urban consumers.
- **Core Technology**:
  - FastAPI (Python 3.11) with SQLite 3 (WAL mode).
  - React 18 + Vite with TailwindCSS, Lucide, Recharts, and Leaflet.
  - Native Android (Kotlin, Jetpack Compose, Room Database, Custom Canvas).
  - 100% deterministic statistical analysis without external cloud AI dependencies.
- **Author**: Farhan Shahriar Polok (CSE Final Year Thesis, 2026).

---

## 2. Market Taxonomy & Spatial Geometry

### The 21-Commodity Canonical Basket
Structured across 5 fundamental food categories defined in `data/taxonomy/commodities.json`:
1. **Grains & Pulses**: Rice (Miniket), Rice (Nazirshail), Rice (Coarse/Mota), Lentil (Masoor - Local), Lentil (Masoor - Imported), Chickpea (Chhola), Flour (Atta - Packet).
2. **Vegetables**: Potato (Diamond), Onion (Local), Onion (Imported), Green Chilli, Tomato, Garlic (Local), Ginger (Imported).
3. **Meat & Fish**: Broiler Chicken, Beef, Rui Fish, Pangas Fish.
4. **Spices & Oils**: Soybean Oil (Bottled), Mustard Oil, Turmeric Powder.
5. **Dairy & Eggs**: Farm Eggs (Brown).

### Spatial Coverage (64 Districts & 78 Markets)
- **Divisions (8)**: Dhaka, Chittagong, Rajshahi, Khulna, Barisal, Sylhet, Rangpur, Mymensingh.
- **Districts**: All 64 official administrative districts with geographic centroids and Haversine distance matrix from Dhaka center.
- **Primary Wholesale Hubs**: Karwan Bazar (Dhaka), Khatunganj (Chittagong), Raja Bazar (Bogura), City Bazar (Rangpur), Boro Bazar (Jashore), Badamtoli (Dhaka).
- **Transport Arbitrage Model**:
  $$C_{\text{freight}} = 1.50 + 0.018 \cdot (d \times 1.25) \quad (\text{BDT/kg})$$
  where $d$ is the great-circle Haversine distance scaled by a $1.25$ highway circuity factor.

---

## 3. Mathematical Analytical Engine

All anomaly calculations are strictly deterministic and mathematically defensible:

1. **14-Day Rolling Baseline ($SMA_{14}$)**:
   $$SMA_{14}(t) = \frac{1}{14}\sum_{i=0}^{13} P(t-i)$$

2. **Dynamic Z-Score ($Z$)**:
   $$Z(t) = \frac{P(t) - SMA_{14}(t)}{\sigma_{14}(t)}$$
   - Critical Alert: $|Z| \ge 2.5$ or 7-day rate of change $|\Delta_{7d}| \ge 15\%$.
   - Direction: `SPIKE` (positive deviation) vs `DROP` (negative deviation).

3. **Coefficient of Variation ($CV$)**:
   $$CV = \frac{\sigma_{14}}{\mu_{14}} \times 100\%$$
   Measures price volatility regime ($CV > 12\%$ indicates high instability).

4. **Spatial Price Dispersion Index ($D(t)$)**:
   $$D(t) = \frac{1}{\bar{P}} \sqrt{\frac{1}{N}\sum_{i=1}^N (P_i(t) - \bar{P}(t))^2}$$
   Quantifies inter-district price divergence across Bangladesh.

---

## 4. Consumer Bazaar Basket & Shopping Optimizer

Integrated under Milestone 013 (`app/services/basket_service.py`):
- **Bilingual Unit Normalizer**:
  - Handles `হালি` (4 units), `পোয়া` (0.25 kg), `মণ` (40 kg), `৫০০ গ্রাম` (0.5 kg).
- **Multi-Channel Price Imputation**:
  - Compares Wholesale vs Retail vs Online (Chaldal) channels.
  - Imputes missing channel observations (+8% online retail markup, -15% wholesale volume discount).
- **Persistent Saved Baskets**:
  - Tables: `saved_baskets` and `saved_basket_items`.
  - Computes 30-day personal CPI inflation trends, historical volatility, and plain-language Bengali shopping explanations.
- **Smart Substitute Recommender**:
  - Automatically identifies local vs imported price disparities (e.g., suggesting Local Onion when Imported surges, or Masoor Local vs Masoor Imported).

---

## 4.5. Phase 3 Forecasting, Rolling Backtesting & Direction Signals

Integrated under Phase 3 (`app/services/forecast_service.py`):
- **Hybrid Candidate Set**:
  - Naive persistence: $P(t+h) = P(t)$.
  - SMA-7: Mean of the trailing 7 observations.
  - SMA-14: Mean of the trailing 14 observations.
  - Formal non-seasonal ARIMA(1,1,0) with exact analytical OLS AR(1) fallback for edge cases.
- **Strict Data Eligibility**:
  - `PANDAMART_MODELED` records are strictly excluded from empirical series extraction.
  - Minimum 14 distinct dates and $\ge 7$ continuous daily streak required. Commodities with sparse history (e.g., imported onion) return explicit `INSUFFICIENT_DATA` rather than fabricated forecasts.
- **Rolling Walk-Forward Backtesting**:
  - $T_{\text{train}} = 14$ days, $H = 7$ days forecast horizon.
  - Strictly chronological walk-forward splits with absolute zero future data leakage ($\max(\text{train\_indices}) < \min(\text{val\_indices})$).
  - Out-of-sample MAE and RMSE evaluated for all candidate models; the lowest-MAE model is dynamically selected.
- **Parametric Uncertainty Interval & Direction Signal**:
  - 95% confidence interval derived from walk-forward backtest empirical RMSE:
    $$\text{Interval}_h = \hat{P}_h \pm 1.96 \cdot \text{RMSE} \cdot \sqrt{\frac{h}{7}}$$
  - Direction classified as `UP`, `DOWN`, `STABLE`, or `UNAVAILABLE`.
  - Base deadband threshold is $\pm 3.0\%$, modulated upwards by historical volatility ($\text{Effective Threshold} = \max(3.0\%, 1.5 \cdot CV_{14})$).
- **Documented Limitations**:
  - The historical dataset contains approximately 33 calendar days. This sample size supports short-term 7-day projections and rolling backtesting across ~13 windows, but does NOT statistically establish long-term or weekly seasonal (SARIMA) dynamics.

---

## 5. Architectural Invariants & Data Integrity

- **Database**: Single SQLite file with WAL mode (`pricepulse.db`). Foreign keys enabled.
- **No Cloud AI / LLM Calls in Core Engine**: All anomalies, narratives, and recommendations are computed via deterministic logic and formatted templates.
- **Simulation Sandbox Isolation**: The Viva Simulation engine (`/api/v1/simulation/inject-shock`) tests scenarios in memory without altering ground-truth SQLite database records.

---

## 6. Active Risk Register

| Risk | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **Upstream Harvester Block / DOM Drift** | HIGH | Offline HTML/JSON fallback fixtures in `data/fixtures/`; source health metrics tracking consecutive failure counts. |
| **Concurrent SQLite Write Contention** | MEDIUM | SQLite WAL mode enabled with `PRAGMA busy_timeout = 5000;`. |
| **Android Build Machine Variability** | MEDIUM | Provided `scripts/setup_android_sdk.py` and Gradle wrapper with pinned SDK 34 toolchain. |
| **Academic Thesis Metric Drift** | LOW | Automated benchmark scripts (`scripts/run_all_benchmarks.py`) sync directly into LaTeX tables and `combined_summary.json`. |

---

## 7. Current Project State & Verification Summary

- **Total Test Suite**: 331 passed (100% green — 17 Phase 3 forecasting tests + 21 Phase 2 spatial consumer tests + 41 Phase 1 regression tests across audit fixes).
- **FastAPI Endpoints**: Realtime pulse, commodities (catalog + history + compare + multi-store prices + **7-day price forecast**), locations (districts, markets, spatial-arbitrage, consumer-opportunity), anomalies, simulation sandbox, bazaar basket optimizer, saved baskets.
- **Retail Collectors**: DAM (government), TCB (statutory), Chaldal (e-commerce), Shwapno (superstore live API), Meena Bazar (superstore live API), Pandamart (transparent modeled).
- **Frontend State**: React 18 + Vite, single-page application with 6 core navigation tabs (Market Pulse, Commodity Explorer with **Hybrid Spatial Opportunity Panel & 7-Day Forecast Outlook Panel**, 64-District Map, Anomaly Alerts, Viva Simulator, Bazaar Basket). Production build verified (2495 modules).
- **Android State**: SDK 34 client with Room database offline cache, Custom Canvas sparklines, and Jetpack Compose screens. Android code is completely frozen and untouched.
