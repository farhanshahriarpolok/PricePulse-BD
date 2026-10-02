# TASKS.md — Active Execution Queue

This file tracks the active development tasks for **PricePulse BD**. Only items under `## NOW` are currently in progress.

---

## NOW

- Phase 6B — API Security Safeguards (Admin API Key Authentication) completed and verified locally. Ready for audit review.

---

## NEXT

- Phase 6C — Automated Backup Restore Drill & Verification Automation.
- Phase 6D — Remote GitHub Synchronization.
- Phase 6E — Linux VPS Cloud Host Provisioning & Nginx SSL Deployment.

---

## BLOCKED
- None.

---

## DONE RECENTLY

- **Phase 6B — API Security Safeguards (Admin API Key Authentication)** (2026-10-02):
  - **Reusable Security Dependency**: Implemented `require_admin_api_key` dependency (`app/core/security.py`) enforcing `X-API-Key` HTTP header authentication with timing-safe comparison (`secrets.compare_digest()`).
  - **Protected Mutation Endpoints**: Secured `POST /api/v1/observations/manual` and `POST /api/v1/system/sync`.
  - **Fail-Closed Default**: Configured dynamic settings property `admin_api_key` reading `PRICEPULSE_ADMIN_API_KEY`. Rejects all mutation attempts with HTTP 401 when unset or empty.
  - **Zero Leakage**: Guaranteed no secret emission in error envelopes, OpenAPI specs, URL params, logs, or frontend code.
  - **Public Endpoints Untouched**: `GET /health`, `GET /api/v1/system/sources`, `POST /api/v1/simulation/inject-shock`, `GET /api/v1/commodities`, etc., remain public and accessible without authentication.
  - **Verification**: 17/17 Phase 6B tests passing, 430/430 full backend regression tests passing, clean Vite build, 6/6 production smoke tests passing.

- **Phase 6A — Container & Process Model Hardening** (2026-10-02):
  - **Single-Worker Process Model**: Configured Uvicorn runner to `--workers 1` in `Dockerfile`, eliminating duplicate in-process background sync schedulers across forked processes.
  - **Non-Root Container Runtime**: Hardened runtime container to run as dedicated unprivileged service user (`pricepulse`, UID/GID 1000) with explicit directory permissions.
  - **Persistent Hot Backup Storage**: Defaulted container backup destination to `/app/data/backups/`, ensuring snapshots share the persistent `pricepulse_data` volume across container recreation.
  - **Localhost-Only Port Binding**: Restricted container port exposure in `docker-compose.yml` to `127.0.0.1:8000:8000` to prevent direct public access bypassing Nginx.
  - **Verification**: 413/413 tests passing 100% green, clean Vite build, 6/6 production smoke tests passing.


- **Phase 5D — Observability, Health Telemetry & Automated Operational Safeguards** (2026-10-02):
  - **Persistent Source Health Telemetry (5D.1)**:
    - Added `source_health_logs` table with `UNIQUE(source_name, date)` constraint.
    - Implemented deterministic daily health aggregation: `availability = (successful / total) * 100`.
    - Unskewed latency: failed/timeout attempts strictly excluded from latency averages.
    - Enriched `GET /api/v1/system/sources` with trailing 7-day rolling metrics (`rolling_7d_availability`, `rolling_7d_avg_latency_ms`) while maintaining 100% backward compatibility with legacy consumers. Missing observation days handled safely without treating unharvested dates as failures.
  - **Safe SQLite Online Hot Backup (5D.2)**:
    - Created `scripts/backup_db.py` utilizing Python's native SQLite Online Backup API (`sqlite3.Connection.backup`).
    - Validates snapshots via `PRAGMA integrity_check; -> 'ok'` and schema verification of canonical tables before atomic promotion (`.tmp` -> `.db`).
    - Enforces configurable retention pruning (`--retention-count`, default: 7 snapshots).
    - Preserves last-known good backup on candidate verification failure and exits with non-zero status.
  - **Nginx Simulation Rate Limiting (5D.3)**:
    - Configured `nginx/nginx.conf` with `limit_req_zone` targeting `/api/v1/simulation/inject-shock` at `5r/s` with `burst=10 nodelay`, returning HTTP 429 upon exhaustion.
    - Preserved unthrottled pass-through for general market discovery routes and React SPA assets.
    - Updated `DEPLOYMENT.md` with complete backup, rate limiting, and telemetry operational guides.
  - **Verification**:
    - **410/410 Pytest tests passing 100% green** across all 32 test suites.
    - Clean production Vite build (0 errors, 0 warnings).
    - All 6/6 production smoke tests passing.

