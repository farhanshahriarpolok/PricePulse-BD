# PricePulse BD REST API Specification

## 1. Overview & Mobile Readiness

The PricePulse BD API serves normalized commodity prices and spatial market hierarchies over standard HTTP/JSON. The interface is designed to support both modern responsive web applications and native Android clients (Retrofit + Kotlinx Serialization / Gson).

- **Base URL**: `/api/v1`
- **Protocol**: HTTP/1.1 or HTTP/2, JSON UTF-8
- **Error Format**: RFC 7807 Problem Details compliant JSON
- **Date Format**: ISO 8601 extended format (`YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`)

---

## 2. API Endpoints

### 2.1 Commodities Catalog

#### `GET /api/v1/commodities`
Retrieves all registered canonical commodities with localized names and categories.

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
      "canonical_name": "Rice (Miniket)",
      "bangla_name": "মিনিকেট চাল",
      "category": "Grains",
      "default_unit": "kg"
    }
  ]
}
```

---

### 2.2 Markets & Spatial Hierarchy

#### `GET /api/v1/markets`
Retrieves physical and online retail/wholesale markets across administrative divisions.

**Query Parameters:**
- `division` (optional, string): Filter by division name (e.g., `Dhaka`, `Chittagong`).
- `market_type` (optional, string): Filter by type (`wholesale`, `retail`, `online`).

**Response (`200 OK`):**
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "name": "Karwan Bazar",
      "bangla_name": "কারওয়ান বাজার",
      "market_type": "wholesale",
      "district": "Dhaka",
      "division": "Dhaka",
      "coordinates": {
        "latitude": 23.7516,
        "longitude": 90.3944
      }
    },
    {
      "id": 2,
      "name": "Khatunganj",
      "bangla_name": "খাতুনগঞ্জ",
      "market_type": "wholesale",
      "district": "Chattogram",
      "division": "Chittagong",
      "coordinates": {
        "latitude": 22.3362,
        "longitude": 91.8365
      }
    }
  ]
}
```

---

### 2.3 Latest Price Observations

#### `GET /api/v1/prices/latest`
Returns the most recent price observation for a commodity, optionally scoped to a market.

**Query Parameters:**
- `commodity_id` (required, integer): Canonical commodity ID.
- `market_id` (optional, integer): Specific market ID.

**Response (`200 OK`):**
```json
{
  "commodity_id": 1,
  "canonical_name": "Onion (Local)",
  "bangla_name": "দেশি পেঁয়াজ",
  "observation_date": "2026-09-27",
  "prices": [
    {
      "market_id": 1,
      "market_name": "Karwan Bazar",
      "price_type": "retail_avg",
      "normalized_price": 95.0,
      "normalized_unit": "kg",
      "currency": "BDT",
      "confidence_score": 0.92,
      "source_name": "Department of Agricultural Marketing"
    }
  ]
}
```

---

### 2.4 Time-Series Price History

#### `GET /api/v1/prices/history`
Returns historical price time-series for trend graphing in web and Android charting libraries (e.g., MPAndroidChart).

**Query Parameters:**
- `commodity_id` (required, integer): Canonical commodity ID.
- `market_id` (optional, integer): Target market ID.
- `start_date` (required, string, `YYYY-MM-DD`): Start date.
- `end_date` (optional, string, `YYYY-MM-DD`): End date (defaults to current date).

**Response (`200 OK`):**
```json
{
  "commodity_id": 1,
  "canonical_name": "Onion (Local)",
  "market_id": 1,
  "market_name": "Karwan Bazar",
  "series": [
    {
      "date": "2026-09-20",
      "retail_avg": 90.0,
      "wholesale_avg": 82.5,
      "confidence": 0.91
    },
    {
      "date": "2026-09-27",
      "retail_avg": 95.0,
      "wholesale_avg": 86.0,
      "confidence": 0.93
    }
  ]
}
```

---

### 2.5 Ingestion Trigger (Administrative)

#### `POST /api/v1/ingest/trigger`
Triggers an asynchronous harvest run for a specified source collector.

**Request Body:**
```json
{
  "source_code": "DAM_DAILY",
  "force_refresh": false
}
```

**Response (`202 Accepted`):**
```json
{
  "status": "queued",
  "job_id": "ingest_dam_20260928_01",
  "message": "Collector DAM_DAILY dispatched successfully."
}
```

---

## 3. Error Contract

When a request encounters an error, the API responds with standard HTTP status codes and a structured body:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Commodity with id 999 does not exist.",
    "status": 404,
    "timestamp": "2026-09-28T01:50:00Z"
  }
}
```
