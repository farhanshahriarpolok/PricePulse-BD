# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-09-29

### Added
- **Visual Identity, Custom Vector Assets & Mass-Consumer UI Media Polish (Milestone 021)**:
  - `frontend/public/logo.svg`: Designed official modern vector brand emblem featuring an integrated market scale, pulse graph wave, and emerald agricultural leaf motif.
  - `frontend/public/favicon.svg`: High-contrast pixel-perfect 32x32 SVG favicon for web and mobile browsers.
  - `frontend/public/og-image.svg`: Bespoke 1200x630 OpenGraph and Twitter social card banner with live commodity metrics and localized branding.
  - `frontend/index.html`: Fully updated with `favicon.svg` link and complete OpenGraph and Twitter card meta tags.
  - `frontend/src/components/media/CommodityIcon.jsx`: Created handcrafted vector illustration system for all staple categories (Vegetables, Grains & Pulses, Meat & Fish, Dairy & Eggs, Oils & Spices) with individual commodity signature dispatching.
  - `frontend/src/components/CommodityCard.jsx`: Embedded bespoke `CommodityIcon` in both hero and standard card variants.
  - `frontend/src/components/CategoryFilter.jsx`: Replaced generic icon placeholders with matching custom vector emblems.
  - `frontend/src/components/BazaarBasketView.jsx`: Rendered bespoke commodity vector icons in basket line items.
  - `frontend/src/components/Navbar.jsx`: Refined brand header with new vector `logo.svg` and added a pulse dot indicator beside the bilingual `[বাংলা | EN]` switcher.
  - Verified visual asset rendering with Playwright MCP headless audit snapshot (`scripts/qa_snapshots/10_media_polish.png`).

## [2.0.0] - 2026-09-29

### Added
- **Full National Production & Academic Synchronization Milestone (TASK-005 / Milestone 019)**:
  - `report/chapters/05_anomaly_engine.tex`:
    - Updated Spatial Arbitrage modeling with formal Highway Transit Corridor equations:
      $$\text{Transit Hours} = \frac{d_{\text{road}}}{45} + \text{Buffer Hours}$$
      $$\text{Total Freight} = 1.50 + 0.018 \cdot d_{\text{road}} + \text{Toll Buffer}$$
    - Documented bridge toll and delay parameters for Bangabandhu Jamuna Bridge corridor (৳0.50/kg, 1.2h), Padma Multipurpose Bridge corridor (৳0.60/kg, 0.8h), and N1/Trans-national corridors (৳0.75-0.85/kg, 1.8-2.2h).
  - `report/chapters/06_evaluation.tex`:
    - Updated automated test suite metrics across the thesis to reflect all 236 passing tests, 21 canonical staples, 64 administrative districts, and 78 markets.
    - Added Table 6.4 summarizing test suite coverage by subsystem domain with 100.0% pass rate.
  - `report/compile_report.py`:
    - Synchronized executive specifications table with Highway Transit Corridors and 236 test cases.
    - Verified ReportLab compilation producing `report/PricePulse_BD_Thesis.pdf` (57 KB).
  - `docs/DEMO_SCRIPT.md`:
    - Standardized 6-step commercial live demo walkthrough:
      1. Market Pulse & 7d Sparkline Cards (Top Mover Hero Card & bilingual search).
      2. Consumer Bazaar Basket (3-channel wholesale vs retail savings, saved household baskets, 30d personal CPI trend).
      3. Market Stress Test Sandbox (dynamic shock slider without DB mutation, deterministic explanation generation).
      4. 64-District Leaflet Map with Highway Transit Corridors (Jamuna & Padma corridors, waypoints, freight breakdown drawer).
      5. Upstream Source Health Telemetry (zero-downtime cached fallback resilience).
      6. Native Android Client Offline Room Mirroring & Data Provenance Lineage.
  - `docs/API_SPEC.md`:
    - Documented persistent Saved Basket endpoints (`GET /api/v1/basket/saved`, `POST /api/v1/basket/saved`, `GET /api/v1/basket/saved/{id}/trend`).
    - Documented Highway Transit Corridor Spatial Arbitrage endpoint (`GET /api/v1/locations/arbitrage`) with waypoint polylines, toll buffers, and freight breakdowns.
  - **Quality & Release Assurance**:
    - 236 of 236 pytest tests passing with zero failures.
    - `run_system.py --test` passes all 4 environment checks.
    - Frontend production bundle cleanly built with Vite.

## [1.11.0] - 2026-09-29

### Added
- **Spatial Arbitrage Engine Enhancements & Interactive Transit Corridors (TASK-004)**:
  - `app/schemas/spatial.py`:
    - Extended `ArbitrageRoute` with `waypoints` (highway polyline coordinates), `transit_hours_estimated`, `toll_and_buffer_cost_bdt`, `freight_breakdown` (base freight, toll buffer, net margin), and `corridor_name`.
  - `app/services/spatial_service.py`:
    - Modeled realistic national highway transit corridors: N5 Jamuna (Bogura/Rangpur/Dinajpur/Rajshahi ➔ Dhaka), N1 Highway (Chattogram ➔ Dhaka), N8 Padma (Jashore/Barishal ➔ Dhaka), N2 Sylhet (Sylhet ➔ Dhaka), and cross-regional arterials.
    - Integrated river crossing toll and bottleneck cost buffers (৳0.50 - ৳0.85/kg) and transit duration estimation (`d / 45 + buffer_hours`).
  - `frontend/src/components/BangladeshPriceMap.jsx`:
    - Added "Show Transit Corridors" (পরিবহন করিডোর) toggle switch in map header.
    - Rendered dynamic React-Leaflet `<Polyline>` corridors with feasibility-driven color coding: Emerald (`Highly Feasible`), Amber (`Marginal`), Rose (`Infeasible`).
    - Added responsive, interactive glassmorphic corridor breakdown drawer with highway distance, transit time in hours, gross spread, base freight vs bridge toll breakdown, net margin, and ROI.
    - Interactive matrix table allows selecting and focusing corridors directly on the geospatial map.
  - `tests/test_national_spatial.py`:
    - Added `test_spatial_arbitrage_corridors_and_waypoints` validating polyline coordinates structure, transit duration, toll buffer injection, and N5 Jamuna corridor accuracy.

