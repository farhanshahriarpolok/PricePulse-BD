"""
Pydantic schemas for the Consumer Bazaar Basket calculus engine.

Covers: basket item input, channel cost breakdowns, per-item cost details,
and the full optimized basket response with savings explanations.
"""

from typing import Optional
from pydantic import BaseModel, Field


class BasketItemInput(BaseModel):
    """Single line-item in a user's market basket request."""

    commodity_id: int = Field(..., description="Canonical commodity ID from the PricePulse taxonomy")
    quantity: float = Field(..., gt=0, description="Numeric quantity in the specified raw unit")
    raw_unit: str = Field(..., description="Unit label (e.g. 'kg', 'liter', 'হালি', 'পিস', 'পোয়া')")


class BasketCalculationRequest(BaseModel):
    """User-supplied market basket for cost optimization analysis."""

    items: list[BasketItemInput] = Field(..., min_length=1, description="List of basket line-items")
    custom_name: Optional[str] = Field(None, max_length=120, description="Optional user-defined basket label")


class ChannelCostBreakdown(BaseModel):
    """Total cost and savings summary for a single procurement channel."""

    channel_name: str = Field(..., description="Human-readable channel label (e.g. 'Wholesale Hub')")
    total_cost: float = Field(..., description="Total basket cost via this channel in BDT")
    savings_vs_retail: float = Field(
        ...,
        description="BDT saved relative to local retail baseline (negative means premium over retail)",
    )
    difference_pct: float = Field(
        ...,
        description="Percentage difference vs retail baseline (negative = cheaper, positive = pricier)",
    )


class BasketItemCostDetail(BaseModel):
    """Per-commodity cost breakdown and channel price map for one basket line-item."""

    commodity_id: int
    canonical_name: str
    bangla_name: str
    quantity_normalized: float = Field(..., description="Quantity expressed in the commodity's canonical base unit")
    standard_unit: str = Field(..., description="Base metric unit after normalization (kg / liter / pc)")
    unit_price: float = Field(..., description="Retail benchmark price per standard unit in BDT")
    line_total: float = Field(..., description="Retail benchmark cost for this line-item (unit_price × qty)")
    channel_prices: dict = Field(
        ...,
        description="Map of channel → price_per_unit for wholesale, retail, online channels",
    )


class PriceAlternativeOut(BaseModel):
    """Empirical cheaper alternative recommendation for a commodity."""

    source_commodity_id: int = Field(..., description="ID of the original basket commodity")
    source_commodity_name: str = Field(..., description="Canonical name of original commodity")
    source_bangla_name: str = Field(..., description="Bangla name of original commodity")
    source_price: float = Field(..., description="Observed price per standard unit of original commodity")

    alternative_commodity_id: int = Field(..., description="ID of the suggested substitute commodity")
    alternative_commodity_name: str = Field(..., description="Canonical name of alternative commodity")
    alternative_bangla_name: str = Field(..., description="Bangla name of alternative commodity")
    alternative_price: float = Field(..., description="Observed price per standard unit of alternative commodity")

    standard_unit: str = Field(..., description="Common standardized unit for comparison")
    savings_per_unit: float = Field(..., description="Absolute savings per unit in BDT")
    savings_percent: float = Field(..., description="Percentage savings relative to original price")

    basket_quantity: Optional[float] = Field(None, description="Normalized quantity in user basket")
    estimated_line_savings: Optional[float] = Field(None, description="Projected savings for user basket line in BDT")

    # Dual-sided freshness tracking (Phase 5B Hardened)
    source_observation_date: str = Field(..., description="ISO observation date of the source commodity price")
    source_freshness_tier: str = Field("FRESH_TODAY", description="Freshness tier of source price: FRESH_TODAY, YESTERDAY, or STALE")
    alternative_observation_date: str = Field(..., description="ISO observation date of the alternative commodity price")
    alternative_freshness_tier: str = Field("FRESH_TODAY", description="Freshness tier of alternative price: FRESH_TODAY, YESTERDAY, or STALE")
    is_symmetric_freshness: bool = Field(True, description="True if both source and alternative prices originate from the exact same observation date")

    # Backward compatibility fields (synced with alternative observation)
    observation_date: str = Field(..., description="ISO observation date of the alternative price")
    freshness_tier: str = Field("FRESH_TODAY", description="Freshness tier: FRESH_TODAY, YESTERDAY, or STALE")
    provenance_status: str = Field("LIVE", description="Collection provenance: LIVE or FALLBACK")
    channel: str = Field("retail", description="Comparison channel (retail or wholesale)")
    reason_bn: str = Field(..., description="Bangla context/reason for alternative")
    reason_en: str = Field(..., description="English context/reason for alternative")