- **Phase 5C — Supply-Chain Price Gap & Arath Commission Deconstruction** (2026-10-02):
  - **Strict Provenance Hierarchy**:
    - Categorized price metrics into `OBSERVED` (empirical wholesale and retail prices, road distances), `OFFICIAL` (statutory bridge toll gazettes), and `MODELED_ASSUMPTION` (arath commission, terminal handling, transit wastage).
    - Refused unsupported statutory claims; modeled arath commission (3.0%) and perishability wastage (0.5% - 6.0%) transparently tagged with academic citations (Minten et al., World Bank, BARC).
  - **Unclamped Economic Formulation**:
    - Implemented `residual_spread = gross_spread - observed_costs - modeled_costs` without clamping to zero.
    - Gracefully surfaces `COMPRESSED_MARGIN` with negative residual and exact compression deficit (`margin_compression_bdt`) when intermediary modeled costs exceed observed price spread.
  - **Backend Engine & API**:
    - Created `SupplyChainService` (`app/services/supply_chain_service.py`) and schemas (`app/schemas/supply_chain.py`).
    - Exposed `GET /api/v1/commodities/{id}/supply-chain` with district and temporal filters.
  - **Consumer-First Hybrid UI**:
    - Built `SupplyChainMarginPanel.jsx` mounted within `CommodityDetailExplorer.jsx`.
    - Features observed price blocks, modeled cost breakdown cards, residual spread banner, and an expandable audit accordion drill-down table.
    - Fully localized in Bengali and English via `translations.js`.
  - **Verification**:
    - **388/388 Pytest tests 100% green** (374 baseline + 14 Phase 5C tests).
    - Production Vite build passing in 4.64s (0 errors, 0 warnings).
    - Browser QA verified on desktop (1440px) and mobile (390px) with 0 console errors and 0 horizontal overflow.


- **Phase 5B — Smart Cheaper Alternative Recommendations (Hardened & Audited)** (2026-10-02):
  - **Empirical Intra-Category Substitution Registry**:
    - Created `data/taxonomy/alternative_registry.json` establishing 17 active verified pairwise substitution relationships strictly within the same food categories (Grains, Edible Oils, Vegetables, Pulses, Meat & Poultry, Fish & Seafood, Eggs & Dairy).
    - Fully deactivated and documented 3 unit-incompatible upstream pairs (`Hilsa pc -> Rui kg`, `Spinach bundle -> Red Spinach pc`, `Malabar Spinach bundle -> Red Spinach pc`) until authoritative unit-to-weight standards are canonized.
  - **Strict Temporal Alignment & Provenance Rules**:
    - Enforced mandatory qualification criteria: absolute savings $\ge ৳2.00/\text{unit}$ **AND** percentage savings $\ge 5.0\%$.
    - Implemented strict backend observation divergence gate: comparisons with temporal divergence $> 1$ calendar day are strictly rejected.
    - Excluded modeled, imputed, or synthetic benchmarks (`PANDAMART_MODELED`, `modeled_benchmark`), relying strictly on empirical channel price observations.
    - Enriched `PriceAlternativeOut` with dual-sided observation metadata (`source_observation_date`, `source_freshness_tier`, `alternative_observation_date`, `alternative_freshness_tier`, `is_symmetric_freshness`).
  - **Frontend UI & Interactive Replacement**:
    - Enhanced `BazaarBasketView.jsx` with an optional, non-intrusive alternative card rendering dual-sided freshness badges, unit savings, line savings, and neutral explanation.
    - Added user-driven `[Use this instead]` / `[এই বিকল্পটি ব্যবহার করুন]` button that updates the specific basket line item and recalculates totals without mutating unrelated items or silently auto-substituting.
    - Added bilingual translations in `translations.js`.
  - **Verification**:
    - **374/374 Pytest tests passing 100% green** across all 29 test suites.
    - Production Vite build passing in 16.28s (0 errors, 0 warnings).
    - Zero DB schema migrations; zero Android modifications.

