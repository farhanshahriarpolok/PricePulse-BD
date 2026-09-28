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