class BasketCalculationResponse(BaseModel):
    """Full optimized basket cost analysis with channel savings and smart tips."""

    benchmark_total: float = Field(..., description="Standard local retail basket total in BDT")
    wholesale_total: float = Field(..., description="Estimated total if sourced from wholesale hub in BDT")
    retail_total: float = Field(..., description="Wet-market retail basket total in BDT")
    online_total: float = Field(..., description="Online / super-shop basket total in BDT")

    best_channel: str = Field(..., description="Channel name offering the lowest total cost")
    max_savings_bdt: float = Field(
        ...,
        description="Maximum BDT saved versus retail benchmark by choosing the best channel",
    )
    savings_explanation: str = Field(
        ...,
        description="Plain Bengali-language savings summary for the household",
    )

    cost_shift_7d_pct: float = Field(
        ...,
        description="Net personal inflation shift vs 7 days ago (Δ% for this exact basket composition)",
    )
    cost_shift_7d_bdt: float = Field(
        ...,
        description="Absolute BDT change of this basket vs 7 days ago",
    )

    item_details: list[BasketItemCostDetail] = Field(..., description="Per-commodity cost and channel breakdown")
    smart_saving_tips: list[str] = Field(
        ...,
        description="Actionable Bengali-language procurement suggestions",
    )
    price_alternatives: list[PriceAlternativeOut] = Field(
        default_factory=list,
        description="Empirical, verified cheaper substitute opportunities for items in this basket",
    )


# ---------------------------------------------------------------------------
# Saved Basket & Personal Inflation Tracking Schemas
# ---------------------------------------------------------------------------

class SavedBasketItemCreate(BaseModel):
    """Line-item payload when saving a customized consumer basket."""

    commodity_id: int = Field(..., description="Canonical commodity ID")
    quantity: float = Field(..., gt=0, description="Quantity in customary unit")
    unit: str = Field(..., description="Customary or metric unit label")


class SavedBasketCreate(BaseModel):
    """Payload for creating a persistent saved basket."""

    name: str = Field(..., min_length=1, max_length=120, description="Name for the personal basket")
    bangla_name: Optional[str] = Field(None, max_length=120, description="Bengali label (optional)")
    description: Optional[str] = Field(None, max_length=255, description="Personal note or purpose")
    items: list[SavedBasketItemCreate] = Field(..., min_length=1, description="Basket items")


class SavedBasketItemOut(BaseModel):
    """Detailed item output in a saved basket."""

    id: int
    commodity_id: int
    canonical_name: str
    bangla_name: str
    quantity: float
    unit: str
    quantity_normalized: float
    standard_unit: str
    unit_price: float
    line_total: float


class SavedBasketSummaryOut(BaseModel):
    """Summary overview of a saved household basket."""

    id: int
    name: str
    bangla_name: Optional[str] = None
    description: Optional[str] = None
    item_count: int
    created_at: str
    updated_at: str
    current_retail_total: float
    current_wholesale_total: float
    current_online_total: float
    max_savings_bdt: float
    best_channel: str
    shift_7d_pct: float
    shift_30d_pct: float


class SavedBasketDetailOut(BaseModel):
    """Full detail of a saved basket with items and channel breakdown."""

    id: int
    name: str
    bangla_name: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    updated_at: str
    calculation: BasketCalculationResponse
    items: list[SavedBasketItemOut]


class BasketTrendPoint(BaseModel):
    """Single chronological day in the 30-day basket trajectory."""

    date: str
    retail_total: float
    wholesale_total: float
    online_total: float
    is_anomaly_day: bool = False


class BasketTrendResponse(BaseModel):
    """30-day personal CPI inflation trajectory and volatility metrics."""

    basket_id: int
    basket_name: str
    bangla_name: Optional[str] = None
    item_count: int
    current_cost: float
    baseline_30d_avg: float
    inflation_30d_pct: float
    inflation_7d_pct: float
    cheapest_date: str
    cheapest_cost: float
    peak_date: str
    peak_cost: float
    volatility_cv: float
    trend_points: list[BasketTrendPoint]
    academic_narrative: str

