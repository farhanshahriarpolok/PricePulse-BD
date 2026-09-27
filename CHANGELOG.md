# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-09-28

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
