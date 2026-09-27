# PricePulse BD REST API Specification

## 1. Architectural Overview & Mobile-First Principles

The PricePulse BD API serves normalized commodity prices, daily market intelligence pulses, and spatial market hierarchies over HTTP/JSON. The interface is optimized for high-performance consumption by:
- **Responsive Web Portals** (React, Vue, or Vanilla JS)
- **Native Android Clients** (Kotlin + Retrofit + Kotlinx Serialization / Gson)

### Protocol Conventions
- **Base URL**: `/api/v1`
- **Content-Type**: `application/json; charset=utf-8`
- **Error Standard**: RFC 7807 Problem Details compliant JSON
- **Date/Time Formatting**: ISO 8601 (`YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`)
- **Currency**: Bangladeshi Taka (`BDT`)
- **Metric Base Units**: `kg`, `liter`, `pc`

---

## 2. System Endpoints

### `GET /api/v1/health`
Verifies backend service availability and database connectivity.

**Response (`200 OK`):**
```json
{
  "status": "ok",
  "app": "PricePulse BD",
  "version": "0.2.0",
  "timestamp": "2026-09-28T02:00:00Z"
}
```

---

## 3. Realtime Price Discovery & Market Pulse

### `GET /api/v1/search/realtime`
Performs an on-demand commodity price discovery query.
> **On-Demand Fallback Invariant**: If the requested date has no recorded observations or cached data is older than 12 hours, the service automatically triggers background collectors (DAM bulletin parser and Chaldal retail collector) and serves the normalized live pulse.

**Query Parameters:**
- `query` (required, string): Commodity label in English or Bengali (e.g., `onion`, `আলু`, `মিনিকেট`).
- `date` (optional, string, `YYYY-MM-DD`): Target observation date. Defaults to today's date.

**Response (`200 OK`):**
```json
{
  "query": "onion",
  "canonical_name": "Onion (Local)",
  "bangla_name": "দেশি পেঁয়াজ",
  "category": "Vegetables",
  "unit": "kg",
  "observation_date": "2026-09-28",
  "price_summary": {
    "min_price": 82.0,
    "max_price": 110.0,
    "avg_price": 91.0,
    "currency": "BDT",
    "sample_count": 9
  },
  "channels": {
    "wholesale_avg": 86.0,
    "retail_avg": 96.5,
    "online_avg": 110.0,
    "spread_bdt": 10.5,
    "markup_percentage": 12.21
  },
  "price_status": "Normal",
  "freshness": {
    "status": "fresh",
    "last_scraped_at": "2026-09-28T02:05:00Z",
    "is_stale": false,
    "cache_age_seconds": 120
  },
  "observations": [
    {
      "id": 45,
      "commodity_name": "Onion (Local)",
      "market_name": "Karwan Bazar",
      "market_type": "wholesale",
      "source_name": "Department of Agricultural Marketing",
      "price_type": "retail_avg",
      "raw_price": 95.0,
      "raw_unit": "কেজি",
      "normalized_price": 95.0,
      "normalized_unit": "kg",
      "currency": "BDT",
      "confidence_score": 0.935,
      "observation_date": "2026-09-28",
      "scraped_at": "2026-09-28T02:05:00Z"
    },
    {
      "id": 89,
      "commodity_name": "Onion (Local)",
      "market_name": "Chaldal Online Hub",
      "market_type": "online",
      "source_name": "Chaldal Online Grocery",
      "price_type": "retail_avg",
      "raw_price": 55.0,
      "raw_unit": "500 gm",
      "normalized_price": 110.0,
      "normalized_unit": "kg",
      "currency": "BDT",
      "confidence_score": 0.8868,
      "observation_date": "2026-09-28",
      "scraped_at": "2026-09-28T02:05:00Z"
    }
  ]
}
```

---

### `GET /api/v1/pulse/today`
Returns the macro commodity pulse for all tracked daily essentials.

**Response (`200 OK`):**
```json
{
  "date": "2026-09-28",
  "total_tracked": 7,
  "items": [
    {
      "commodity_id": 1,
      "canonical_name": "Onion (Local)",
      "bangla_name": "দেশি পেঁয়াজ",
      "category": "Vegetables",
      "unit": "kg",
      "price_summary": {
        "min_price": 82.0,
        "max_price": 110.0,
        "avg_price": 91.0,
        "currency": "BDT",
        "sample_count": 9
      },
      "channels": {
        "wholesale_avg": 86.0,
        "retail_avg": 96.5,
        "online_avg": 110.0,
        "spread_bdt": 10.5,
        "markup_percentage": 12.21
      },
      "price_status": "Normal",
      "freshness": {
        "status": "fresh",
        "last_scraped_at": "2026-09-28T02:05:00Z",
        "is_stale": false,
        "cache_age_seconds": 0
      }
    }
  ]
}
```

---

## 4. Commodities Catalog & Time-Series History

### `GET /api/v1/commodities`
Lists all canonical commodities in the taxonomy.

**Query Parameters:**
- `category` (optional, string): Filter by category (e.g., `Vegetables`, `Grains`, `Edible Oils`).

**Response (`200 OK`):**
```json
{
  "total": 4,
  "items": [
    {
      "id": 1,
      "canonical_name": "Onion (Local)",
      "bangla_name": "দেশি পেঁয়াজ",
      "category": "Vegetables",
      "default_unit": "kg"
    },
    {
      "id": 2,
      "canonical_name": "Onion (Imported)",
      "bangla_name": "আমদানি পেঁয়াজ",
      "category": "Vegetables",
      "default_unit": "kg"
    }
  ]
}
```

---

### `GET /api/v1/commodities/{id}`
Returns commodity details and all registered bilingual alias mappings.