## [1.10.0] - 2026-09-29

### Added
- **TCB & DAM Live Harvester Hardening & Adaptive DOM Parsing (TASK-003)**:
  - `app/collectors/tcb_collector.py`:
    - Multi-strategy CSS selectors (`table.tcb-price-table`, `table.price-table`, `table.content-table`, `.content-table table`, `table.table-bordered`, `table.table`) for resilient table discovery across upstream DOM shifts.
    - Adaptive column detection identifying commodity, unit, min price, max price, and average price indices dynamically from header cells.
    - Enhanced numeral parser handling Bengali (`১২০ - ১৩০`, `১২০ থেকে ১৩০`) and English (`120 - 130`, `120 to 130`) ranges and currency suffixes (`টাকা`, `Tk/kg`).
    - Exponential backoff with randomized jitter (`base * 2^attempt + uniform(0, 0.5)`) and zero-halt fallback to verified cached fixtures.
  - `app/collectors/dam_live_collector.py`:
    - Adaptive column order detection accommodating varying wholesale vs retail column orderings.
    - Support for Bengali numerals in table price cells.
    - Granular network error telemetry recording (`ConnectTimeout`, `DNS/ConnectError`, `HTTPStatusError`) in `SourceHealthService`.
    - Exponential backoff retry jitter to survive transient gateway timeouts.
  - `app/services/scheduler.py`:
    - Integrated all four collectors (`DAMLiveCollector`, `ChaldalLiveCollector`, `TCBCollector`, `NewsCollector`) into periodic and on-demand synchronization workers with localized imports to eliminate circular import risks.
  - `scripts/sync_daily_prices.py`:
    - Formatted ASCII console summary table displaying Source, Status, Harvested, Inserted, Updated, and Latency for operational clarity.
  - `tests/test_resilient_collectors.py`:
    - 8 comprehensive unit tests validating TCB DOM mutation tolerance, exponential backoff retries, DAM adaptive column swapping, Bengali numeral support, and SourceHealth status lifecycle transitions (`HEALTHY` -> `DEGRADED` -> `OFFLINE`).

## [1.9.0] - 2026-09-29

### Added
- **Android Native Jetpack Compose Bazaar Basket & Room Integration**:
  - `BasketScreen.kt`: Commercial-grade consumer shopping optimizer screen built with Jetpack Compose Material 3:
    - Quick-select preset chips ("সাপ্তাহিক বাজার", "ব্যাচেলর বাস্কেট", "উইকেন্ড ফিস্ট") with one-tap populating.
    - Active basket item cards with quantity stepper (`-`/`+`), customary units (`কেজি`, `হালি`, `লিটার`), and line total calculation.
    - 3-Channel Cost Overview Hero Card comparing Local Wet Market Retail baseline, Wholesale Hub (with green savings pill), and Online Grocery.
    - Saved Baskets Section reading reactive `offlineRepository.savedBaskets` Flow from local Room DB with 1-tap load and delete actions.
    - Save Basket dialog persisting custom household baskets to Room DB for 100% offline market visits.
  - `MainActivity.kt`: Integrated bottom `NavigationBar` with edge-to-edge `Scaffold` routing across `Pulse` (Home), `Anomalies`, `Basket`, and `Report`.

## [1.8.1] - 2026-09-29

### Added
- **Android Native Client Room Offline Saved Basket Mirroring**:
  - `android/app/src/main/java/com/pricepulse/bd/data/local/Entities.kt`: Added `SavedBasketEntity` and `SavedBasketItemEntity` with auto-generated primary keys and foreign key constraints mirroring FastAPI schemas.
  - `android/app/src/main/java/com/pricepulse/bd/data/local/Daos.kt`: Added `BasketDao` with reactive `Flow<List<SavedBasketEntity>>`, basket item flows, atomic inserts, and cascade deletions.
  - `android/app/src/main/java/com/pricepulse/bd/data/local/PricePulseDatabase.kt`: Bumped Room database schema to `version = 2` and registered `SavedBasketEntity`, `SavedBasketItemEntity`, and `basketDao()`.
  - `android/app/src/main/java/com/pricepulse/bd/data/repository/OfflinePriceRepository.kt`: Exposed `savedBaskets` Flow, `getItemsForBasket()`, `saveBasketLocally()`, and `deleteBasketLocally()` for offline mobile shopping.

### Changed
- **Runtime & API Documentation Sanitization**:
  - `run_system.py`: Sanitized orchestrator console banner to "National Commodity Price Intelligence & Cost of Living Platform" and updated startup comments.
  - `app/api/v1/endpoints/simulation.py`: Sanitized endpoint tags to "Market Stress Test", summary to "Simulate Market Supply Shock & Policy Stress Test", and description with zero student/viva disclaimers.

## [1.8.0] - 2026-09-29

