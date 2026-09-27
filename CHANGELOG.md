# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
