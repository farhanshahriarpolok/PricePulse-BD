# Data Model & Relational Schema

## 1. Relational Schema Architecture

PricePulse BD organizes its domain into five relational groups:
1. **Commodity Taxonomy**: Canonical commodities and their multilingual alias variations.
2. **Spatial Hierarchy**: Administrative tree mapping divisions, districts, and physical/online retail markets.
3. **Source Registry**: Institutional and commercial publishers with assigned reliability metrics.
4. **Price Observations**: Time-series price points with raw values, normalized values, and provenance.
5. **Ingestion Logs**: Audit trails tracking batch ingestion runs.

---

## 2. Entity Specifications

```
+-------------------+        +--------------------+
|    commodities    | 1    * | commodity_aliases  |
+-------------------+--------+--------------------+
| id (PK)           |        | id (PK)            |
| canonical_name    |        | commodity_id (FK)  |
| bangla_name       |        | alias              |
| category          |        | language           |
| default_unit      |        | confidence_weight  |
+---------+---------+        +--------------------+
          | 1
          |
          | *
+---------+-----------+        +--------------------+
|  price_observations | *    1 |      markets       |
+---------------------+--------+--------------------+
| id (PK)             |        | id (PK)            |
| commodity_id (FK)   |        | district_id (FK)   |
| market_id (FK)      |        | name               |
| source_id (FK)      |        | bangla_name        |
| raw_name            |        | market_type        |
| raw_price           |        | latitude           |
| raw_unit            |        | longitude          |
| normalized_price    |        +---------+----------+
| normalized_unit     |                  | *
| price_type          |                  |
| observation_date    |                  | 1
| scraped_at          |        +---------+----------+
| confidence_score    |        |     districts      |
+---------+-----------+        +--------------------+
          | *                  | id (PK)            |
          |                    | division_id (FK)   |
          | 1                  | name               |
+---------+-----------+        | bangla_name        |
|       sources       |        +---------+----------+
+---------------------+                  | *
| id (PK)             |                  | 1
| code (UNIQUE)       |        +---------+----------+
| name                |        |     divisions      |
| source_type         |        +--------------------+
| base_url            |        | id (PK)            |
| reliability_score   |        | name               |
+---------------------+        | bangla_name        |
                               +--------------------+
```

### 2.1 Table: `commodities`
Stores verified canonical commodity records.
- `id` (INTEGER, Primary Key, Auto-increment)
- `canonical_name` (VARCHAR(120), Unique, Not Null) - e.g., `"Onion (Local)"`
- `bangla_name` (VARCHAR(120), Not Null) - e.g., `"দেশি পেঁয়াজ"`
- `category` (VARCHAR(60), Not Null) - e.g., `"Vegetables"`, `"Grains"`, `"Oil"`
- `default_unit` (VARCHAR(20), Not Null) - e.g., `"kg"`, `"liter"`, `"pc"`
- `created_at` (DATETIME, Default: Current UTC)

### 2.2 Table: `commodity_aliases`
Provides bilingual matching keys to resolve raw bulletin entries to canonical IDs.
- `id` (INTEGER, Primary Key, Auto-increment)
- `commodity_id` (INTEGER, Foreign Key -> `commodities.id`, Not Null)
- `alias` (VARCHAR(150), Not Null) - e.g., `"deshi peyaj"`, `"পেঁয়াজ (দেশী)"`, `"Onion Deshi"`
- `language` (VARCHAR(10), Not Null) - `"bn"`, `"en"`, or `"phonetic"`
- `confidence_weight` (FLOAT, Default: 1.0) - Weight penalty for ambiguous aliases

### 2.3 Spatial Hierarchy: `divisions`, `districts`, `markets`
Encapsulates geographic distribution and market classification across Bangladesh.
- **`divisions`**: `id`, `name`, `bangla_name` (e.g., Dhaka, Chittagong).
- **`districts`**: `id`, `division_id`, `name`, `bangla_name` (e.g., Dhaka, Gazipur, Chattogram).
- **`markets`**:
  - `id` (INTEGER, Primary Key)
  - `district_id` (INTEGER, Foreign Key -> `districts.id`)
  - `name` (VARCHAR(120), Not Null) - e.g., `"Karwan Bazar"`
  - `bangla_name` (VARCHAR(120), Nullable) - e.g., `"কারওয়ান বাজার"`
  - `market_type` (VARCHAR(30)) - `"wholesale"`, `"retail"`, `"online"`
  - `latitude` (FLOAT, Nullable)
  - `longitude` (FLOAT, Nullable)