### Added
- **Production Rebranding & Consumer UI Cleansing (Commercial Polish)**:
  - Rebranded "Viva Simulator" to "Market Stress Test & Economic Scenario Engine" across navigation and scenario testbed.
  - Set authoritative header brand subtitle: "National Market Price Intelligence & Basket Optimizer".
  - Sanitized `frontend/index.html` with national title and meta description: "PricePulse BD — Bangladesh Commodity Price Intelligence & Cost of Living Tracker".
  - Rephrased explainable alert justification to "Algorithmic Anomaly Detection Analysis" and basket narrative to "বাজার বিশ্লেষণ ও অর্থনৈতিক পর্যবেক্ষণ (Market Analysis & Insights)".
  - Updated provenance panel and application footer to authoritative civic-tech standards: "National Commodity Market Intelligence & Cost of Living Platform".
  - Verified 0 occurrences of academic or student disclaimers across all user-facing frontend code.
- **Resilient Storefront Harvester Engine & Multi-Source Daily Sync**:
  - Enhanced `ChaldalLiveCollector` in `app/collectors/chaldal_live_collector.py` with multi-format JSON catalog extraction (`items`, `products`, `data`), BeautifulSoup CSS selector DOM fallback for storefront cards, dynamic stock status filtering (`in_stock`, `stock_status`, `out_of_stock`), and package unit resolution.
  - Enhanced `scripts/sync_daily_prices.py` to support all 4 primary sources: Department of Agricultural Marketing (`dam`), Chaldal Online Grocery (`chaldal`), Trading Corporation of Bangladesh (`tcb`), and Newspaper Press Roundups (`news`).
  - Added `ingest_observations()` helper function in `app/services/ingestion.py` and `record_health_event()` telemetry dispatcher in `app/services/source_health.py`.

## [1.7.0] - 2026-09-28

### Added
- **Persistent Saved Baskets Engine & 30-Day Personal CPI Trend Trajectory**:
  - `app/models/basket.py`: SQLAlchemy ORM models `SavedBasket` and `SavedBasketItem` with cascade deletion, tracking user-customized household shopping baskets and quantities.
  - `app/schemas/basket.py`: Added `SavedBasketCreateIn`, `SavedBasketItemIn`, `SavedBasketSummaryOut`, `SavedBasketDetailOut`, `SavedBasketItemOut`, `BasketTrendPoint`, and `BasketTrendResponse` schemas.
  - `app/services/basket_service.py`: Added `save_basket()`, `list_saved_baskets()`, `get_saved_basket()`, `delete_saved_basket()`, and `calculate_basket_trend()` with 30-day chronological price trajectory reconstruction, personal inflation percentage ($\Delta_{30d}\%$, $\Delta_{7d}\%$), coefficient of variation ($CV$), anomaly threshold tagging, and plain-language Bengali narrative synthesis.
  - `app/api/v1/endpoints/basket.py`: Added REST endpoints:
    - `POST /api/v1/basket/saved` — create persistent saved household basket.
    - `GET /api/v1/basket/saved` — list all saved baskets with real-time price totals and 7d/30d inflation indicators.
    - `GET /api/v1/basket/saved/{id}` — retrieve single saved basket with calculation and item details.
    - `DELETE /api/v1/basket/saved/{id}` — delete saved basket.
    - `GET /api/v1/basket/saved/{id}/trend` — 30-day cost trajectory, volatility metrics, and personal inflation analysis.
  - `frontend/src/components/BazaarBasketView.jsx`: Added "Save Basket" modal, "My Saved Baskets" collection drawer with quick-load and delete actions, and full 30-day interactive Personal CPI Trend Modal featuring multi-channel cost trajectories, peak/cheapest markers, volatility index, and Bengali synthesis callouts.
  - `tests/test_saved_baskets.py`: Comprehensive 10-test suite verifying saved basket persistence, custom unit handling (`পোয়া`), 404/422 validations, cascade deletion, and 30-day trend trajectory mathematics.
- **Repository Control Layer & Governance Framework**:
  - Established durable operational contracts: `AGENTS.md` (operational contract & invariants), `CLAUDE.md` (context entry point), `TASKS.md` (execution queue), and `BRAIN.md` (compressed project intelligence).