- **Phase 5A — Observation Freshness & Stale Data Safeguards** (2026-10-02):
  - **Freshness vs Provenance Decoupling**:
    - Disentangled temporal age (`freshness_tier`: `FRESH_TODAY`, `YESTERDAY`, `STALE`, `freshness_age_hours`) from source provenance (`LIVE`, `FALLBACK`, `MODELED`, `UNAVAILABLE`).
    - Standardized Bangladesh Standard Time (BST UTC+6) calendar boundaries across observation lifecycles without requiring schema mutations.
  - **Ingestion & Fallback Safeguards**:
    - Ensured older fallback data and fixtures cannot overwrite newer live observations (`raw.is_fallback` records never overwrite existing observations).
    - Fixed fixture date handling in `DAMLiveCollector`: fallback fixture parser extracts the authentic date from bulletin metadata (`data-date="2026-09-27"`) instead of falsely synthesizing target dates.
  - **API Contract & Realtime Enrichment**:
    - Enriched `FreshnessMetadata` with `freshness_tier` (`FRESH_TODAY`, `YESTERDAY`, `STALE`) and `freshness_age_hours`.
    - Added `observation_date` to `DailyPulseItem` and `freshness_tier`/`freshness_age_hours` to `StorePriceOut`.
    - In `RealtimePriceService.get_today_pulse()`, commodities lacking today's observations discover the latest available observation date and accurately reflect their tier (`YESTERDAY` or `STALE`), preventing data disappearance.
  - **Frontend UI & Localization**:
    - Updated `CommodityCard.jsx` to render deterministic, non-alarmist freshness indicators:
      - `FRESH_TODAY`: Emerald dot with subtle pulse + `আজকের দর` / `Today's Price`.
      - `YESTERDAY`: Sky blue steady dot + `গতকালের দর` / `Yesterday's Price`.
      - `STALE`: Amber steady dot + `পুরনো বাজারদর` / `Older Price` (or formatted date).
    - Preserved distinct source provenance badges (`DAM / TCB ভেরিফাইড`).
    - Added bilingual keys (`freshness_today`, `freshness_yesterday`, `freshness_stale`) to `translations.js`.
  - **Verification**:
    - **355/355 Pytest tests 100% green** (343 baseline + 12 new Phase 5A freshness tests).
    - Production Vite build passing (394.28 kB JS / 117.75 kB gzip, 0 errors).
    - Playwright QA verified on desktop (1440px) and mobile (390px) viewports with zero horizontal overflow and zero console errors.

- **Phase 4B — Data Freshness & Cache Correctness Audit** (2026-10-01):
  - **Freshness Audit & Bug Discovery**:
    - Traced execution flows across `ForecastService`, `SpatialService`, `IngestionPipeline`, `scheduler.py`, and `observations.py`.
    - Proved via empirical lifecycle tests (`test_phase4b_lifecycle_freshness.py`) that under pure TTL caching, newly ingested price observations (from background harvests or manual spot reports) left downstream forecast and spatial opportunity caches stale for up to 3600s.
  - **Minimal Correctness Hardening (Strategy A)**:
    - Added granular `invalidate(commodity_id: Optional[int], channel: Optional[str])` to `ForecastService`.
    - Added granular `invalidate(commodity_id: Optional[int])` to `SpatialService`.
    - Updated `SpatialService.get_consumer_opportunity` to compute `eff_date` before building `cache_key`, preventing stale `(comm.id, None)` collisions across dates.
    - Wired event-driven invalidation hooks into `IngestionPipeline.run_collector`, `ingest_observations`, and `submit_manual_observation`: newly inserted or updated observations immediately evict only the affected commodities, leaving unaffected staples warm in cache.
  - **Verification**:
    - **343/343 Pytest tests 100% green** (331 baseline + 8 caching + 4 lifecycle freshness).
    - Production Vite build passing (392.92 kB JS / 117.37 kB gzip, 0 chunk warnings).
    - Production smoke test 6/6 passing.
    - Android client directory 100% untouched.

- **Phase 4 — Controlled Hardening, Performance Caching, Bundle Optimization & Viva Readiness** (2026-10-01):
  - **P1 — Documentation Alignment**:
    - Audited `app/services/forecast_service.py` vs `BRAIN.md`. Aligned documentation to reflect the actual production formulas:
      - Estimated parametric uncertainty range: $\sigma_h = \text{RMSE}_{\text{OOS}} \cdot \sqrt{1.0 + 0.10(h-1)}$, with bounds $[\max(0, \hat{P}_h - 1.96\sigma_h), \hat{P}_h + 1.96\sigma_h]$.
      - Volatility-aware direction deadband: Base $\pm 3.0\%$; modulated when $CV_{14} > 8.0\%$ by $\min(4.0\%, (CV_{14} - 8.0\%) \times 0.4)$, bounded within $[3.0\%, 7.0\%]$.
    - Clarified terminology: Labeled as "estimated uncertainty range based on out-of-sample RMSE" rather than uncalibrated confidence intervals.
  - **P2 & P3 — In-Memory Performance Caching**:
    - Implemented deterministic bounded TTL cache (`cache_ttl = 3600s`) in `ForecastService` keyed by `(commodity_id, channel, market_id)`.
      - Measured latency dropped from **196.25 ms** to **6.19 ms** (>30x speedup / 96.8% latency reduction).
      - Added cache isolation (channel, market, cross-commodity) and exclusion of incomplete/sparse datasets.
    - Implemented deterministic bounded TTL cache (`cache_ttl = 3600s`) in `SpatialService` keyed by `(commodity_id, date_key)`.
      - Measured latency dropped from **8.49 ms** to **5.70 ms** (33% latency reduction).
    - Added comprehensive cache test suite (`tests/test_phase4_caching.py`, 8 tests).
  - **P4 — Frontend Bundle Optimization & Code Splitting**:
    - Implemented `React.lazy` and `Suspense` for heavy non-landing modules (`BangladeshPriceMap`, `SimulationSandbox`, `ComparisonView`, `CommodityDetailExplorer`, and modal dialogs).
    - Removed unused `HistoricalTrendChart` import from `App.jsx`.
    - **Initial JS bundle size slashed from 1,078.77 kB to 392.90 kB (63.6% reduction)**; initial gzip payload slashed from **302.61 kB to 117.35 kB (61.2% reduction)**.
    - Eliminated all Vite >500 kB build chunk warnings.
  - **P5 & P6 — Viva / Demo Hardening & Documentation Consistency**:
    - Replaced unverified "nationwide" and "64-district" claims in translations and UI with accurate commercial hub and inter-district freight corridor labels.
    - Replaced "95% Interval" table headers with "Uncertainty Range (±1.96σ)" and added empirical out-of-sample RMSE methodology disclosures.
    - Verified all 65 canonical commodities, 7 populated markets, 5 districts with empirical observations, zero SARIMA/deep learning, and modeled-data isolation.
  - **P7 & P8 — Security Recheck & Comprehensive Verification**:
    - All 339 unit and integration tests passing (100% green).
    - Production Vite build passing in 4.53s.
    - Production smoke test 6/6 passing.
    - Android client directory 100% untouched.

