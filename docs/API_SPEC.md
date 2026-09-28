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

---

## 10. Consumer Bazaar Basket & Cost of Living Tracker

### `POST /api/v1/basket/calculate`
Calculate the optimized cost breakdown for a user-supplied market basket across wholesale, retail, and online channels.

**Request Body (JSON):**
```json
{
  "items": [
    {"commodity_id": 1, "quantity": 5, "raw_unit": "kg"},
    {"commodity_id": 3, "quantity": 2, "raw_unit": "হালি"},
    {"commodity_id": 4, "quantity": 2, "raw_unit": "liter"}
  ],
  "custom_name": "সাপ্তাহিক বাজার"
}
```

**Field Notes:**
- `commodity_id`: Canonical commodity ID from `GET /api/v1/commodities`.
- `quantity`: Numeric quantity in the specified `raw_unit`; must be > 0.
- `raw_unit`: Supports all PricePulse BD canonical units including Bangladeshi customary units (`হালি` = 4 pcs, `পোয়া` = 0.25 kg, `মণ` = 40 kg, `500ml`, `250g`, `ডজন`, etc.).

**Response (`200 OK`):**
```json
{
  "benchmark_total": 615.0,
  "wholesale_total": 540.0,
  "retail_total": 615.0,
  "online_total": 695.0,
  "best_channel": "🏪 পাইকারি বাজার",
  "max_savings_bdt": 75.0,
  "savings_explanation": "পাইকারি বাজার থেকে কিনলে আপনার ৳৭৫ বাঁচবে, আর অনলাইন থেকে কিনলে ৳৮০ বেশি লাগবে।",
  "cost_shift_7d_pct": 8.4,
  "cost_shift_7d_bdt": 47.8,
  "item_details": [
    {
      "commodity_id": 1,
      "canonical_name": "Rice (Miniket)",
      "bangla_name": "মিনিকেট চাল",
      "quantity_normalized": 5.0,
      "standard_unit": "kg",
      "unit_price": 72.0,
      "line_total": 360.0,
      "channel_prices": {
        "wholesale": 65.0,
        "retail": 72.0,
        "online": 78.0
      }
    }
  ],
  "smart_saving_tips": [
    "মিনিকেটের বদলে মোটা চাল নিলে উল্লেখযোগ্য সাশ্রয় সম্ভব।",
    "সপ্তাহের শুরুতে (শনি-রবিবার) বাজার করলে তাজা মালে ভালো দাম পাওয়া যায়।"
  ]
}
```

**Error Responses:**
- `422 Unprocessable Entity`: Empty items list or invalid quantity (≤ 0).
- `500 Internal Server Error`: Unexpected calculation failure.

---

### `GET /api/v1/basket/presets`
Returns three pre-defined Bangladeshi household market basket presets ready for direct use in the basket calculator.

**Response (`200 OK`):**
```json
{
  "total": 3,
  "presets": [
    {
      "id": "weekly_essentials",
      "name": "Middle-Class Weekly Essentials",
      "bangla_name": "সাপ্তাহিক পারিবারিক বাজার",
      "description": "Standard weekly grocery run for a 4-member middle-class household.",
      "items": [
        {"commodity_name": "Rice (Miniket)", "bangla_name": "মিনিকেট চাল", "quantity": 5, "unit": "kg"},
        {"commodity_name": "Lentils (Masur Dal)", "bangla_name": "মসুর ডাল", "quantity": 1, "unit": "kg"},
        {"commodity_name": "Onion (Local)", "bangla_name": "দেশি পেঁয়াজ", "quantity": 2, "unit": "kg"},
        {"commodity_name": "Potato (Diamond)", "bangla_name": "আলু", "quantity": 3, "unit": "kg"},
        {"commodity_name": "Soybean Oil (Bottled)", "bangla_name": "সয়াবিন তেল", "quantity": 2, "unit": "liter"},
        {"commodity_name": "Egg (Hen)", "bangla_name": "মুরগির ডিম", "quantity": 2, "unit": "হালি"}
      ]
    },
    {
      "id": "bachelor_fast_basket",
      "name": "Bachelor Fast Basket",
      "bangla_name": "ব্যাচেলর বাস্কেট",
      "description": "Minimal weekly essentials for a single working person.",
      "items": [...]
    },
    {
      "id": "family_weekend_feast",
      "name": "Family Weekend Feast",
      "bangla_name": "উইকেন্ড পারিবারিক ভোজ",
      "description": "Special weekend feast basket for a 6-member Bangladeshi family.",
      "items": [...]
    }
  ]
}
```