- **Consumer "Bazaar Basket" & Cost of Living Tracker (Shopping Optimizer)**:
  - `app/schemas/basket.py`: Pydantic schemas `BasketItemInput`, `BasketCalculationRequest`, `ChannelCostBreakdown`, `BasketItemCostDetail`, `BasketCalculationResponse` covering all basket calculus data contracts with full field documentation.
  - `app/services/basket_service.py`: `BasketOptimizationService` — comprehensive basket calculus engine that normalizes customary units (`হালি` → 4 pc, `পোয়া` → 0.25 kg, `মণ` → 40 kg, `500ml` → 0.5 liter) via the existing `CommodityNormalizer`, pulls today's wholesale/retail/online prices per commodity from the DB using a single-pass SQL query with a 14-day trailing window, imputes missing channel prices from cross-channel averages (online defaults to +8% premium when absent), computes 7-day personal inflation shift (Δ% = (today − t7) / t7 × 100), generates smart substitute savings recommendations using a commodity close-variant map, and produces consumer-friendly Bengali procurement explanations.
  - `app/api/v1/endpoints/basket.py`: Two REST endpoints registered under `/api/v1/basket`:
    - `POST /api/v1/basket/calculate` — public endpoint computing optimized channel breakdown in <15ms; returns benchmark_total, wholesale_total, retail_total, online_total, best_channel, max_savings_bdt, savings_explanation (Bengali), cost_shift_7d_pct, cost_shift_7d_bdt, item_details, and smart_saving_tips.
    - `GET /api/v1/basket/presets` — three pre-defined family baskets: "Middle-Class Weekly Essentials" (চাল ৫ কেজি, ডাল, পেঁয়াজ, আলু, তেল, ডিম), "Bachelor Fast Basket" (ডিম, আলু, পেঁয়াজ, তেল, কাঁচা মরিচ), "Family Weekend Feast" (গরুর মাংস, পোলাও চাল, পেঁয়াজ, সরিষার তেল, রসুন).
  - `app/api/v1/router.py`: Registered `basket.router` in the v1 API aggregator.
  - `frontend/src/components/BazaarBasketView.jsx`: Full React component with preset quick-load buttons, searchable bilingual commodity dropdown, quantity `−/+` stepper, unit selector (কেজি/লিটার/হালি/পিস/পোয়া), animated add-to-basket, active basket table with inline edit, Hero Total display, 3-channel comparison meter (Wholesale/Retail/Online with savings pills), 7-day cost shift banner, smart saving tips lightbulb card, and print/share export actions.
  - `frontend/src/components/Navbar.jsx`: Added "🧺 Bazaar Basket" nav tab with amber accent coloring and floating mini-cart count badge (shows item count).
  - `frontend/src/App.jsx`: Integrated `BazaarBasketView` tab panel and wired `basketItemCount` state to the Navbar `basketCount` prop.
  - `frontend/src/api/endpoints.js`: Added `calculateBasket()` (POST) and `getBasketPresets()` (GET) API client functions.
  - `frontend/src/index.css`: Added comprehensive `.bb-*` CSS component classes for the Bazaar Basket view using Tailwind `@apply` directives, plus print-only receipt stylesheet.
  - `tests/test_basket_service.py`: 35-test comprehensive test suite covering: unit normalization (হালি, পোয়া, 500ml, g), `_ChannelPrices` aggregation, wholesale vs retail savings arithmetic, 7-day cost shift formula (including division-by-zero guard), channel imputation logic, mocked-DB service integration tests, and REST endpoint validation (empty basket 422, negative quantity 422, response schema completeness).

## [1.6.0] - 2026-09-28

### Added
- **Dynamic, Engaging & High-Density Commodity Card Architecture**:
  - `CommodityCard.jsx`: Replaced legacy flat cards with high-density market intelligence cards featuring category identity pills with Lucide icons, 3.5px left border accents, 7-day visual mini-sparklines, percentage change delta tags (`↑ +13.4%` / `↓ -4.2%` / `→ 0.0%`), observed range metrics (`৳min – ৳max`), channel split bar (`Wholesale • Retail • Online`), and provenance indicators (`● X Sources | Y% Conf`).
  - `MiniSparkline.jsx`: Zero-layout-shift SVG cubic-bezier sparkline with dynamic stroke color coding (Rose for surges $> +2\%$, Emerald for decreases $< -2\%$, Slate for neutral), vertical gradient underlay, and terminal glow node.
  - Category Visual Identity (`frontend/src/utils/categoryTheme.js`): Systematic color-coded border accents, background badges, and category iconography (`Vegetables`, `Grains & Pulses`, `Meat & Fish`, `Dairy & Eggs`, `Spices & Oils`).
  - Refined Multi-Factor Severity Classification: Five-state status indicators (`Critical Spike`, `Elevated`, `Price Drop`, `Volatile`, `Stable`) driven by Z-score, 7-day delta percentage, and 14-day coefficient of variation.
  - "Top Market Mover" Dynamic Hero Layout: Prominent double-span Hero Card dynamically highlighting the market basket's primary price mover at the top of the grid with anomaly explanations, expanded sparkline, and direct inspection workflows.
- **Backend Realtime Pulse API & Serialization Enrichment**:
  - Enriched `DailyPulseItem` schema in `app/schemas/search.py` with `sparkline_7d`, `percentage_change_7d`, `min_price`, `max_price`, `wholesale_avg`, `retail_avg`, `online_avg`, `source_count`, `confidence_score`, `volatility_cv`, and `z_score`.
  - Optimized batched SQL history trail aggregation in `RealtimeService.get_today_pulse()` executing single-pass multi-commodity window calculations with sub-30ms API latency.

## [1.5.0] - 2026-09-28

### Added
- **National 64-District Administrative Spatial Engine & Arbitrage Analytics**:
  - Expanded `data/taxonomy/locations.json` to cover all 8 Divisions (Dhaka, Chittagong, Rajshahi, Khulna, Barisal, Sylhet, Rangpur, Mymensingh), 64 Districts, and 78 primary wholesale and retail markets (e.g., Karwan Bazar, Khatunganj, Raja Bazar Bogura, City Bazar Rangpur, Boro Bazar Jashore).
  - High-resolution administrative district centroids in `data/geo/bangladesh_districts_simplified.json`.
  - Implemented the Spatial Price Dispersion Index $D(t) = \frac{1}{\bar{P}} \sqrt{\frac{1}{N}\sum_{i=1}^N (P_i(t) - \bar{P}(t))^2}$ in `SpatialService`.
  - Freight & Transport Arbitrage Estimator calculating price differentials between agricultural production hubs and metropolitan consumption centers with great-circle Haversine distance scaled by a 1.25 road circuity factor and calibrated carrier overhead $C_{\text{freight}} = 1.50 + 0.018 \cdot d\text{ BDT/kg}$.
  - Added REST endpoint `GET /api/v1/locations/arbitrage?commodity_id={id}` returning sorted inter-district corridors with feasibility ratings.