- **Phase 3 — Forecasting, Direction Signals, Backtesting & Research Analytics** (2026-10-01):
  - **Backend Forecasting Engine**:
    - Built production `ForecastService` (`app/services/forecast_service.py`) supporting hybrid candidate models: Naive persistence, SMA-7, SMA-14, and formal non-seasonal ARIMA(1,1,0) with analytical OLS AR(1) fallback.
    - Implemented rolling-origin walk-forward backtesting ($T_{\text{train}} = 14$ days, $H = 7$) strictly guaranteeing zero future data leakage (`train_end < val_start`), evaluating candidate models via out-of-sample MAE and RMSE.
    - Added data eligibility engine strictly excluding `PANDAMART_MODELED` records and sparse commodities ($< 14$ continuous dates return `INSUFFICIENT_DATA` rather than fabricated predictions).
    - Integrated channel-separated national series (Wholesale, Retail, Online, Combined) and verified populated market series.
    - Implemented volatility-modulated direction signals (base deadband $\pm 3.0\%$ modulated by 14-day historical CV).
    - Exposed endpoint `GET /api/v1/commodities/{id}/forecast` with full provenance, eligibility reasons, and backtest candidate metrics.
  - **Consumer-First Hybrid UI**:
    - Created `ForecastOutlookPanel.jsx` component featuring dual-tier layout:
      1. *Consumer Tier*: Expected direction badge (সম্ভাব্য বৃদ্ধি/হ্রাস/স্থিতিশীল), projected 7-day price range (`৳X – ৳Y / unit`), point forecast delta, and clear analytical disclaimer.
      2. *Expandable Research Tier*: Candidate models backtest table (NAIVE, SMA-7, SMA-14, ARIMA_1_1_0) with windows evaluated, out-of-sample MAE/RMSE, winning model status, volatility CV, and Day 1..7 daily schedule.
    - Added channel toggle buttons (পাইকারি, খুচরা, অনলাইন) dynamically fetching channel-specific models.
    - Integrated `ForecastOutlookPanel` into `CommodityDetailExplorer.jsx` below `SpatialOpportunityPanel`.
  - **Comprehensive Verification & Zero Regression**:
    - Added 17 unit and integration tests in `tests/test_phase3_forecast.py` covering data eligibility, channel separation, candidate models, leakage prevention, backtest selection, and API contracts.
    - **Verification**: **331/331 Pytest tests 100% green** (up from 314), clean Vite production build (2495 modules transformed, 0 errors, built in 12.89s), all 6/6 production smoke checks passed, Playwright desktop (1440x900) & mobile (390x844) verified with zero horizontal overflow and zero console errors. Android directory 100% untouched.

