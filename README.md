# PricePulse BD

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Database: SQLite WAL](https://img.shields.io/badge/Database-SQLite%20(WAL)-blue.svg)](https://www.sqlite.org/wal.html)
[![FastAPI Ready](https://img.shields.io/badge/FastAPI-Production%20Ready-009688.svg)](https://fastapi.tiangolo.com/)

An automated market intelligence engine and commodity price aggregator designed for the retail and wholesale agricultural commodity ecosystems across Bangladesh.

---

## 1. Research Context & Problem Statement

Retail and wholesale commodity markets across Bangladesh exhibit pronounced information asymmetry and spatial price disparities. Essential daily commodities—such as rice, onions, potatoes, lentils, and edible oils—frequently experience volatile day-to-day price shifts influenced by seasonal cycles, transport logistics, and fragmented wholesale market tiers (e.g., Karwan Bazar, Khatunganj, Badamtali).

While government agencies like the Department of Agricultural Marketing (DAM) and Trading Corporation of Bangladesh (TCB) publish periodic bulletins, and modern quick-commerce platforms (such as Chaldal, Shwapno, and Meena Bazar) maintain live retail catalogs, the data exists in non-standardized formats:
- Inconsistent commodity naming across Bengali and English phonetic variants (e.g., *পেঁয়াজ*, *দেশি পেঁয়াজ*, *Onion Local*, *Indian Onion*).
- Fragmented units of measurement ranging from customary regional units (*maund*, *seer*, *hali*) to metric standards (*kg*, *quintal*, *liter*).
- Diverse reporting intervals, collection methodologies, and reliability levels.

**PricePulse BD** is an undergraduate CSE capstone research initiative aimed at establishing an open-source, deterministic ingestion and normalization pipeline that consolidates these disparate sources into canonical, time-stamped market observations backed by weighted confidence scoring.

---

## 2. Core Architecture

The system is constructed with a modular, layered architecture designed for local-first execution, high-concurrency read operations, and clean decoupling between ingestion workers and downstream presentation clients (Web dashboard and Android mobile client).

```
+--------------------------------------------------------------------------+
|                         External Data Sources                            |
|  [DAM Daily Bulletins]     [TCB Price Lists]     [Retail E-Commerce APIs]|
+-------------------------------------+------------------------------------+
                                      |
                                      v
+--------------------------------------------------------------------------+
|                     Ingestion & Extraction Layer                         |
|  - HTML Bulletin Scrapers (BeautifulSoup4)                               |
|  - Headless API Collectors                                               |
|  - Resilient Raw Payload Archival                                        |
+-------------------------------------+------------------------------------+
                                      |
                                      v
+--------------------------------------------------------------------------+
|                 Canonical Normalization Engine                           |
|  - Bilingual Taxonomy Resolution (Bengali Unicode & Romanized Aliases)   |
|  - Metric Unit Standardization (Maund/Seer/Hali -> Kg/Liter/Pieces)      |
|  - Multi-factor Linear Confidence Scoring (Source, Freshness, Mapping)   |
+-------------------------------------+------------------------------------+
                                      |
                                      v
+--------------------------------------------------------------------------+
|                   Relational Persistence (SQLite WAL)                    |
|  - Spatial Hierarchy (Divisions -> Districts -> Markets)                 |
|  - Commodity & Alias Catalog                                             |
|  - Time-Series Price Observations with Provenance Metadata               |
+-------------------------------------+------------------------------------+
                                      |
                                      v
+--------------------------------------------------------------------------+
|                         REST API Service Layer                           |
|  - FastAPI Endpoints (Pydantic v2 Serialization)                         |
|  - Decoupled JSON Contracts for Web Dashboard & Android Native Client    |
+--------------------------------------------------------------------------+
```

### Key Technical Decisions
1. **Local-First SQLite with WAL Mode**: Designed to run reliably without demanding complex distributed infrastructure during local prototyping and field testing. Write-Ahead Logging (WAL) ensures non-blocking concurrent reads while background ingestion scripts write observations.
2. **Deterministic Entity Normalization**: Rule-based taxonomy matching ensures reproducible transformations from raw scraped text to canonical database records without reliance on unpredictable black-box heuristics.
3. **Decoupled Mobile-First API**: The backend delivers clean JSON payload structures matching OpenAPI 3.1 specifications, enabling native Android (Kotlin / Jetpack Compose) consumption alongside web dashboards.

---

## 3. Directory Layout

```
PricePulse BD/
├── .gitignore                      # Git exclusion rules (venv, temp DBs, orchestration)
├── requirements.txt                # Production and test dependencies
├── README.md                       # Academic & system documentation
├── CHANGELOG.md                    # Semantic version release notes
├── run_system.py                   # Unified system orchestrator and launcher
├── report/                         # Academic Undergraduate Research Thesis (LaTeX)
│   ├── main.tex                    # Master thesis root document
│   ├── references.bib              # Scholarly BibTeX bibliography
│   └── chapters/                   # Chapters 01 to 07 (Architecture, Anomaly, Evaluation)
├── docs/                           # Technical documentation & defense materials
│   ├── ARCHITECTURE.md             # System design, dataflow, and concurrency model
│   ├── DATA_MODEL.md               # Relational schema and confidence formulation
│   ├── NORMALIZATION.md            # Taxonomy, alias resolution, and unit conversion
│   ├── ALGORITHMS.md               # Mathematical formulations for anomaly & spatial spread
│   ├── API_SPEC.md                 # REST API endpoints for Web & Android
│   ├── VIVA_DEFENSE_GUIDE.md       # Comprehensive examination defense playbook
│   └── DEMO_SCRIPT.md              # 6-step deterministic live presentation script
├── frontend/                       # Interactive Web Dashboard (React 18 + Vite)
│   ├── src/
│   │   ├── api/                    # Axios REST client and endpoint services
│   │   ├── components/             # Reusable UI cards, Recharts, Leaflet map
│   │   ├── App.jsx                 # Multi-view application shell
│   │   ├── main.jsx                # DOM mount entry
│   │   └── index.css               # Tailwind & Leaflet global styles
│   ├── package.json                # React, Vite, Tailwind, Leaflet, Recharts deps
│   └── vite.config.js              # Vite server config with /api reverse proxy
├── app/
│   ├── core/
│   │   ├── config.py               # Application settings and filesystem paths
│   │   └── database.py             # SQLAlchemy engine with SQLite WAL initialization
│   ├── models/
│   │   ├── commodity.py            # Commodity and CommodityAlias ORM models
│   │   ├── location.py             # Division, District, Market spatial hierarchy
│   │   ├── source.py               # Data Source registry and reliability scores
│   │   └── observation.py          # PriceObservation entity with provenance
│   ├── collectors/
│   │   ├── base.py                 # Abstract BaseCollector interface
│   │   └── dam_fixture_collector.py# Deterministic parser for DAM bulletin HTML
│   └── services/
│       ├── normalizer.py           # Taxonomy matching and unit standardization
│       ├── confidence.py           # Weighted linear confidence scoring
│       └── ingestion.py            # Orchestrator: Harvest -> Normalize -> Persist
├── data/
│   ├── fixtures/
│   │   └── dam_bulletin_sample.html# Realistic DAM daily bulletin fixture
│   └── taxonomy/
│       ├── commodities.json        # Canonical commodities and bilingual aliases
│       └── locations.json          # Spatial seed data (Divisions, Districts, Markets)
├── scripts/
│   ├── init_db.py                  # DDL creation and taxonomy seeder
│   └── seed_and_ingest.py          # Pipeline runner executing fixture ingestion
└── tests/
    ├── test_normalization.py       # Unit tests for alias and unit conversions
    └── test_ingestion.py           # Integration tests for DB persistence & metrics
```

---

## 4. Getting Started

### Prerequisites
- Python 3.11 or newer (Python 3.14 compatible)
- Git

### Installation & Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/farhanshahriarpolok/PricePulse-BD.git
   cd "PricePulse BD"
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install project dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database & Seed Taxonomy:**
   ```bash
   python scripts/init_db.py
   ```
   *This creates `pricepulse.db` in the repository root, applies SQLite WAL pragma, and populates canonical commodities, aliases, and market locations.*

5. **Execute Seed & Ingestion Pipeline:**
   ```bash
   python scripts/seed_and_ingest.py
   ```
   *This extracts observations from the verified Department of Agricultural Marketing (DAM) bulletin fixture, resolves aliases, standardizes prices to standard units (BDT/kg or BDT/liter), computes confidence scores, and stores them in SQLite.*

6. **Run Backend Test Suite:**
   ```bash
   pytest tests/ -v
   ```

7. **Launch Frontend Web Client (Development):**
   ```bash
   cd frontend
   npm install
   # Development server (http://localhost:3000) with /api proxy to FastAPI:
   npm run dev
   # Production build verification:
   npm run build
   ```

8. **One-Click Unified System Launcher (Offline Viva Mode):**
   ```bash
   # Launch both FastAPI REST API and React Web Client simultaneously on http://localhost:8000
   python run_system.py

   # Perform environment self-test without launching:
   python run_system.py --test
   ```

---

## 5. Normalization & Confidence Formulation

### Unit Standardization
Raw market reports use varying traditional and metric units. PricePulse BD standardizes all observations to base metric units:
- **Weight**: 1 Maund (মণ) = 40.0 kg (customary commercial market standard in Bangladesh); 1 Seer (সের) = 0.933 kg; 1 Quintal (কুইন্টাল) = 100.0 kg; 1 Gram = 0.001 kg. Canonical base: `kg`.
- **Volume**: 1 Liter = 1.0 L; 1 Milliliter = 0.001 L. Canonical base: `liter`.
- **Count**: 1 Hali (হালি) = 4 units; 1 Dozen (ডজন) = 12 units. Canonical base: `pc`.

### Confidence Score Formula
Each ingested observation is assigned a confidence metric $C \in [0.0, 1.0]$:

$$C = (w_{\text{src}} \times S_{\text{src}}) + (w_{\text{alias}} \times S_{\text{alias}}) + (w_{\text{fresh}} \times S_{\text{fresh}}) + (w_{\text{cmpl}} \times S_{\text{cmpl}})$$

Where:
- $S_{\text{src}}$: Base reliability score of the publisher (e.g., DAM Official = 0.90, Verified Retail = 0.85).
- $S_{\text{alias}}$: Match quality of the commodity name (Exact = 1.0, Direct Alias = 0.90, Substring/Fuzzy = 0.70).
- $S_{\text{fresh}}$: Temporal freshness decay based on observation age.
- $S_{\text{cmpl}}$: Data completeness (presence of min, max, average ranges, and verified market links).
- Weights satisfy: $w_{\text{src}} + w_{\text{alias}} + w_{\text{fresh}} + w_{\text{cmpl}} = 1.0$.

---

## 6. Live Web Ingestion, Fallback Resilience & Scheduler Mechanics

### Resilient Live Harvesting & Graceful Degradation
To operate robustly across real-world internet instability without crashing or polluting time-series observations, PricePulse BD implements a fault-tolerant multi-tier collection strategy:
1. **Live HTTP Harvesting (`DAMLiveCollector`, `ChaldalLiveCollector`)**:
   - Collectors attempt real-time harvesting against upstream web endpoints (`http://www.dam.gov.bd` bulletin tables and retail grocery catalog feeds).
   - Upstream requests enforce strict connection timeouts (3.0s) and exponential backoff retry cycles.
2. **Deterministic Offline Fallback**:
   - If upstream servers face DNS resolution failure, network disconnection, HTTP 5xx internal server errors, or anti-scraping rate limits (HTTP 429), collectors **never crash**.
   - The engine automatically logs a structured warning and delegates ingestion to verified local cached fixtures (`dam_bulletin_sample.html`, `chaldal_catalog_sample.json`).
   - Observations harvested from fallback fixtures are marked with completeness flags, and provider health is updated to `DEGRADED`.
3. **Telemetry & Source Health (`SourceHealthService`)**:
   - Real-time latency tracking (`latency_ms`), last synchronization timestamps, success/error counters, and provider status (`HEALTHY`, `DEGRADED`, `OFFLINE`).
   - Accessible via REST endpoint `GET /api/v1/system/sources`.

### In-Process Background Task Scheduler
- Built on Python's native `asyncio` event loop inside `app/services/scheduler.py`, requiring zero external daemon or cron infrastructure.
- **Periodic Harvesting**: Automatically executes periodic data harvests and incremental anomaly checks on a recurring 12-hour cadence.
- **Asynchronous On-Demand Trigger**:
  - `POST /api/v1/system/sync` schedules background execution without blocking the FastAPI event loop and returns an immediate tracking task ID.
  - Clients poll `GET /api/v1/system/sync/{task_id}` for execution progress, inserted count, and updated record counts.
- **Application Lifespan Integration**: Integrated into FastAPI `lifespan` in `app/main.py` ensuring clean task startup and graceful teardown during process termination.

---

## 7. Academic Thesis & Viva Defense Materials

- **Undergraduate Research Thesis (LaTeX)**: Located in [`report/`](file:///D:/PricePulse%20BD/report/). Compilable via `pdflatex main.tex` or `xelatex main.tex`. Incorporates full methodology, mathematical formulations, and evaluation across 7 chapters.
- **Viva Defense Master Guide**: [`docs/VIVA_DEFENSE_GUIDE.md`](file:///D:/PricePulse%20BD/docs/VIVA_DEFENSE_GUIDE.md) provides comprehensive, academically defensible answers addressing core Computer Science contributions, parametric Z-score justification, confidence formulation, and web harvesting boundaries.
- **Live Demonstration Walkthrough**: [`docs/DEMO_SCRIPT.md`](file:///D:/PricePulse%20BD/docs/DEMO_SCRIPT.md) outlines a 6-step deterministic 5-minute presentation script designed specifically for the final examination committee.

---

## 8. Research Roadmap

- [x] **Milestone 001**: Relational schema, SQLite WAL configuration, bilingual normalization engine, DAM bulletin ingestion slice, and automated testing.
- [x] **Milestone 002**: Realtime on-demand price search engine, Chaldal online retail collector, channel spread analytics, and FastAPI REST routing.
- [x] **Milestone 003**: Explainable statistical anomaly detection engine (Rolling SMA, Z-score, Volatility CV), Bangladesh spatial spread with GeoJSON, and 30-day historical seed generator.
- [x] **Milestone 004**: Modern interactive web client (React 18 + Vite + Tailwind CSS + Leaflet + Recharts) with 5 core intelligence views and bilingual search.
- [x] **Milestone 005**: Academic LaTeX research thesis, Viva Defense Master Guide, 6-step live demo script, and unified system launcher (`run_system.py`).
- [x] **Milestone 006**: Protein and pulse taxonomy expansion (Broiler Chicken, Eggs, Masur Dal, Garlic), customary count units (`hali`, `dozen`), side-by-side comparison view, and field spot price ingestion form.
- [x] **Milestone 007**: Resilient live web harvesting (DAM and Chaldal), zero-downtime offline fallback, in-process async scheduler, source health monitor, and UI live sync controls.
- [x] **Milestone 008**: Quantitative evaluation suite, P95/P99 latency benchmarks, LaTeX vector figures, and interactive Reveal.js presentation deck.
- [x] **Milestone 009**: Full 21-commodity market basket expansion (Beef, Mutton, Fish, Milk, Green Chilli, Sugar, Salt), live marquee ticker, category filtering, and commercial Material 3 Android app.
- [x] **Milestone 010**: National 64-District spatial expansion, Spatial Price Dispersion Index $D(t)$, freight/transport arbitrage model, autonomous TCB & newspaper regex harvesters, Android Room offline database caching, custom Canvas price charts, and Live Viva Defense Simulation Sandbox.

---

## 8. Viva Defense Live Simulation Mode

Examiners and evaluators can interactively stress-test the statistical anomaly detection engine without altering ground-truth records:
1. Navigate to the **"Viva Simulator"** tab in the web client.
2. Select target commodity and economic scenario (e.g. *Sudden Supply Disruption*, *Import Tariff Spike*, *Transport Strike*, *Cartel Hoarding*).
3. Adjust sliders:
   - **Injected Price Shift (Δ%)**: -50% (Crash) to +100% (Crisis).
   - **Shock Window Duration**: 1 to 14 days.
   - **Baseline Price Drift**: -30% to +50%.
   - **Volatility Noise (σ)**: 0% to 20%.
4. Observe real-time Recharts trajectory updating the ground-truth line vs simulated curve and rolling 14-day SMA.
5. Inspect the dynamic Z-score badge, Volatility CV%, and instant explainable natural language justification generated on-the-fly.

---

## 9. License & Academic Attribution

This project is developed as part of an undergraduate CSE Final Year Research Project.
- **Author**: Farhan Shahriar Polok
- **Year**: 2026
- Released under the [MIT License](LICENSE).