**Response (`200 OK`):**
```json
{
  "id": 1,
  "canonical_name": "Onion (Local)",
  "bangla_name": "দেশি পেঁয়াজ",
  "category": "Vegetables",
  "default_unit": "kg",
  "aliases": [
    "দেশি পেঁয়াজ",
    "দেশি পেঁয়াজ",
    "দেশী পেঁয়াজ",
    "পেঁয়াজ (দেশি)",
    "deshi peyaj",
    "local onion",
    "onion local",
    "onion (deshi)",
    "onion deshi"
  ]
}
```

---

### `GET /api/v1/commodities/{id}/history`
Returns aggregated historical daily price curves for Android (MPAndroidChart) or Web charts.

**Query Parameters:**
- `start_date` (optional, string, `YYYY-MM-DD`)
- `end_date` (optional, string, `YYYY-MM-DD`)
- `market_id` (optional, integer)

**Response (`200 OK`):**
```json
{
  "commodity_id": 1,
  "canonical_name": "Onion (Local)",
  "unit": "kg",
  "series": [
    {
      "date": "2026-09-27",
      "avg_price": 88.5,
      "min_price": 82.0,
      "max_price": 98.0,
      "sample_count": 8
    },
    {
      "date": "2026-09-28",
      "avg_price": 91.0,
      "min_price": 82.0,
      "max_price": 110.0,
      "sample_count": 9
    }
  ]
}
```

---

## 5. Android Retrofit Integration Guide

Android mobile developers can bind these endpoints using standard Retrofit interfaces:

```kotlin
// PricePulseApi.kt
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface PricePulseApi {

    @GET("api/v1/health")
    suspend fun getHealth(): HealthResponse

    @GET("api/v1/search/realtime")
    suspend fun searchRealtime(
        @Query("query") query: String,
        @Query("date") date: String? = null
    ): RealtimePriceResponse

    @GET("api/v1/pulse/today")
    suspend fun getDailyPulse(): DailyPulseResponse

    @GET("api/v1/commodities")
    suspend fun getCommodities(
        @Query("category") category: String? = null
    ): CommodityListResponse

    @GET("api/v1/commodities/{id}/history")
    suspend fun getCommodityHistory(
        @Path("id") commodityId: Int,
        @Query("start_date") startDate: String? = null,
        @Query("end_date") endDate: String? = null
    ): CommodityHistoryResponse

    @GET("api/v1/commodities/compare")
    suspend fun compareCommodities(
        @Query("ids") ids: String,
        @Query("district_id") districtId: Int? = null
    ): ComparisonResponse

    @POST("api/v1/observations/manual")
    suspend fun submitManualObservation(
        @Body payload: ManualObservationRequest
    ): ManualObservationResponse
}
```

---

## 5. Field Ingestion & Spot Price Reporting API

### `POST /api/v1/observations/manual`
Submits a spot price observation collected from the field. Normalizes custom units (e.g. `হালি` -> 4 pcs, `ডজন` -> 12 pcs), validates bounds, assigns Tier-4 confidence (`reliability = 0.60`), and persists to SQLite WAL.

**Request Payload:**
```json
{
  "commodity_id": 8,
  "market_id": 1,
  "price": 52.0,
  "raw_unit": "হালি",
  "market_tier": "retail",
  "observation_date": "2026-09-28",
  "reporter_note": "Observed at Kawran Bazar morning shift",
  "reporter_name": "Inspector Rahim"
}
```

**Response (`201 Created`):**
```json
{
  "id": 142,
  "commodity_id": 8,
  "commodity_name": "Farm Egg",
  "commodity_bangla_name": "ফার্মের ডিম",
  "market_id": 1,
  "market_name": "Kawran Bazar Wholesale & Retail Hub",
  "district_name": "Dhaka",
  "raw_price": 52.0,
  "raw_unit": "হালি",
  "normalized_price": 13.0,
  "normalized_unit": "pc",
  "price_type": "retail_avg",
  "source_code": "field_report",
  "source_name": "Field Spot Report (Manual)",
  "observation_date": "2026-09-28",
  "confidence_score": 0.84,
  "reporter_note": "Observed at Kawran Bazar morning shift",
  "created_at": "2026-09-28T03:10:00Z",
  "message": "Manual price observation recorded and normalized successfully"
}
```

---

### `GET /api/v1/commodities/compare`
Returns side-by-side pricing, wholesale vs retail spreads, 14-day trends, and volatility metrics for comparison.

**Parameters:**
- `ids` (string, required): Comma-separated commodity IDs (e.g. `1,2,3`).
- `district_id` (integer, optional): Filter by administrative district.

**Response (`200 OK`):**
```json
{
  "total_compared": 2,
  "district_id": null,
  "items": [
    {
      "commodity_id": 1,
      "canonical_name": "Onion (Local)",
      "bangla_name": "দেশি পেঁয়াজ",
      "category": "Vegetables",
      "unit": "kg",
      "retail_price": 98.0,
      "wholesale_price": 85.0,
      "spread_bdt": 13.0,
      "spread_pct": 15.3,
      "baseline_sma_14d": 65.2,
      "delta_pct": 50.3,
      "z_score": 17.98,
      "volatility_cv": 2.8,
      "is_anomaly": true,
      "severity": "Critical",
      "direction": "Spike"
    }
  ]
}

```

---

## 6. Error Response Schema (RFC 7807)

When validation fails or an unknown resource is requested, the API returns a structured error object:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Commodity 'unknown_item' could not be resolved in the canonical taxonomy.",
    "status": 404,
    "timestamp": "2026-09-28T02:00:00Z"
  }
}
```
