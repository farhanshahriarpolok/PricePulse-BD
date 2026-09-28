"""
Pydantic schemas for spatial market dispersion and GeoJSON representations.
"""

import datetime as dt
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MarketPricePoint(BaseModel):
    market_id: int
    market_name: str
    market_type: str
    district: str
    division: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    avg_price: float
    unit: str
    confidence_score: float


class DistrictAggregate(BaseModel):
    district: str
    division: str
    avg_price: float
    min_price: float
    max_price: float
    market_count: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationSpreadMetrics(BaseModel):
    cheapest_market: Optional[str] = None
    cheapest_price: Optional[float] = None
    highest_market: Optional[str] = None
    highest_price: Optional[float] = None
    absolute_spread_bdt: Optional[float] = None
    percentage_spread: Optional[float] = None
    spatial_dispersion_index: Optional[float] = None
    mean_market_price: Optional[float] = None
    std_dev_price: Optional[float] = None


class ArbitrageRoute(BaseModel):
    source_district: str
    destination_district: str
    source_market: str
    destination_market: str
    source_price: float
    destination_price: float
    gross_spread_bdt: float
    distance_km: float
    estimated_freight_cost_bdt: float
    net_arbitrage_margin_bdt: float
    roi_percentage: float
    economic_feasibility: str


class SpatialArbitrageResponse(BaseModel):
    commodity_id: int
    canonical_name: str
    bangla_name: str
    unit: str
    observation_date: dt.date
    spatial_dispersion_index: float
    inter_district_cv_pct: float
    production_hubs: List[str]
    consumption_hubs: List[str]
    routes: List[ArbitrageRoute]
    recommendation: str


class GeoSpatialPulseResponse(BaseModel):
    commodity_id: int
    canonical_name: str
    bangla_name: str
    unit: str
    date: dt.date
    spread_summary: LocationSpreadMetrics
    districts: List[DistrictAggregate]
    markets: List[MarketPricePoint]
    geojson_feature_collection: Optional[Dict[str, Any]] = Field(
        None, description="Leaflet-ready GeoJSON feature collection with district price properties"
    )


class LocationHierarchyMarket(BaseModel):
    id: int
    name: str
    bangla_name: Optional[str] = None
    market_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationHierarchyDistrict(BaseModel):
    id: int
    name: str
    bangla_name: Optional[str] = None
    markets: List[LocationHierarchyMarket]


class LocationHierarchyDivision(BaseModel):
    id: int
    name: str
    bangla_name: Optional[str] = None
    districts: List[LocationHierarchyDistrict]


class LocationHierarchyResponse(BaseModel):
    total_divisions: int
    total_districts: int
    total_markets: int
    divisions: List[LocationHierarchyDivision]