- **Phase 2 — Spatial Intelligence Implementation (Hybrid UI, Canonical Units & Consumer Opportunity)** (2026-10-01):
  - **Backend Spatial Enhancement**:
    - Added `calculation_unit` and `data_provenance` fields to `ArbitrageRoute` schema (`app/schemas/spatial.py`).
    - Added `FreightBreakdownDetail` and `ConsumerOpportunityResponse` schemas to expose consumer-first spatial arbitrage summaries alongside granular corridor freight breakdowns.
    - Implemented `get_consumer_opportunity()` in `SpatialService` (`app/services/spatial_service.py`), deterministically finding the highest net-opportunity corridor (net margin $\ge 2.0$ BDT/unit) or returning a structured market equilibrium / no-arbitrage response when spreads are unviable.
    - Added `GET /api/v1/locations/consumer-opportunity` endpoint in `app/api/v1/endpoints/locations.py` with 404 handling and query routing.
    - Added `getConsumerOpportunity()` API helper in `frontend/src/api/endpoints.js`.
  - **Consumer-First Hybrid UI**:
    - Created `SpatialOpportunityPanel.jsx` component featuring dual-tier layout:
      1. *Consumer Tier*: Clear visual card showing cheapest origin district vs expensive destination district, transport cost, net savings callout (`+৳X.XX / unit`), and feasibility indicator (or market equilibrium notice when no net corridor exists).
      2. *Expandable Research Tier*: Drill-down view with distance in km, transit hours, base freight breakdown (loading, fuel/distance, toll/ferry), Spatial Dispersion Index $D(t)$, and top corridor rankings table.
    - Integrated `SpatialOpportunityPanel` directly into `CommodityDetailExplorer.jsx` below historical trend charts.
    - Full bilingual Bengali/English localization (`lang` prop aware).
  - **Comprehensive Test Suite & Zero-Regression Verification**:
    - Added 21 unit and integration tests in `tests/test_phase2_spatial_consumer.py` covering schema compliance, canonical units matching `commodity.default_unit`, mathematical consistency of freight components, equilibrium handling, and HTTP endpoint contract.
    - **Verification**: **314/314 Pytest tests 100% green**, clean Vite production build (2494 modules, 0 errors, built in 13.63s), Android directory untouched, zero unverified claims.

- **Phase 1 Final Acceptance & Evidence Gate Passed** (2026-09-30):
  - **DAM Ticker Range Inconsistency Fixed**: Corrected `DAMLiveCollector._parse_html` so intra-day ticker ranges (e.g. 30 - 35 Tk) within a single channel compute an arithmetic mean rather than falsely splitting into `wholesale_avg` and `retail_avg`. Added regression test `test_dam_ticker_range_not_split_wholesale_retail`.
  - **Mobile 390x844 Layout Contained**: Fixed horizontal overflow on 390px mobile viewports by adding `min-w-0` to Navbar search and `overflow-x: hidden` to root HTML/body container.
  - **Complete Evidence Gate**: All 25 acceptance gates verified with runtime evidence (293/293 pytest, fresh isolated SQLite DB, E2E collectors, Store API, scheduler, source health, cultural units, taxonomy safety, PWA, desktop/mobile browser testing).
  - **Verification**: **293/293 Pytest tests 100% green**, clean Vite production build (2493 modules transformed, 0 errors), 6/6 production smoke tests passed.


- **Phase 1 — Real Data Integration Foundation + Data Quality & Validation Hardening** (2026-09-30):
  - Hardened `CommodityNormalizer` with token-boundary constraint: multi-token phrase containment only, single-token aliases restricted to exact match to prevent taxonomy bleed on multi-word branded items.
  - Added all canonical sources (`SHWAPNO_RETAIL`, `MEENA_BAZAR_RETAIL`, `PANDAMART_MODELED`) to `scripts/init_db.py` seed routines, ensuring isolated fresh database deployments have 100% complete source registries.
  - Aligned `SourceHealthService` initial state with real endpoint status (Chaldal marked as fallback due to live 404, Shwapno & Meena Bazar initialized to UNKNOWN prior to harvest).
  - Resolved local variable scoping bug in `commodities.py` store endpoints.
  - Added 33 new regression tests in `tests/test_phase1_regression.py` across taxonomy safety, cultural unit scaling, clean DB initialization, and provenance isolation.
  - Full suite verified: **285/285 tests passed (100% green)**, Vite production build successful.

- **Milestone 025 — Multi-Store Retail Collector Trio, `/commodities/{id}/stores` API & Detail Page Store Panel** (2026-09-30):
  - Added three new retail harvest connectors registered in `app/collectors/__init__.py`:
    - `ShwapnoCollector` (`SHWAPNO_RETAIL`, reliability 0.90): Live network harvest across 4 category APIs (fresh-vegetables, rice, oil, eggs) with explicit taxonomy mapping and fixture fallback.
    - `MeenaBazarCollector` (`MEENA_BAZAR_RETAIL`, reliability 0.89): Live home-section API harvest with explicit commodity mapping, stock/zero-price filtering, and deduplication.
    - `PandamartCollector` (`PANDAMART_MODELED`, reliability 0.75): Transparent modeled benchmark collector documenting the Cloudflare 403 / mobile-app-only access limitation; fixture-backed.
  - Extended `app/collectors/base.py` with `CollectionStatus` enum (`LIVE`, `FALLBACK`, `MODELED`, `STALE`, `UNAVAILABLE`) and `RawObservation` fields (`collection_status`, `source_url`, `raw_package_size`, `error_message`).
  - Added new `GET /api/v1/commodities/{id}/stores` endpoint in `app/api/v1/endpoints/commodities.py` returning live/fallback/modeled prices from Chaldal, Shwapno, Meena Bazar, and Pandamart with transparent status labels (Bengali + English).
  - Added `StorePriceOut` and `CommodityStoresResponse` Pydantic v2 schemas in `app/schemas/commodity.py`.
  - Overhauled `CommodityDetailExplorer.jsx` with a full store price comparison panel: live vs fallback vs modeled badges, BDT price per unit display, direct store links, and Bengali-first status labels.
  - Wired `getCommodityStores()` in `frontend/src/api/endpoints.js`.
  - Added 16 new deterministic tests across `test_meena_bazar_collector.py`, `test_pandamart_collector.py`, and `test_shwapno_collector.py` covering fixture harvest, canonical mapping accuracy, deduplication, network failure fallback, source health telemetry, and IngestionPipeline persistence.
  - Verification: **252/252 Pytest tests 100% green**, clean Vite production build (2493 modules, 0 errors).

