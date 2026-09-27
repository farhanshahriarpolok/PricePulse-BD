# System Architecture

## 1. Overview & System Philosophy

PricePulse BD is designed as an open-source, local-first commodity market intelligence pipeline tailored for Bangladesh's agricultural and consumer retail ecosystem. The architecture balances two core imperatives:
1. **Deterministic Data Ingestion**: Guaranteeing traceability, auditable provenance, and metric standardization across diverse, unstructured bulletins.
2. **Decoupled Client Delivery**: Serving standard, versioned JSON REST APIs suitable for web visualization platforms and native Android mobile clients (Kotlin + Jetpack Compose).

```
+-------------------------------------------------------------------------------+
|                             External Publishers                               |
|   (DAM Bulletins, TCB Bulletins, Wholesale Portals, Quick-Commerce APIs)      |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       Ingestion & Extraction Layer                            |
|   - BaseCollector Interface                                                   |
|   - Deterministic Bulletin Parsers (BeautifulSoup4 / lxml)                    |
|   - Raw Payload Snapshotting                                                  |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       Normalization & Scoring Engine                          |
|   - Bilingual Alias Matching (Bengali Unicode + Romanized Phonetics)          |
|   - Standard SI Unit Standardization (Maund/Seer/Hali -> Kg/Liter/Pc)         |
|   - Multi-Attribute Linear Confidence Scoring Model                           |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                        Relational Storage (SQLite WAL)                        |
|   - Spatial Hierarchy (Division -> District -> Market)                        |
|   - Canonical Commodity Registry & Aliases                                    |
|   - Time-Series Price Observations with Compound Spatial/Temporal Indexes     |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                           Application API Service                             |
|   - FastAPI REST Layer (Async/Await)                                          |
|   - Pydantic v2 Request/Response Schemas                                      |
|   - Mobile-First JSON Payloads (Android Kotlin / Jetpack Compose Ready)       |
+-------------------------------------------------------------------------------+
```

---

## 2. Ingestion Pipeline Layers

### 2.1 Harvest & Extraction Layer (`app/collectors/`)
Collectors implement the abstract `BaseCollector` interface. Each collector encapsulates:
- Source identification (`source_code`, `source_type`).
- Safe HTTP retrieval or deterministic local fixture parsing.
- Extraction of raw records containing the verbatim commodity label, price range (min, max, modal), raw unit, market identifier, and bulletin date.

### 2.2 Normalization & Harmonization Layer (`app/services/normalizer.py`)
Because price reporting in Bangladesh blends English terminology with Bengali script and customary wholesale units, this layer executes two deterministic pipelines:
1. **Commodity Resolution**: Normalizes diacritics, strips whitespace, converts Unicode Bengali to standard tokens, and maps against a pre-compiled taxonomy tree. Unmatched entities are flagged for administrative inspection rather than discarded.
2. **Unit Conversion**: Translates regional volumetric and mass standards into SI units:
   - $1\text{ Maund (মণ)} = 40.0\text{ kg}$ (standard commercial wholesale metric in Bangladesh).
   - $1\text{ Seer (সের)} = 0.933\text{ kg}$.
   - $1\text{ Hali (হালি)} = 4\text{ pieces}$.
   - Prices are recalculated to base BDT per unit ($\text{BDT/kg}$, $\text{BDT/liter}$, $\text{BDT/pc}$).

### 2.3 Confidence Assessment Layer (`app/services/confidence.py`)
Every observation is tagged with a deterministic confidence metric $C \in [0.0, 1.0]$. The score reflects:
- Source verification status and institutional authority.
- Exactness of commodity alias resolution.
- Freshness relative to the extraction timestamp.
- Internal consistency (e.g., $P_{\text{min}} \le P_{\text{avg}} \le P_{\text{max}}$).

### 2.4 Deduplication & Persistence Layer (`app/services/ingestion.py`)
To prevent redundant rows when bulletins are re-ingested or updated:
- Deduplication keys are formed from `(commodity_id, market_id, source_id, observation_date, price_type)`.
- If a record exists, updates are applied only if the incoming record exhibits an equal or higher confidence score.

---

## 3. Storage Architecture: SQLite with Write-Ahead Logging (WAL)

The initial implementation targets a local-first SQLite database (`pricepulse.db`), providing zero-dependency deployment for research evaluation while maintaining production-grade concurrency.

### Concurrency & Performance Configuration
Upon connection initialization, the SQLAlchemy engine applies SQLite pragmas:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA cache_size = -64000; -- 64MB memory cache
PRAGMA busy_timeout = 5000;  -- 5 second wait before SQLITE_BUSY
```

- **WAL Mode**: Enables background ingestion processes to insert and update rows concurrently while FastAPI handles incoming client queries without read/write locks colliding.
- **Portability**: The database engine is configured via abstract SQLAlchemy ORM models, enabling straightforward future migration to PostgreSQL as workload scales.

---

## 4. Mobile API Integration Design (Android Decoupling)

The presentation layer is decoupled from ingestion. The backend serves pure JSON REST APIs configured according to standard mobile client constraints:

1. **Lightweight Data Transfer**: Payloads omit internal database metadata and present standardized, pre-computed fields:
   - Canonical name and localized Bengali label.
   - Standardized unit price with currency denomination (`BDT`).
   - Location metadata (Market name, District, Division, Coordinates).
2. **Network Resilience**: Endpoints support ISO 8601 timestamps and compact cache-control headers, enabling Android clients (via Retrofit + Room) to cache historical price curves locally for offline use.
3. **Strict Validation**: Pydantic v2 schemas validate input parameters and serialization, preventing mobile app crashes caused by `null` or unexpected payload types.