- **Autonomous Harvester Suite (TCB, Newspapers & Adaptive Jitter)**:
  - `TCBDailyCollector` (`app/collectors/tcb_collector.py`): Ingests Trading Corporation of Bangladesh daily price bulletins with Bengali numeral regex parser (`১-৯`), retail ranges, and offline fixture fallback (`data/fixtures/tcb_sample_bulletin.html`).
  - `NewsMarketCollector` (`app/collectors/news_collector.py`): Deterministic regex extractor parsing Bengali and English newspaper market roundups (Prothom Alo, Daily Star), location mentions, unit sanitization, and confidence dampening ($S_{\text{src}} = 0.70$).
  - Adaptive request jitter and anti-throttling cache proxies with source health telemetry integration in `SourceHealthService`.
- **Viva Defense Live Simulation Sandbox (Frontend & REST API)**:
  - Simulation REST endpoint `POST /api/v1/simulation/inject-shock` supporting dynamic supply disruptions, tariff hikes, and transport strikes with on-the-fly SMA, Z-score, and plain-language explanation generation without ground-truth database corruption.
  - Interactive React component `SimulationSandbox.jsx` ("Viva Simulator" tab) featuring scenario presets, real-time sliders (Shock %, Duration, Baseline drift, Volatility noise), Recharts dynamic curve comparison, and instant explainable justification callouts.
  - Enhanced Leaflet map in `BangladeshPriceMap.jsx` with 64-district choropleth shading, distance from capital indicators, and spatial arbitrage corridor breakdown.
- **Native Android Client Room Database & Custom Canvas Production Engine**:
  - Configured Room persistence in `android/app/build.gradle.kts` with `CommodityEntity`, `PriceObservationEntity`, `AnomalyEntity`, DAOs, and singleton `PricePulseDatabase`.
  - Implemented `OfflinePriceRepository.kt` providing reactive `Flow` queries and offline caching.
  - Custom Canvas-drawn interactive time-series chart in `PriceChartView.kt`: cubic bezier price curve, dashed 14-day rolling SMA baseline, glowing anomaly markers, and touch/drag crosshair tooltip.
- **Academic Thesis Vector Pipeline**:
  - Vector SVG diagrams in `report/figures/`: `system_architecture.svg`, `anomaly_pipeline.svg`, `spatial_arbitrage.svg`.
  - Updated Chapter 5 (64-District spatial dispersion and freight arbitrage) and Chapter 6 (harvester accuracy, Android Room/Canvas benchmarks).
  - Automated report synthesizer producing `report/PricePulse_BD_Thesis.pdf`.
  - Automated test suite expanded to **176 tests** passing with 100% success rate (0 failures).

## [1.4.0] - 2026-09-28

### Added
- **Full Market Basket Taxonomy Expansion (21 Canonical Commodities)**:
  - Added 10 high-value proteins, dairy, fish, and staple commodities to `data/taxonomy/commodities.json`:
    1. **Beef (Local with Bone)** [`গরুর মাংস (হাড়সহ)`] — base unit: kg
    2. **Mutton / Goat Meat** [`খাসির মাংস`] — base unit: kg
    3. **Rui Fish (Fresh 1-2 kg)** [`রুই মাছ`] — base unit: kg
    4. **Pangas Fish** [`পাঙ্গাস মাছ`] — base unit: kg
    5. **Hilsa Fish (Medium ~800g-1kg)** [`ইলিশ মাছ`] — base unit: kg
    6. **Pasteurized Cow Milk** [`তরল দুধ (প্যাকেটজাত)`] — base unit: liter
    7. **Green Chilli** [`কাঁচা মরিচ`] — base unit: kg
    8. **Sugar (Refined White)** [`চিনি (সাদা)`] — base unit: kg
    9. **Salt (Iodized)** [`লবণ (আয়োডিনযুক্ত)`] — base unit: kg
    10. **Mustard Oil** [`সরিষার তেল`] — base unit: liter
  - Support for customary Bengali packaging units: `২৫০ গ্রাম`, `আধা কেজি`, `১ পোয়া` (250g), `১ কেজি`, `হালি`, `মণ`, `সের`.
  - Non-destructive DB schema migration in `scripts/init_db.py` and 30-day realistic trajectory synthesis in `scripts/generate_demo_history.py`.
- **Automated Daily Ingestion & Scheduler Hardening**:
  - `BackgroundSyncScheduler` enhanced with lifecycle management (`list_jobs()`, `stop()`).
  - Standalone daily synchronization CLI utility `scripts/sync_daily_prices.py` for automated headless cron jobs.
  - Resilient collector fallback handling upstream network failures and throttles.
- **100% Interactive Web UI Polish (`frontend/`)**:
  - `MarketTicker.jsx`: Horizontal scrolling marquee ticker bar with live pulse indicator, price movements (`↑`, `↓`, `=`), and click-to-inspect navigation.
  - `CategoryFilter.jsx`: Dynamic category tabs ("All Items", "Grains & Pulses", "Vegetables", "Meat & Fish", "Dairy & Eggs", "Spices & Oils") with badge counters.
  - `ExportDataModal.jsx`: Client-side dataset exporter supporting UTF-8 BOM CSV and formatted JSON formats for active pulse and commodity histories.
  - Enhanced Anomaly Alert cards with quick inspection links.
