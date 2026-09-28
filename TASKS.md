# TASKS.md — Active Execution Queue

This file tracks the active development tasks for **PricePulse BD**. Only items under `## NOW` are currently in progress.

---

## NOW

- None (All development milestones and tasks completed).

---

## NEXT

- None (Production v2.0.0 released & oral defense ready).

---

## BLOCKED
- None.

---

## DONE RECENTLY

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

