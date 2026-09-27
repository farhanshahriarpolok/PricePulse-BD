"""
Pydantic schemas for human-in-the-loop manual field price submissions.
"""

from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class ManualObservationCreate(BaseModel):
    """Payload schema for submitting a spot market observation from the field."""

    commodity_id: int = Field(..., gt=0, description="Foreign key ID of the target canonical commodity")
    market_id: int = Field(..., gt=0, description="Foreign key ID of the physical market location")
    price: float = Field(..., gt=0.0, description="Observed transaction price in BDT")
    raw_unit: str = Field(..., min_length=1, max_length=50, description="Raw transaction unit (e.g., 'কেজি', 'হালি', 'লিটার', 'ডজন')")
    market_tier: Literal["retail", "wholesale"] = Field(
        default="retail", description="Market classification channel: 'retail' or 'wholesale'"
    )
    observation_date: Optional[date] = Field(
        default=None, description="Date of market observation (defaults to current date if omitted)"
    )
    reporter_note: Optional[str] = Field(
        default=None, max_length=500, description="Optional qualitative field observations or merchant context"
    )
    reporter_name: Optional[str] = Field(
        default=None, max_length=100, description="Optional name or identifier of field reporter"
    )

    @field_validator("raw_unit")
    @classmethod
    def validate_raw_unit(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("raw_unit cannot be empty or blank")
        return cleaned


class ManualObservationResponse(BaseModel):
    """Response payload confirming successful normalization and ingestion of field quote."""

    id: int = Field(..., description="Unique persistent ID of the price observation record")
    commodity_id: int
    commodity_name: str
    commodity_bangla_name: str
    market_id: int
    market_name: str
    district_name: Optional[str] = None
    raw_price: float
    raw_unit: str
    normalized_price: float
    normalized_unit: str
    price_type: str
    source_code: str
    source_name: str
    observation_date: date
    confidence_score: float
    reporter_note: Optional[str] = None
    created_at: datetime
    message: str = "Manual price observation recorded and normalized successfully"