### 2.4 Table: `sources`
Maintains publishers and institutional sources.
- `id` (INTEGER, Primary Key)
- `code` (VARCHAR(50), Unique, Not Null) - e.g., `"DAM_DAILY"`, `"TCB_BULLETIN"`
- `name` (VARCHAR(150), Not Null) - e.g., `"Department of Agricultural Marketing"`
- `source_type` (VARCHAR(40)) - `"government"`, `"retail_ecommerce"`, `"wholesale_market"`
- `base_url` (VARCHAR(255), Nullable)
- `reliability_score` (FLOAT, Default: 0.8) - Prior weight in confidence formulation

### 2.5 Table: `price_observations`
Contains the core atomic time-series observation data.
- `id` (INTEGER, Primary Key)
- `commodity_id` (INTEGER, Foreign Key -> `commodities.id`, Not Null)
- `market_id` (INTEGER, Foreign Key -> `markets.id`, Not Null)
- `source_id` (INTEGER, Foreign Key -> `sources.id`, Not Null)
- `raw_name` (VARCHAR(200), Not Null) - Original string extracted from bulletin
- `raw_price` (FLOAT, Not Null) - Price as extracted before metric conversion
- `raw_unit` (VARCHAR(50), Not Null) - Original unit string (e.g., `"মণ"`, `"কেজি"`)
- `normalized_price` (FLOAT, Not Null) - Standardized price in BDT per canonical unit
- `normalized_unit` (VARCHAR(20), Not Null) - Canonical unit (`"kg"`, `"liter"`, `"pc"`)
- `price_type` (VARCHAR(30), Not Null) - `"retail_avg"`, `"retail_min"`, `"retail_max"`, `"wholesale_avg"`
- `observation_date` (DATE, Not Null) - Date recorded in the bulletin
- `scraped_at` (DATETIME, Default: Current UTC)
- `confidence_score` (FLOAT, Not Null) - Computed composite confidence $[0.0, 1.0]$

---

## 3. Confidence Score Formulation

The confidence score $C \in [0.0, 1.0]$ represents the mathematical credibility of a normalized observation:

$$C = (w_{\text{src}} \cdot S_{\text{src}}) + (w_{\text{alias}} \cdot S_{\text{alias}}) + (w_{\text{fresh}} \cdot S_{\text{fresh}}) + (w_{\text{cmpl}} \cdot S_{\text{cmpl}})$$

### Parameter Specifications & Weighting

| Component | Variable | Default Weight | Description |
|-----------|----------|----------------|-------------|
| **Source Authority** | $S_{\text{src}}$ | $w_{\text{src}} = 0.40$ | Publisher baseline score ($0.95$ for verified government bulletins, $0.85$ for established retail APIs, $0.60$ for unverified crowdsourced reports). |
| **Alias Precision** | $S_{\text{alias}}$ | $w_{\text{alias}} = 0.30$ | Exact dictionary match ($1.0$), localized exact alias ($0.95$), stripped phonetic match ($0.85$), partial substring match ($0.65$). |
| **Data Freshness** | $S_{\text{fresh}}$ | $w_{\text{fresh}} = 0.15$ | $S_{\text{fresh}} = \max\left(0.2, 1.0 - 0.1 \times \Delta t_{\text{days}}\right)$, penalizing stale reports. |
| **Data Completeness** | $S_{\text{cmpl}}$ | $w_{\text{cmpl}} = 0.15$ | Bonus for presence of verified spatial coordinates, full min/max price envelope, and unit certainty ($1.0$ for fully specified, $0.7$ for partial). |

$$\sum w_i = 0.40 + 0.30 + 0.15 + 0.15 = 1.00$$

---

## 4. Indexing Strategy

To support millisecond response times on time-series queries and ensure idempotent inserts:

```sql
-- Deduplication and uniqueness guard
CREATE UNIQUE INDEX idx_obs_unique 
ON price_observations(commodity_id, market_id, source_id, observation_date, price_type);

-- Time-series lookup for commodities across markets
CREATE INDEX idx_obs_commodity_date 
ON price_observations(commodity_id, observation_date DESC);

-- Market price snapshot queries
CREATE INDEX idx_obs_market_date 
ON price_observations(market_id, observation_date DESC);

-- Fast alias lookup
CREATE INDEX idx_alias_lookup 
ON commodity_aliases(alias);
```
