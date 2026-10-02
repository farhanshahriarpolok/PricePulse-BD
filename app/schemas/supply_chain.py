"""
Pydantic v2 schemas for Supply Chain Price Gap Deconstruction (Phase 5C).
Maintains strict separation between directly observed price data,
official regulatory parameters, and explicitly modeled economic assumptions.
"""

from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ProvenanceType(str, Enum):
    """Classification of data certainty and legal/empirical backing."""
    OBSERVED = "OBSERVED"
    OFFICIAL = "OFFICIAL"
    MODELED_ASSUMPTION = "MODELED_ASSUMPTION"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class SpreadStatus(str, Enum):
    """Economic categorization of the wholesale-to-retail spread."""
    NORMAL_SPREAD = "NORMAL_SPREAD"
    COMPRESSED_MARGIN = "COMPRESSED_MARGIN"
    EXPANDED_SPREAD = "EXPANDED_SPREAD"


class SupplyChainComponent(BaseModel):
    """
    Granular cost component within the wholesale-to-retail spread.
    Every component must declare its provenance type, source, and methodology note.
    """
    name: str = Field(description="Component name in English")
    bangla_name: str = Field(description="Component name in Bengali")
    value_bdt: float = Field(description="Calculated cost or margin in BDT per canonical unit")
    percentage_of_spread: Optional[float] = Field(
        default=None, description="Share of the gross spread represented by this component (can be None or negative if compressed)"
    )
    percentage_of_retail: Optional[float] = Field(
        default=None, description="Share of the retail price represented by this component"
    )
    unit: str = Field(description="Canonical metric unit (e.g., kg, liter, pc)")
    provenance_type: ProvenanceType = Field(
        description="OBSERVED | OFFICIAL | MODELED_ASSUMPTION | NOT_AVAILABLE"
    )
    source_name: str = Field(description="Primary institution, gazette, or literature citation")
    source_reference: Optional[str] = Field(
        default=None, description="Specific gazette number, study citation, or model reference"
    )
    methodology_note: Optional[str] = Field(
        default=None, description="Plain-language description of how this value was computed or modeled"
    )


class SupplyChainDeconstructionResponse(BaseModel):
    """
    Complete Supply Chain Price Gap Deconstruction shape.
    Surfaces observed benchmark prices alongside modeled intermediary cost assumptions.
    """
    commodity_id: int
    canonical_name: str
    bangla_name: str
    category: str
    calculation_unit: str = Field(description="Canonical metric unit for all rates (kg/liter/pc)")

    # Directly Observed Benchmarks
    wholesale_price: Optional[float] = Field(
        default=None, description="Empirically observed wholesale benchmark price (BDT/unit)"
    )
    retail_price: Optional[float] = Field(
        default=None, description="Empirically observed retail kitchen market price (BDT/unit)"
    )
    gross_spread_bdt: Optional[float] = Field(
        default=None, description="Observed price gap = retail_price - wholesale_price"
    )
    gross_spread_pct: Optional[float] = Field(
        default=None, description="Spread as a percentage of the wholesale price"
    )

    # Location & Market Names
    wholesale_market_name: Optional[str] = Field(default=None)
    retail_market_name: Optional[str] = Field(default=None)
    source_district: Optional[str] = Field(default=None)
    destination_district: Optional[str] = Field(default=None)
    corridor_name: Optional[str] = Field(default=None)
    corridor_distance_km: Optional[float] = Field(default=None)

    # Temporal & Freshness Metadata
    wholesale_observation_date: Optional[date] = Field(default=None)
    retail_observation_date: Optional[date] = Field(default=None)
    wholesale_freshness_tier: Optional[str] = Field(
        default=None, description="FRESH_TODAY | YESTERDAY | STALE"
    )
    retail_freshness_tier: Optional[str] = Field(
        default=None, description="FRESH_TODAY | YESTERDAY | STALE"
    )
    is_symmetric_freshness: bool = Field(
        default=True, description="True if both wholesale and retail dates match calendar date"
    )
    temporal_divergence_days: int = Field(
        default=0, description="Calendar day gap between wholesale and retail observations"
    )

    # Deconstructed Totals
    observed_or_supported_costs_bdt: float = Field(
        default=0.0, description="Sum of supported freight and direct logistical costs (BDT/unit)"
    )
    modeled_costs_bdt: float = Field(
        default=0.0, description="Sum of modeled arath, handling, and spoilage assumptions (BDT/unit)"
    )
    residual_spread_bdt: Optional[float] = Field(
        default=None,
        description="gross_spread - observed_costs - modeled_costs. Preserves negative values if compressed.",
    )
    spread_status: SpreadStatus = Field(
        default=SpreadStatus.NORMAL_SPREAD,
        description="NORMAL_SPREAD | COMPRESSED_MARGIN | EXPANDED_SPREAD",
    )
    margin_compression_bdt: Optional[float] = Field(
        default=None,
        description="Amount in BDT by which intermediate costs exceed gross spread (populated when residual < 0)",
    )

    # Itemized Components
    components: List[SupplyChainComponent] = Field(
        default_factory=list, description="Itemized cost components with strict provenance labels"
    )

    # Provenance Disclaimer
    methodology_disclaimer: str = Field(
        default=(
            "Observed prices and road distances reflect empirical collection. "
            "Intermediary arathdar commission, handling tolls, and transit wastage are modeled "
            "economic assumptions from published agricultural research, not audited merchant accounts."
        ),
        description="Mandatory methodological disclosure separating observed facts from modeled assumptions",
    )
