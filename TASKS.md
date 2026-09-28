# TASKS.md — Active Execution Queue

This file tracks the active development tasks for **PricePulse BD**. Only items under `## NOW` are currently in progress.

---

## NOW

### TASK-004 — Spatial Arbitrage Engine Enhancements & Corridor Visualization Polish
- **Status**: IN_PROGRESS
- **Priority**: MEDIUM
- **Goal**: Enhance `SpatialService` inter-district corridor analytics with realistic transport route waypoints, seasonal river ferry congestion buffers, and interactive corridor overlays in `BangladeshPriceMap.jsx`.
- **Why**: Elevates the academic defense for supply chain bottleneck analysis between northern agricultural production hubs and southern metropolitan demand centers.
- **Dependencies**: `TASK-001`, `TASK-003`.
- **Files Likely Affected**:
  - `app/services/spatial_service.py`
  - `app/api/v1/endpoints/locations.py`
  - `frontend/src/components/BangladeshPriceMap.jsx`
  - `tests/test_national_spatial.py`

---

## NEXT

### TASK-005 — Viva Defense Demonstration Script Verification & Academic LaTeX Report Alignment
- **Status**: PLANNED
- **Priority**: HIGH
- **Goal**: Conduct a comprehensive verification of `docs/DEMO_SCRIPT.md`, `docs/VIVA_DEFENSE_GUIDE.md`, and compile the final LaTeX thesis draft (`report/compile_report.py`), ensuring that all tables, formulas, and figures match recent benchmark figures.
- **Why**: Ensures absolute defensibility during the final thesis defense and oral viva examination before university evaluators.
- **Dependencies**: `TASK-001`, `TASK-002`, `TASK-003`.
- **Files Likely Affected**:
  - `docs/DEMO_SCRIPT.md`
  - `docs/VIVA_DEFENSE_GUIDE.md`
  - `report/main.tex`
  - `report/compile_report.py`

---

## BLOCKED
- None.

---

## DONE RECENTLY

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