- **Commercial-Grade Material 3 Android App (`android/`)**:
  - Refined theme tokens (`Color.kt`, `Theme.kt`) featuring Deep Emerald (`#059669`), Dark Slate (`#0F172A`), Amber (`#F59E0B`), and Rose (`#E11D48`).
  - `MarketTickerBar.kt`: Horizontal scrolling live price marquee with animated pulsing status indicator.
  - `HomeScreen.kt`: Real-time telemetry chip (`Live Engine API` vs `Offline Cache`), metric summary cards, category filter chips, and debounced search.
  - `CommodityDetailScreen.kt`: Channel spread breakdown card (Wholesale vs Physical Retail vs E-Commerce) and lightweight Canvas baseline curve.
  - `FieldReportScreen.kt`: Instant interactive metric unit conversion preview card (`হালি` -> `pc`, `২৫০ গ্রাম` -> `kg`, `মণ` -> `kg`).
  - Graceful offline fallback: Displays cached observations with a prominent banner when backend is unreachable.
- **Test Suite & Benchmark Verification**:
  - Test suite expanded to 152 automated tests (`tests/test_expanded_basket.py`, `tests/test_daily_sync.py`) passing with 100% success rate.
  - Benchmark runner script wrapper `scripts/run_all_benchmarks.py`.

## [1.2.0] - 2026-09-28

### Added
- **Resilient Live Web Harvesting Engine**:
  - `DAMLiveCollector` (`app/collectors/dam_live_collector.py`): Real-time HTTP harvesting of official Department of Agricultural Marketing (DAM) daily bulletins with automatic, zero-downtime fallback to verified cached HTML fixtures upon network timeout, DNS failure, or HTTP 5xx responses.
  - `ChaldalLiveCollector` (`app/collectors/chaldal_live_collector.py`): Live retail catalog harvester featuring retry logic with exponential backoff and seamless fallback to verified cached JSON fixtures during network failures or HTTP 429 rate limits.
- **Upstream Provider Source Health Telemetry**:
  - `SourceHealthService` (`app/services/source_health.py`): Real-time telemetry tracker recording operational health (`HEALTHY`, `DEGRADED`, `OFFLINE`), millisecond response latency, sync timestamps, error/success counts, and fallback activation indicators across all registered data providers.
- **In-Process Async Background Scheduler & Sync Layer**:
  - `BackgroundSyncScheduler` (`app/services/scheduler.py`): Asyncio background scheduler running periodic harvests without external cron dependencies. Provides non-blocking execution of on-demand sync tasks with tracking IDs.
  - System REST endpoints:
    - `GET /api/v1/system/sources`: Returns health telemetry and latency metrics for all providers.
    - `POST /api/v1/system/sync`: Triggers asynchronous background ingestion and immediately returns task tracking ID.
    - `GET /api/v1/system/sync/{task_id}`: Real-time progress and completion polling endpoint.
    - `GET /api/v1/system/sync`: Lists all recorded background sync task executions.
  - FastAPI `lifespan` handler integration in `app/main.py` ensuring graceful scheduler startup and termination.
- **Frontend Source Health Dashboard & Live Sync Controls**:
  - `SourceHealthCard.jsx`: Telemetry monitoring cards displaying live connection badges, response latencies, and last updated timestamps for DAM, Chaldal, and Field Spot Submissions.
  - Dynamic "Sync Live Data" trigger button in `Navbar.jsx` with an active spinning animation and non-intrusive status toast alerts.
  - Dedicated "Source Health" tab in `App.jsx` providing architecture explanations and on-demand live re-harvest actions.
- **Resilience Test Suite**:
  - `tests/test_resilient_collectors.py`: Validates network timeouts, connection errors, HTTP 500, and HTTP 429 mocked conditions, confirming seamless fallback to local fixtures without raising unhandled exceptions.
  - `tests/test_source_health.py`: Validates telemetry state transitions and verifies the complete `/api/v1/system/` endpoint contract, expanding the test suite to 84 passing tests.

## [1.1.0] - 2026-09-28

### Added
- **Essential Protein & Pulse Taxonomy Expansion**:
  - Expanded canonical taxonomy with 4 core daily staples: **Broiler Chicken** (`ব্রয়লার মুরগি` - kg), **Farm Egg** (`ফার্মের ডিম` - pc), **Masur Dal (Medium)** (`মসুর ডাল (মাঝারি)` - kg), and **Garlic (Local)** (`দেশি রসুন` - kg).
  - Enriched bilingual alias mappings covering phonetic variants and regional culinary expressions.
  - Enhanced unit normalizer supporting customary discrete units (`হালি` -> 4 pcs, `ডজন` -> 12 pcs), fractions (`1/2 dozen`, `হাফ ডজন` -> 6 pcs), and Bengali numerals (`১ হালি`, `২ হালি`).
- **Human-in-the-Loop Spot Price Ingestion API**:
  - `POST /api/v1/observations/manual`: endpoint accepting authenticated field market reports with Pydantic validation (`price > 0`, valid commodity and market keys).
  - Dynamic unit standardization translating customary trading units to SI metric equivalents.
  - Calibrated Tier 4 confidence scoring applying a 0.60 publisher reliability scalar to prevent outlier poisoning until peer corroborated.
  - Idempotent record persistence updating same-day quotes or logging new price observation records.