**Basket Calculus Engine Notes:**
- **Unit Normalization**: `হালি` → 4 pc, `পোয়া` → 0.25 kg, `মণ` → 40 kg, `500ml` → 0.5 liter (all handled by `CommodityNormalizer.normalize_unit()`).
- **Channel Imputation**: Missing channel observations are filled with the cross-channel average; online imputed at +8% premium when absent.
- **7-Day Inflation Shift**: Δ% = (Total_today − Total_t7) / Total_t7 × 100, using 14-day trailing window per commodity.
- **Performance**: <15ms end-to-end via single-pass SQL aggregation.

---

### `GET /api/v1/basket/saved`
Retrieves all persistent household baskets configured by the user, complete with real-time 3-channel market totals and 7-day / 30-day personal CPI shifts.

**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "name": "Middle-Class Weekly Essentials",
    "bangla_name": "সাপ্তাহিক পারিবারিক বাজার",
    "description": "Standard weekly grocery run for a 4-member middle-class household.",
    "item_count": 6,
    "created_at": "2026-09-28T02:00:00Z",
    "updated_at": "2026-09-28T02:00:00Z",
    "current_retail_total": 1280.0,
    "current_wholesale_total": 1095.0,
    "current_online_total": 1390.0,
    "max_savings_bdt": 185.0,
    "best_channel": "🏪 পাইকারি বাজার",
    "shift_7d_pct": 3.8,
    "shift_30d_pct": 7.4
  }
]
```

---

### `POST /api/v1/basket/saved`
Creates a new persistent household market basket with normalized line items.

**Request Payload:**
```json
{
  "name": "My Weekly Grocery",
  "bangla_name": "আমার সাপ্তাহিক বাজার",
  "description": "Family groceries for 4 members",
  "items": [
    {"commodity_id": 1, "quantity": 10.0, "unit": "kg"},
    {"commodity_id": 2, "quantity": 2.0, "unit": "kg"},
    {"commodity_id": 5, "quantity": 2.0, "unit": "liter"},
    {"commodity_id": 7, "quantity": 2.0, "unit": "kg"}
  ]
}
```

**Response (`201 Created`):**
```json
{
  "id": 2,
  "name": "My Weekly Grocery",
  "bangla_name": "আমার সাপ্তাহিক বাজার",
  "description": "Family groceries for 4 members",
  "created_at": "2026-09-28T04:15:00Z",
  "updated_at": "2026-09-28T04:15:00Z",
  "calculation": {
    "benchmark_total": 1640.0,
    "wholesale_total": 1415.0,
    "retail_total": 1640.0,
    "online_total": 1780.0,
    "best_channel": "🏪 পাইকারি বাজার",
    "max_savings_bdt": 225.0,
    "savings_explanation": "পাইকারি বাজার থেকে কিনলে আপনার ৳২২৫ বাঁচবে।",
    "cost_shift_7d_pct": 4.2,
    "cost_shift_7d_bdt": 66.0,
    "item_details": [...],
    "smart_saving_tips": [...]
  },
  "items": [
    {
      "id": 5,
      "commodity_id": 1,
      "canonical_name": "Rice (Miniket)",
      "bangla_name": "মিনিকেট চাল",
      "quantity": 10.0,
      "unit": "kg",
      "quantity_normalized": 10.0,
      "standard_unit": "kg",
      "unit_price": 72.0,
      "line_total": 720.0
    }
  ]
}
```

---

### `GET /api/v1/basket/saved/{id}/trend`
Computes the 30-day personal Consumer Price Index (CPI) inflation trajectory, historical price extrema, and volatility metrics ($CV\%$) for a specific saved basket.

**Response (`200 OK`):**
```json
{
  "basket_id": 1,
  "basket_name": "Middle-Class Weekly Essentials",
  "bangla_name": "সাপ্তাহিক পারিবারিক বাজার",
  "item_count": 6,
  "current_cost": 1280.0,
  "baseline_30d_avg": 1210.5,
  "inflation_30d_pct": 5.74,
  "inflation_7d_pct": 3.80,
  "cheapest_date": "2026-08-30",
  "cheapest_cost": 1180.0,
  "peak_date": "2026-09-25",
  "peak_cost": 1310.0,
  "volatility_cv": 3.42,
  "trend_points": [
    {
      "date": "2026-08-30",
      "retail_total": 1180.0,
      "wholesale_total": 1010.0,
      "online_total": 1285.0,
      "is_anomaly_day": false
    },
    {
      "date": "2026-09-28",
      "retail_total": 1280.0,
      "wholesale_total": 1095.0,
      "online_total": 1390.0,
      "is_anomaly_day": false
    }
  ],
  "academic_narrative": "Over the past 30 days, this consumer basket demonstrated a moderate personal inflation increase of +5.74% (baseline avg: ৳1,210.50). The basket reached its lowest expenditure of ৳1,180.00 on 2026-08-30 and peaked at ৳1,310.00 on 2026-09-25. The 30-day Coefficient of Variation stands at 3.42%."
}
```

---

## 11. Spatial Arbitrage & Highway Transit Corridors API

### `GET /api/v1/locations/arbitrage`
Evaluates freight-adjusted inter-district spatial arbitrage opportunities between surplus production hubs (Bogura, Rangpur, Jashore, Rajshahi, Dinajpur) and deficit consumption hubs (Dhaka, Chattogram, Sylhet).

Incorporates realistic highway circuity ($\kappa = 1.25$), commercial truck cruising speed ($45\text{ km/h}$), intermediate transit waypoints, and river crossing toll buffers (Bangabandhu Jamuna Bridge, Padma Multipurpose Bridge).

**Query Parameters:**
- `commodity_id` (required, string/int): Canonical commodity ID or slug (e.g., `1` or `onion-local`).
- `date` (optional, string `YYYY-MM-DD`): Target observation date (defaults to latest available date).

**Response (`200 OK`):**
```json
{
  "commodity_id": 2,
  "canonical_name": "Onion (Local)",
  "bangla_name": "দেশি পেঁয়াজ",
  "unit": "kg",
  "observation_date": "2026-09-28",
  "spatial_dispersion_index": 0.1845,
  "inter_district_cv_pct": 18.45,
  "production_hubs": ["Bogura", "Rangpur", "Jashore", "Rajshahi", "Dinajpur"],
  "consumption_hubs": ["Dhaka", "Chattogram", "Sylhet"],
  "routes": [
    {
      "source_district": "Bogura",
      "destination_district": "Dhaka",
      "source_market": "Raja Bazar Bogura",
      "destination_market": "Karwan Bazar",
      "source_price": 64.0,
      "destination_price": 98.0,
      "gross_spread_bdt": 34.0,
      "distance_km": 228.4,
      "estimated_freight_cost_bdt": 6.11,
      "net_arbitrage_margin_bdt": 27.89,
      "roi_percentage": 39.78,
      "economic_feasibility": "Highly Feasible",
      "waypoints": [
        [24.8465, 89.3770],
        [24.4534, 89.7006],
        [24.3980, 89.7800],
        [24.2513, 89.9167],
        [24.0023, 90.4264],
        [23.8103, 90.4125]
      ],
      "transit_hours_estimated": 6.3,
      "toll_and_buffer_cost_bdt": 0.50,
      "freight_breakdown": {
        "base_freight": 5.61,
        "toll_buffer": 0.50,
        "total_freight": 6.11,
        "gross_spread": 34.0,
        "net_margin": 27.89
      },
      "corridor_name": "বগুড়া ➔ ঢাকা উত্তরবঙ্গ হাইওয়ে (N5 Jamuna Corridor)"
    },
    {
      "source_district": "Jashore",
      "destination_district": "Dhaka",
      "source_market": "Boro Bazar Jashore",
      "destination_market": "Karwan Bazar",
      "source_price": 70.0,
      "destination_price": 98.0,
      "gross_spread_bdt": 28.0,
      "distance_km": 204.2,
      "estimated_freight_cost_bdt": 5.78,
      "net_arbitrage_margin_bdt": 22.22,
      "roi_percentage": 29.32,
      "economic_feasibility": "Highly Feasible",
      "waypoints": [
        [23.1664, 89.2081],
        [23.4400, 89.4200],
        [23.6071, 89.8429],
        [23.4900, 90.1600],
        [23.4500, 90.2600],
        [23.6500, 90.3500],
        [23.8103, 90.4125]
      ],
      "transit_hours_estimated": 5.3,
      "toll_and_buffer_cost_bdt": 0.60,
      "freight_breakdown": {
        "base_freight": 5.18,
        "toll_buffer": 0.60,
        "total_freight": 5.78,
        "gross_spread": 28.0,
        "net_margin": 22.22
      },
      "corridor_name": "যশোর ➔ ঢাকা পদ্মা এক্সপ্রেসওয়ে (N8 Corridor)"
    }
  ],
  "recommendation": "Spatial arbitrage between surplus production hubs and metropolitan consumption hubs is economically viable on 12 of 15 tracked highway corridors."
}
```

**Field Descriptions:**
- `economic_feasibility`:
  - `Highly Feasible`: Net margin $M_{\text{net}} \ge 6.00\text{ BDT/kg}$.
  - `Marginal`: $2.00 \le M_{\text{net}} < 6.00\text{ BDT/kg}$.
  - `Infeasible`: $M_{\text{net}} < 2.00\text{ BDT/kg}$.
- `transit_hours_estimated`: Truck transit duration calculated as $\frac{d_{\text{road}}}{45} + \text{Buffer Hours}$.
- `toll_and_buffer_cost_bdt`: Critical river crossing and toll fee per kilogram (e.g. ৳0.50 for Bangabandhu Jamuna Bridge, ৳0.60 for Padma Multipurpose Bridge).
- `waypoints`: Sequential latitude/longitude coordinate pairs along the designated national highway corridor polyline, optimized for direct Leaflet `<Polyline>` rendering.