- **Milestone 024 — Android SDK Packaging, WhatsApp Bazaar Fard Export & Background Ingestion Hardening** (2026-09-29):
  - Added WhatsApp Bazar Fard export & sharing directly in the active basket section of `BazaarBasketView.jsx`, generating structured, colloquial Bengali shopping lists with line-item totals, total estimated cost, wholesale savings, and local verification link.
  - Implemented interactive Share Modal with 1-click WhatsApp web launch, clipboard copy with visual feedback, and native device sharing.
  - Modernized physical paper and PDF printable fard with `@media print` CSS rules, pen-checkable `[ ]` boxes, dual-language commodity labels, benchmark estimates, and handwritten note columns for physical traditional market shopping.
  - Hardened autonomous background scheduler (`app/services/scheduler.py`) to run on 6-hour interval (`interval_seconds = 21600`) without blocking FastAPI ASGI loop, recording latency, fallback state, and error logs into `SourceHealthService`.
  - Added loop execution support (`--all`, `--loop`, `--interval`) in `scripts/sync_daily_prices.py` and updated `docker-compose.yml` worker container profile to run continuously without container exits.
  - Enhanced `scripts/build_android_apk.py` with automatic Windows Android SDK location discovery (`%LOCALAPPDATA%\Android\Sdk`, `C:\Android\Sdk`, `D:\Android\Sdk`, etc.), `android/local.properties` generation, and Gradle wrapper dry-run assembly check.
  - Verification: 236/236 Pytest test suite 100% green, clean Vite frontend production build (0 errors), and all 6 production smoke tests passing.

- **Milestone 023 — UI/UX Minimal Overhaul, Commodity Card Simplification & Navigation De-cluttering** (2026-09-29):
  - Overhauled `CommodityCard.jsx`: Replaced cluttered developer metrics and tags with consumer-focused visual hierarchy, human-friendly trend badges (`↑ ২.১% বেড়েছে`), bold prices formatted with Bengali numerals, clean 3-channel horizontal comparison strip with cheapest channel highlighting, and intuitive `বিস্তারিত দেখুন →` action link.
  - De-cluttered `Navbar.jsx`: Consolidated from 9 horizontal items to 5 core consumer tabs (`pulse`, `basket`, `compare`, `anomalies`, `map`) and placed technical tools in a clean "অন্যান্য" (More) dropdown. Fixed vertical clipping with enhanced `min-h-[72px]` header height.
  - Repaired blank screens and unwired modals: Fixed market dropdown population in `ManualIngestionModal.jsx` and added robust fallback 30-day historical time-series generation in `App.jsx` so clicking `বিস্তারিত দেখুন →` on any commodity renders full interactive charts immediately.
  - Verified visual quality, zero console errors, and flawless tab switching via Playwright MCP headless audit (`scripts/qa_snapshots/12_simplified_minimal_ui.png`, `13_report_modal_fixed.png`, `14_details_page_chart_fixed.png`).
  - All 236 pytest test suites passing 100% green and clean frontend production build.

- **Milestone 022 — Production Docker Engine, Android Release Build & Deployment Handoff** (2026-09-29):
  - Created multi-stage production `Dockerfile` (Node 20 Alpine frontend builder, Python 3.11 Slim runtime, automated SQLite volume initialization, and curl healthcheck).
  - Authored `docker-compose.yml` with port 8000 mapping, volume mounting for persistent SQLite WAL state, and an optional daily sync worker profile.
  - Added `.dockerignore` for minimal, high-speed container builds.
  - Bumped Android mobile client to `versionCode = 2` and `versionName = "2.3.0"` in `android/app/build.gradle.kts`.
  - Built `scripts/build_android_apk.py` helper for Gradle packaging, artifact detection, SHA-256 calculation, and USB/sideload instructions.
  - Created and executed `scripts/production_smoke_test.py` with 100% pass across all 6 core subsystem checks (Health, Taxonomy, Arbitrage Corridors, 3-Channel Basket, Saved Baskets CRUD, Static React SPA).
  - Authored comprehensive Linux VPS deployment and operations handbook in `DEPLOYMENT.md`.
  - Verified 100% green Pytest test suite (236/236 passing) and clean frontend production build.

