# AGENTS.md — Operational Contract for Coding Agents

This document defines the operational contract, architectural invariants, engineering principles, and quality standards for all coding agents collaborating on **PricePulse BD**.

Every agent must read and adhere to these guidelines before inspecting, modifying, or testing the codebase.

---

## 1. Project Mission & Scope

**PricePulse BD** is an academically defensible, local-first commodity market intelligence and anomaly detection platform tailored specifically for Bangladesh's agricultural and retail food supply chains.

The platform monitors, aggregates, normalizes, and analyzes essential commodity prices across 64 administrative districts and multiple market channels (Wholesale, Retail, Online, Government TCB), identifying supply chain anomalies, spatial arbitrage opportunities, and consumer inflation pressures in real time.

- **Author & Researcher**: Farhan Shahriar Polok (CSE Final Year Project / Thesis).
- **Core Stance**: Local-first, privacy-respecting, zero cloud dependency, 100% deterministic and mathematically auditable algorithms. Zero AI/LLM hallucinations in analytical layers.

---

## 2. Architectural Invariants

Agents must never violate or refactor away these architectural invariants:

1. **Local-First SQLite Engine with WAL Mode**:
   - Single ground-truth database file (`pricepulse.db`).
   - SQLite WAL (Write-Ahead Logging) enabled (`PRAGMA journal_mode=WAL;`).
   - Foreign key enforcement active (`PRAGMA foreign_keys=ON;`).
   - Busy timeout configured to 5000ms to guarantee zero lock contention during asynchronous harvests.

2. **Bilingual Normalization Pipeline**:
   - Input normalization combines Unicode NFKC normalization, ASCII/Bengali numeral mapping (`০-৯` $\leftrightarrow$ `0-9`), whitespace stripping, and canonical alias lookup via `data/taxonomy/commodities.json`.
   - Customary Bangladeshi trading units (`হালি` $\to$ 4 pc, `পোয়া` $\to$ 0.25 kg, `মণ` $\to$ 40 kg, `৫০০ গ্রাম / 500ml` $\to$ 0.5 units) are normalized deterministically before persistence or price calculations.

3. **Compound Mathematical Anomaly Core**:
   - Price shock evaluation is based on rigorous statistical metrics: 14-day rolling Simple Moving Average ($SMA_{14}$), dynamic Z-score ($Z \ge 2.5$), 14-day Coefficient of Variation ($CV$), and Spatial Dispersion Index $D(t)$.
   - All anomaly explanations are generated deterministically from parameter metrics, not black-box ML or LLM summarization.

4. **Decoupled REST API Contract**:
   - FastAPI v1 routing mounted under `/api/v1/`.
   - Strict Pydantic v2 data transfer schemas (`app/schemas/`) with runtime validation.
   - Comprehensive error handling: Return 404 for missing entities, 422 for unprocessable payloads, never unhandled 500s.

5. **Sandbox Isolation for Simulations**:
   - The Viva Simulation Sandbox (`/api/v1/simulation/inject-shock`) evaluates hypothetical supply shocks and price anomalies in-memory or on ephemeral state.
   - **Ground-truth database tables must never be corrupted with synthetic or simulated shocks.**

---

## 3. Development Principles & Data Integrity

- **Absolute Data Integrity**: Never fabricate prices, sources, locations, test results, or benchmark metrics.
- **Strict Data Classification**:
  - `REAL LIVE DATA`: Directly collected from live online/government endpoints with active timestamps and source URLs.
  - `CACHED REAL DATA`: Immutable historical records stored in SQLite with full provenance and source confidence ratings.
  - `FIXTURE DATA`: Canonical test fixtures stored under `data/fixtures/` for deterministic offline testing.
  - `SIMULATED SHOCK DATA`: Ephemeral memory structures used exclusively in the Viva Simulation Sandbox.
- **Never Cross-Contaminate**: The UI, reporting engine, and thesis drafts must explicitly differentiate these categories.

---

## 4. Technology Stack & Operational Commands

### Backend (Python 3.11+)
- **Framework**: FastAPI with Uvicorn.
- **Database**: SQLite 3 with SQLAlchemy 2.0 ORM.
- **Scraping / Ingestion**: Requests, BeautifulSoup4, Playwright.
- **Run Backend**:
  ```bash
  venv\Scripts\python.exe run_system.py
  # or
  venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
  ```

### Frontend (React 18 + Vite)
- **Framework**: React 18, Vite 5, TailwindCSS, Lucide React, Recharts, Leaflet.
- **Run Frontend**:
  ```bash
  cd frontend
  npm run dev
  ```
- **Build Frontend**:
  ```bash
  cd frontend
  cmd /c "npm run build"
  ```

### Native Android Client (Kotlin / SDK 34)
- **Framework**: Jetpack Compose, Room Database, Material 3, MPAndroidChart / Custom Canvas.
- **Location**: `android/`

### Test Suite (Pytest)
- **Command**:
  ```bash
  venv\Scripts\python.exe -m pytest tests/ -q
  ```
- **Standard**: All 233+ unit and integration tests must pass with 100% green status.

---

## 5. Git Discipline & Definition of Done

1. **Commit Convention**: Follow Conventional Commits:
   - `feat: ...` for verified new capabilities.
   - `fix: ...` for bug fixes.
   - `test: ...` for test suite additions.
   - `docs: ...` for documentation updates.
   - `refactor: ...` for non-breaking internal improvements.
2. **Pre-Commit Verification**:
   - Ensure `git status` contains no untracked scratch files, temporary logs, or binary test dumps.
   - Ensure the entire test suite passes (`pytest tests/ -q`).
   - Ensure frontend production bundle compiles cleanly (`npm run build`).
3. **Definition of Done**:
   A task is complete **only** when:
   $$\text{Done} = \text{Implemented} + \text{Tested} + \text{Runtime Verified} + \text{Zero Regressions} + \text{Docs Synchronized}$$

---

## 6. Forbidden Behaviors

- **DO NOT** introduce external paid or cloud AI APIs (OpenAI, Anthropic, Gemini, Groq) into the core runtime logic.
- **DO NOT** use non-deterministic stochastic models where exact statistical formulas are required.
- **DO NOT** rewrite stable working subsystems because another pattern looks cleaner.
- **DO NOT** commit unverified or mocked-up tests that skip runtime checks.
- **DO NOT** delete, truncate, or overwrite production or demo database tables without rollback safeguards.
