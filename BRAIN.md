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

- **Total Test Suite**: 285 passed (100% green — 33 regression tests added in Phase 1).
- **FastAPI Endpoints**: Realtime pulse, commodities (catalog + history + compare + **multi-store prices**), locations, anomalies, spatial arbitrage, simulation sandbox, bazaar basket optimizer, saved baskets.
- **Retail Collectors**: DAM (government), TCB (statutory), Chaldal (e-commerce), **Shwapno** (superstore live API), **Meena Bazar** (superstore live API), **Pandamart** (transparent modeled).
- **Frontend State**: React 18 + Vite, single-page application with 6 core navigation tabs (Market Pulse, Commodity Explorer, 64-District Map, Anomaly Alerts, Viva Simulator, Bazaar Basket). Production build verified (2493 modules).
- **Android State**: SDK 34 client with Room database offline cache, Custom Canvas sparklines, and Jetpack Compose screens.