- **Interactive Multi-Commodity Comparison Matrix**:
  - Dedicated **Compare Markets** view (`ComparisonView.jsx`) enabling side-by-side comparative analysis of up to 3 commodities.
  - Side-by-side metric comparison across retail vs wholesale price spreads, 14-day SMA baselines, percentage deltas ($\Delta\%$), volatility indices (CV%), and anomaly classifications.
  - District-level spatial filtering for comparative inter-regional arbitrage analysis.
  - Backend analytical endpoint `GET /api/v1/commodities/compare` powering sub-25ms matrix computations.
- **Manual Price Reporting Modal**:
  - Interactive modal dialog (`ManualIngestionModal.jsx`) triggered via the `+ Report Price` button in the navigation header.
  - Live unit conversion preview estimating standardized price per base unit in real-time.
- **Automated Verification Suite**:
  - Added `tests/test_manual_ingestion.py` verifying validation rules, persistence, and confidence calculation.
  - Added `tests/test_expanded_taxonomy.py` testing customary unit conversions and bilingual entity resolution (expanding test suite from 47 to 70 passing tests).

## [1.0.0] - 2026-09-28

### Added
- **Academic LaTeX Research Thesis (`report/`)**:
  - Full university final-year undergraduate thesis entitled *"PricePulse BD: A Location-Aware Multi-Source Market Price Intelligence and Anomaly Detection System for Essential Commodities in Bangladesh"*.
  - Compilable, modular LaTeX structure with `main.tex`, front matter (declaration, abstract, acknowledgments, table of contents), and comprehensive BibTeX references (`references.bib`).
  - Seven exhaustive technical chapters:
    - *Chapter 1: Introduction* (Macro context, commodity volatility in Bangladesh, research objectives).
    - *Chapter 2: Literature Review* (Agricultural MIS, multi-source data fusion, schema matching, parametric vs deep learning anomaly detection).
    - *Chapter 3: System Architecture* (Decoupled local-first design, SQLite WAL concurrency, FastAPI REST gateway, Android decoupling contracts).
    - *Chapter 4: Bilingual Normalization and Data Fusion* (NFKC Unicode normalization, alias resolution cascade, customary unit standardization formulas, 4-factor linear confidence formulation).
    - *Chapter 5: Statistical Anomaly Detection and Spatial Analytics* (14-day rolling SMA, sample standard deviation, Z-score, volatility CV%, compound decision rule, deterministic natural language generator, and spatial inter-district markups).
    - *Chapter 6: Experimental Evaluation and Results* (Bilingual normalization precision/recall benchmarks, 30-day onion supply-shock case study, REST latency profiling with P95 < 45ms, and 47-test pytest verification).
    - *Chapter 7: Conclusion and Future Work* (Summary of contributions, acknowledged boundaries, and Android Kotlin native client roadmap).
- **Viva Defense Master Kit (`docs/`)**:
  - `docs/VIVA_DEFENSE_GUIDE.md`: Comprehensive defense playbook addressing core committee questions, including Computer Science contributions, mathematical justification of parametric statistics over deep learning, confidence scoring mechanics, web harvesting ethics, and Android architecture.
  - `docs/DEMO_SCRIPT.md`: Step-by-step 5-to-7-minute deterministic live demonstration script for the defense board spanning all 5 views, bilingual search, anomaly drilldown, and offline resilience.
- **Unified System Orchestrator & Launcher (`run_system.py`)**:
  - Single-command launcher providing environment checks, automated taxonomy seeding, 30-day demo history verification, and single-port unified serving of both backend REST API and React frontend on port 8000.
  - Command-line flags for self-test verification (`--test`), static serving toggles (`--no-frontend`), port/host configuration, and demo history regeneration (`--seed-history`).

## [0.4.0] - 2026-09-28

### Added
- **Modern Interactive Web Client (React 18 + Vite + Tailwind CSS)**:
  - Production-grade frontend application created in `frontend/` powered by Vite 5 and responsive Tailwind CSS layout.
  - Vite reverse proxy routing `/api` directly to local FastAPI server (`http://127.0.0.1:8000`).
  - Five core dashboard views:
    - **Market Pulse**: Real-time market metrics, KPI summary cards (monitored items, active anomalies, retail spread, market health), channel comparison (wholesale vs physical retail vs online grocery), and daily staple overview.
    - **Commodity Explorer**: Interactive Recharts time-series visualization rendering 30-day price trends against a 14-day Rolling Simple Moving Average (SMA) baseline, with anomaly point callouts and statistical summary metrics.
    - **Anomaly Monitor**: Live anomaly alert stream with severity classification (`Critical`, `Severe`, `Moderate`), Z-score and percentage departure badges, and plain-language natural language explanations.
    - **Bangladesh Price Map**: Interactive Leaflet geospatial map rendering district-level price observations on OpenStreetMap tiles with dynamic price markers, cheapest vs highest market callouts, and hover tooltips.
    - **Data Provenance Drawer**: Detailed audit panel breaking down raw collected values, normalized canonical prices, publisher authority tiers, and confidence score decomposition.
  - Realtime search component supporting bilingual English and Bengali queries with instant price quotes and freshness badges.
- **Frontend Architecture & API Client**:
  - Modular Axios client with standardized timeout and error handling.
  - Service endpoints module wrapping backend REST APIs for commodities, pulse, realtime queries, anomalies, and geo-spread.


### Added
- **Explainable Statistical Anomaly Detection Engine**:
  - `AnomalyEngine` computing Rolling Simple Moving Averages (7, 14, 30 days), sample standard deviation ($\sigma$), Z-score, and Volatility Coefficient of Variation (CV%).
  - Compound Anomaly Decision Rule ($|Z| \ge 1.5$ AND $|\Delta\%| \ge 10.0\%$) with granular severity tiers (`Moderate`, `Severe`, `Critical`) and directional classification (`Spike` vs `Drop`).
  - Rule-based Natural Language Explanation Generator delivering auditable justifications.
