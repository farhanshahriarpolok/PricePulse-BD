# TASKS.md — Active Execution Queue

This file tracks the active development tasks for **PricePulse BD**. Only items under `## NOW` are currently in progress.

---

## NOW
- *No active execution tasks. TASK-001 completed successfully. Ready for TASK-002.*

---

## NEXT

### TASK-002 — Android Client Offline Synchronization & Saved Basket Mirroring
- **Status**: PLANNED
- **Priority**: HIGH
- **Goal**: Extend the native Android client Room database to store user-defined bazaar baskets locally, mirror the FastAPI `/api/v1/basket/saved` schema, and display the 3-channel cost comparison in Jetpack Compose.
- **Why**: Fulfills the project requirement for dual-platform (Web + Android) parity and offline-first mobile utility for shoppers visiting physical wet markets.
- **Dependencies**: `TASK-001` completion.
- **Files Likely Affected**:
  - `android/app/src/main/java/com/pricepulse/bd/data/local/Daos.kt`
  - `android/app/src/main/java/com/pricepulse/bd/data/local/Entities.kt`
  - `android/app/src/main/java/com/pricepulse/bd/data/local/PricePulseDatabase.kt`
  - `android/app/src/main/java/com/pricepulse/bd/ui/screens/BasketScreen.kt`

### TASK-003 — Automated Daily Ingestion Resilience & Live TCB/Chaldal Scraper Hardening
- **Status**: PLANNED
- **Priority**: HIGH
- **Goal**: Harden autonomous harvesters (`tcb_collector.py`, `chaldal_collector.py`, `news_collector.py`) against upstream markup shifts, implement exponential backoff jitter, and verify graceful fallback to cached bulletins without pipeline halts.
- **Why**: Guarantees live data integrity and continuous operation even when upstream government websites experience intermittent downtime.
- **Dependencies**: `TASK-001` completion.
- **Files Likely Affected**:
  - `app/collectors/tcb_collector.py`
  - `app/collectors/chaldal_collector.py`
  - `app/collectors/news_collector.py`
  - `app/services/source_health.py`
  - `tests/test_tcb_and_news_collectors.py`

### TASK-004 — Spatial Arbitrage Engine Enhancements & Corridor Visualization Polish
- **Status**: PLANNED
- **Priority**: MEDIUM
- **Goal**: Enhance `SpatialService` inter-district corridor analytics with realistic transport route waypoints, seasonal river ferry congestion buffers, and interactive corridor overlays in `BangladeshPriceMap.jsx`.
- **Why**: Elevates the academic defense for supply chain bottleneck analysis between northern agricultural production hubs and southern metropolitan demand centers.
- **Dependencies**: `TASK-001`.
- **Files Likely Affected**:
  - `app/services/spatial_service.py`
  - `app/api/v1/endpoints/locations.py`
  - `frontend/src/components/BangladeshPriceMap.jsx`
  - `tests/test_national_spatial.py`

### TASK-005 — Viva Defense Demonstration Script Verification & Academic LaTeX Report Alignment
- **Status**: PLANNED
- **Priority**: HIGH
- **Goal**: Conduct a comprehensive verification of `docs/DEMO_SCRIPT.md`, `docs/VIVA_DEFENSE_GUIDE.md`, and compile the final LaTeX thesis draft (`report/compile_report.py`), ensuring that all tables, formulas, and figures match recent benchmark figures.
- **Why**: Ensures absolute defensibility during the final thesis defense and oral viva examination before university evaluators.
- **Dependencies**: `TASK-001`, `TASK-002`.
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