- **Milestone 021 — Visual Identity, Custom Vector Assets & Mass-Consumer UI Media Polish** (2026-09-29):
  - Designed and deployed brand identity suite: `frontend/public/logo.svg` (market scale + pulse + leaf motif), `frontend/public/favicon.svg` (pixel-perfect 32x32 SVG), and `frontend/public/og-image.svg` (1200x630 OpenGraph preview banner).
  - Enriched `frontend/index.html` with SVG favicon and standard OpenGraph / Twitter card metadata.
  - Implemented bespoke vector illustration system `frontend/src/components/media/CommodityIcon.jsx` covering all staple categories and individual commodity signatures.
  - Integrated `CommodityIcon` into `CommodityCard.jsx` (hero and standard cards), `CategoryFilter.jsx` (filter chips), and `BazaarBasketView.jsx` (basket line items).
  - Refined `Navbar.jsx` with vector `logo.svg` and live animated pulse dot indicator.
  - Verified visual rendering via Playwright MCP headless audit screenshot (`scripts/qa_snapshots/10_media_polish.png`).
  - Maintained 100% test pass rate across all 236 pytest tests and clean Vite production build.

- **Milestone 020 — Mass-Consumer Localization Overhaul, Bilingual Toggle, Expanded Taxonomy & Browser E2E Audit** (2026-09-29):
  - Fixed white-screen tab crashes: resolved undefined property access in `ChannelComparisonCard.jsx` and `HistoricalTrendChart.jsx` (`.toFixed(2)` on undefined variables), rectified response unnesting in `ComparisonView.jsx`, and wrapped all tabs in React `<ErrorBoundary>`.
  - Implemented bilingual localization dictionary (`frontend/src/i18n/translations.js`) with default natural, colloquial Bangla (`bn`) and added `[বাংলা | EN]` toggle button in `Navbar.jsx` with persistent `localStorage` preference.
  - Replaced academic/statistical jargon with consumer-friendly wording across all views (e.g. "আজকের নিত্যপণ্যের বাজারদর", "বাজার বাস্কেট", "দাম বৃদ্ধি সতর্কতা", "জেলাভিত্তিক ম্যাপ", "মার্কেট সিমুলেটর").
  - Expanded national essential staples taxonomy (`data/taxonomy/commodities.json`) from 21 to 35 commodities (adding ginger, eggplant, tomato, papaya, cucumber, carrot, atta, maida, fine masur dal, deshi chicken, tilapia, loose oil, dry red chilli, turmeric powder) with grounded historical market baselines.
  - Performed comprehensive headless Playwright MCP E2E audit navigating through all 9 tabs (`pulse`, `basket`, `compare`, `explorer`, `anomalies`, `simulator`, `map`, `sources`, `provenance`), asserting 0 console errors/exceptions, and archiving verified visual snapshots in `scripts/qa_snapshots/`.
  - Maintained 100% test pass rate across all 236 pytest tests.
  - Updated academic thesis Chapters 5 and 6 (`report/chapters/05_anomaly_engine.tex`, `06_evaluation.tex`) with Highway Transit Corridor equations:
    $$\text{Transit Hours} = \frac{d_{\text{road}}}{45} + \text{Buffer Hours}$$
    $$\text{Total Freight} = 1.50 + 0.018 \cdot d_{\text{road}} + \text{Toll Buffer}$$
  - Added comprehensive test suite distribution table (Table 6.4) and updated evaluation metrics to reflect all 236 passing tests, 21 canonical staples, 64 administrative districts, and 78 verified markets.
  - Successfully compiled and verified thesis document `report/PricePulse_BD_Thesis.pdf` (57 KB) via `report/compile_report.py`.
  - Updated `docs/DEMO_SCRIPT.md` with complete 6-step commercial live demo walkthrough covering Market Pulse Top Mover Card, 3-Channel Consumer Bazaar Basket, Market Stress Test sandbox with zero DB mutation, 64-District Leaflet map with interactive Highway Transit Corridors, Source Health telemetry fallback, and Native Android client offline Room mirroring.
  - Updated `docs/API_SPEC.md` documenting `/api/v1/basket/saved`, `/api/v1/basket/saved/{id}/trend`, and `/api/v1/locations/arbitrage` with corridor waypoints and toll buffers.
  - Verified 100% test pass rate (236/236 green), clean system environment checks (`run_system.py --test`), and clean frontend production build (`npm run build`).