- **Spatial Market Spread & GeoJSON Intelligence**:
  - `SpatialService` calculating inter-district spatial dispersion, identifying cheapest vs most expensive market nodes, and computing geographical markup percentages.
  - Simplified Bangladesh district GeoJSON dataset (`data/geo/bangladesh_districts_simplified.json`) enriched dynamically with live market prices for Leaflet map visualization.
  - Complete administrative location hierarchy endpoint (`/api/v1/locations/hierarchy`).
- **REST API Endpoints**:
  - `GET /api/v1/anomalies/active`: scans all registered commodities for active price anomalies.
  - `GET /api/v1/anomalies/{commodity_id}/explain`: in-depth statistical decomposition and natural language breakdown for a specific commodity.
  - `GET /api/v1/locations/spread?commodity_id={id}`: inter-district spatial spread and enriched GeoJSON feature collection.
- **Offline Viva Defense Seed Generator**:
  - `scripts/generate_demo_history.py`: populates 30 days of continuous market observations across four core staples, embedding a calibrated 5-day supply shock on Onion to demonstrate live anomaly detection.
- **Documentation**:
  - Mathematical formulation document (`docs/ALGORITHMS.md`) covering SMA, Standard Deviation, Z-score, Volatility CV, Compound Anomaly Rule, and Spatial Spread.
- **Automated Test Suite**:
  - Added unit and integration tests across statistical formulas, anomaly decision matrices, spatial calculations, and REST endpoints (47 passing tests total).

## [0.2.0] - 2026-09-28

### Added
- **Realtime Price Search & On-Demand Ingestion**:
  - `RealtimePriceService` providing automatic collector fallback when observations are absent or cached records exceed 12 hours.
  - Multi-tier freshness markers (`fresh`, `stale`, `realtime_ingested`, `historical`) and cache age metrics.
- **Retail Catalog Collector (Chaldal)**:
  - `ChaldalCollector` and realistic retail fixture (`chaldal_catalog_sample.json`) supporting commercial packet sizes (`1 kg`, `500 gm`, `2 kg`, `5 kg`, `1 liter`, `2 liter`).
  - Multi-SKU package price averaging for retail product varieties.
- **Market Analytics & Spread Engine**:
  - `AnalyticsService` calculating price ranges (`min`, `max`, `avg`), wholesale vs physical retail vs online grocery channel breakdowns, and price pressure classifications (`Normal`, `Elevated`, `High`).
- **REST API Routers & FastAPI Application**:
  - Production FastAPI app factory with CORS middleware, lifespan events, and global RFC 7807 problem details error handling.
  - `GET /api/v1/health` and `/health` system status endpoints.
  - `GET /api/v1/search/realtime` for on-demand price discovery.
  - `GET /api/v1/pulse/today` for macro essential market summaries.
  - `GET /api/v1/commodities`, `/{id}`, and `/{id}/history` for catalog and time-series charting.
- **API Schemas & Android Compatibility**:
  - Pydantic v2 schemas (`app/schemas/`) with strict validation and Retrofit Kotlin client integration contracts.
- **Automated Test Suite**:
  - `tests/test_realtime_service.py` verifying on-demand ingestion triggers, cache hits, and analytics calculations.
  - `tests/test_api_endpoints.py` verifying all REST API endpoints using FastAPI `TestClient`.

## [0.1.0] - 2026-09-28

### Added
- **Core Architecture & Schema**:
  - Relational schema definitions in SQLAlchemy 2.0 covering `Commodity`, `CommodityAlias`, `Division`, `District`, `Market`, `Source`, and `PriceObservation`.
  - SQLite configuration with Write-Ahead Logging (WAL) pragmas, synchronous normal mode, and foreign key enforcement.
- **Bilingual Normalization Engine**:
  - Alias matching pipeline supporting Unicode Bengali and Latin script variations.
  - Multi-tiered unit standardizer converting regional units (maund, seer, hali, quintal) into SI metrics (`kg`, `liter`, `pc`).
- **Confidence Scoring System**:
  - Weighted linear confidence model incorporating publisher authority, alias match precision, temporal freshness, and price completeness.
- **Fixture Collectors & Pipeline Slice**:
  - `BaseCollector` abstract interface defining ingestion contracts.
  - `DAMFixtureCollector` deterministic parser extracting retail and wholesale commodity quotes from official Department of Agricultural Marketing (DAM) market bulletins.
  - End-to-end `IngestionPipeline` orchestrating extraction, normalization, deduplication, confidence assignment, and persistence.
- **Taxonomy Seeds**:
  - Canonical taxonomy for daily staple commodities (`Rice`, `Onion`, `Potato`, `Soybean Oil`) with comprehensive Bengali and English aliases.
  - Hierarchical administrative and market spatial seed data for Dhaka and Chittagong divisions.
- **Documentation**:
  - System architecture specification (`docs/ARCHITECTURE.md`).
  - Relational schema and confidence formulation (`docs/DATA_MODEL.md`).
  - Normalization rules and bilingual dictionary (`docs/NORMALIZATION.md`).
  - REST API contracts for Web and Android clients (`docs/API_SPEC.md`).
- **Test Suite**:
  - Automated unit tests for unit conversion and alias resolution (`tests/test_normalization.py`).
  - End-to-end integration tests verifying database ingestion and observation counts (`tests/test_ingestion.py`).
