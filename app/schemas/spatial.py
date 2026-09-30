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
    waypoints: List[List[float]] = Field(
        default_factory=list,
        description="Lat/Lng coordinate pairs defining the highway corridor polyline",
    )
    transit_hours_estimated: float = Field(
        default=0.0,
        description="Estimated truck transit duration including bridge crossing buffers",
    )
    toll_and_buffer_cost_bdt: float = Field(
        default=0.0,
        description="River crossing / bridge toll & bottleneck buffer cost in BDT/kg",
    )
    freight_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Granular freight cost breakdown: base_freight, toll_buffer, net_margin",
    )
    corridor_name: Optional[str] = Field(
        default=None,
        description="Designated national highway corridor (e.g., N5 Jamuna, N1 Highway, N8 Padma)",
    )
    # Phase 2 additions — unit provenance for consumer display
    calculation_unit: str = Field(
        default="kg",
        description="Canonical metric unit used for all price calculations in this route (kg/liter/pc)",
    )
    data_provenance: str = Field(
        default="FALLBACK",
        description="Data quality label for source price: LIVE | FALLBACK | MODELED | STALE",
    )



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


# ── Phase 2: Consumer-Facing Opportunity Shape ────────────────────────────────

class FreightBreakdownDetail(BaseModel):
    """Granular freight cost breakdown surfaced in the expandable research layer."""
    base_loading_bdt: float = Field(
        description="Fixed loading/handling overhead per canonical unit (BDT)"
    )
    distance_cost_bdt: float = Field(
        description="Variable distance-proportional freight cost (0.018 BDT/kg/km)"
    )
    toll_and_bridge_bdt: float = Field(
        description="River crossing / bridge toll buffer (BDT/canonical unit)"
    )
    total_freight_bdt: float = Field(
        description="Total estimated freight cost per canonical unit (BDT)"
    )
    distance_km: float = Field(description="Road-corrected transport distance (km)")
    transit_hours: float = Field(description="Estimated truck transit duration (hours)")
    corridor_name: Optional[str] = Field(
        default=None, description="National highway corridor name"
    )
    calculation_basis: str = Field(
        default="1.50 BDT fixed + 0.018 BDT/kg/km (road circuity 1.25×) + bridge toll",
        description="Plain-language formula description for the freight model",
    )


class ConsumerOpportunityResponse(BaseModel):
    """
    Consumer-first spatial opportunity shape for the hybrid Q1 UI.
    Top-level fields are human-actionable; freight_detail is the expandable research layer.
    """
    commodity_id: int
    canonical_name: str
    bangla_name: str
    calculation_unit: str = Field(
        description="Canonical metric unit for all prices in this response (kg/liter/pc)"
    )
    observation_date: dt.date

    # Consumer-layer fields (always visible)
    has_opportunity: bool = Field(
        description="True when net margin is positive and transport is economically viable"
    )
    opportunity_summary: str = Field(
        description="Plain-language human-readable summary (Bangla-first, English translation follows)"
    )
    cheapest_district: Optional[str] = Field(
        default=None, description="District where the commodity is cheapest"
    )
    cheapest_market: Optional[str] = Field(
        default=None, description="Market name at the cheapest source"
    )
    cheapest_price_bdt: Optional[float] = Field(
        default=None, description="Cheapest observed price per calculation_unit"
    )
    expensive_district: Optional[str] = Field(
        default=None, description="Destination district (consumer hub)"
    )
    expensive_market: Optional[str] = Field(
        default=None, description="Destination market name"
    )
    expensive_price_bdt: Optional[float] = Field(
        default=None, description="Destination price per calculation_unit"
    )
    gross_difference_bdt: Optional[float] = Field(
        default=None, description="Raw price difference before transport costs"
    )
    transport_cost_bdt: Optional[float] = Field(
        default=None, description="Total estimated freight cost per calculation_unit"
    )
    net_opportunity_bdt: Optional[float] = Field(
        default=None,
        description="Net opportunity = gross_difference - transport_cost. Negative means no viable opportunity.",
    )
    roi_percentage: Optional[float] = Field(
        default=None, description="Return on investment % for the arbitrage route"
    )
    economic_feasibility: Optional[str] = Field(
        default=None,
        description="Human label: Highly Feasible | Marginal | Infeasible (Transport Barrier)",
    )
    data_provenance: str = Field(
        description="Data quality label: LIVE | FALLBACK | MODELED | STALE"
    )

    # Research/detail layer (expandable)
    freight_detail: Optional[FreightBreakdownDetail] = Field(
        default=None,
        description="Detailed freight breakdown for the expandable research panel",
    )
    waypoints: List[List[float]] = Field(
        default_factory=list,
        description="Highway corridor polyline for map rendering",
    )
    spatial_dispersion_index: Optional[float] = Field(
        default=None,
        description="D(t) — coefficient of variation across all market prices",
    )
    all_routes_count: int = Field(
        default=0,
        description="Total routes evaluated (including infeasible)",
    )
    top_routes: List[ArbitrageRoute] = Field(
        default_factory=list,
        description="Top 5 routes sorted by net margin for the research accordion",
    )