- **TASK-004 / Milestone 018 — Spatial Arbitrage Engine Enhancements & Interactive Corridor Visualization** (2026-09-29):
  - In `app/schemas/spatial.py`, extended `ArbitrageRoute` schema with `waypoints`, `transit_hours_estimated`, `toll_and_buffer_cost_bdt`, `freight_breakdown`, and `corridor_name`.
  - In `app/services/spatial_service.py`, integrated canonical national highway corridors (N5 Jamuna, N1 Highway, N8 Padma, N2 Sylhet, and cross-arterials) with realistic intermediate geographic waypoints, bridge toll buffers (৳0.50 - ৳0.85/kg), and truck transit duration calculations (`d / 45 + buffer`).
  - In `frontend/src/components/BangladeshPriceMap.jsx`, added a toggle switch for "Show Transit Corridors" (পরিবহন করিডোর), dynamic React-Leaflet `<Polyline>` rendering with feasibility coloring (Emerald / Amber / Rose), and an interactive glassmorphic corridor breakdown drawer with responsive tooltips.
  - Verified 100% green test suite (236/236 passing) and cleanly compiled frontend production bundle (`npm run build`).

- **TASK-003 / Milestone 017 — Automated Daily Ingestion Resilience & Live Harvester Hardening** (2026-09-29):
  - Hardened `tcb_collector.py` with multi-strategy table discovery (`.tcb-price-table`, `.price-table`, `.content-table`, dynamic selectors), adaptive column index detection, Bengali/English range numerals (`১২০ - ১৩০`, `120 - 130`, `১২০ থেকে ১৩০`), and exponential backoff retry jitter.
  - Enhanced `dam_live_collector.py` with adaptive column order detection (swapped wholesale vs retail columns), Bengali numeral cell parsing, and granular error telemetry recording in `SourceHealthService`.
  - Upgraded in-process `scheduler.py` worker to harvest all 4 channels (`dam`, `chaldal`, `tcb`, `news`) with non-blocking error containment and decoupled local imports.
  - Hardened `scripts/sync_daily_prices.py` CLI with latency tracking, formatted ASCII summary reporting, and zero unhandled exceptions.
  - Added 8 comprehensive resilience tests in `tests/test_resilient_collectors.py` (235/235 passing).

- **TASK-002 / Milestone 016 — Android Native Basket Compose UI & Room Integration** (2026-09-29):
  - Created `BasketScreen.kt` in Jetpack Compose Material 3 with preset basket quick-select chips, quantity adjustment steppers, line total calculations, and 3-channel cost comparison overview (Wholesale vs Retail vs Online).
  - Integrated `BasketScreen` and bottom `NavigationBar` in `MainActivity.kt` with edge-to-edge Scaffold.
  - Connected local Room DB reactive `savedBaskets` Flow with 1-tap load, save dialog, and cascade deletion.
  - Verified 100% green test suite and clean frontend build.

- **Milestone 015 & Patch 014 — Terminal/API Sanitization & Android Room Offline Mirroring** (2026-09-29):
  - Completely sanitized `run_system.py` banner and comments, removing all undergraduate/viva references.
  - Sanitized `app/api/v1/endpoints/simulation.py` tags, summary, and description to "Market Stress Test & Policy Stress Test".
  - Implemented `SavedBasketEntity`, `SavedBasketItemEntity`, and `BasketDao` in Android Room database (`PricePulseDatabase` v2).
  - Exposed offline basket caching flows and persistence helpers in `OfflinePriceRepository.kt`.
  - Verified 100% green test suite (233/233 tests passing), `run_system.py --test`, and clean Vite production build.

- **Milestone 014 — Production Rebranding, Consumer UI Cleansing & Live Storefront Harvester Engine** (2026-09-29):
  - Rebranded "Viva Simulator" to "Market Stress Test & Economic Scenario Engine" across navigation and scenario testbed.
  - Sanitized frontend titles, descriptions, footers, and provenance cards to commercial civic-tech standards. Verified 0 occurrences of academic/student disclaimers in user interfaces.
  - Hardened `ChaldalLiveCollector` with multi-key JSON extraction, CSS selector DOM fallback, dynamic stock status filtering, and package unit resolution.
  - Extended `scripts/sync_daily_prices.py` to support all 4 national ingestion sources (`dam`, `chaldal`, `tcb`, `news`).
  - Added `ingest_observations()` and `record_health_event()` telemetry bridges.
  - Verified 100% green test suite (233/233 tests passing) and clean production bundle build.

- **TASK-001 — Repository Control Layer Initialization & Persistent Saved Basket Commit** (2026-09-28):
  - Created repository governance files: `AGENTS.md` (rules & invariants), `CLAUDE.md` (fast context pointer), `TASKS.md` (active queue), and `BRAIN.md` (compressed intelligence).
  - Committed Milestone 013 persistent Saved Baskets SQLAlchemy models (`SavedBasket`, `SavedBasketItem`), schemas, endpoints, 30-day CPI trend trajectory, and React frontend view.
  - Verified 100% green test suite (233/233 passing tests) and clean Vite production build.
  - Synchronized with `origin main`.

