"""
Pydantic schemas for realtime on-demand search and market pulse endpoints.
"""

import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import FreshnessMetadata
from app.schemas.observation import (
    PriceObservationOut,
    PriceSummaryOut,
    ChannelComparisonOut,
)


class RealtimePriceQuery(BaseModel):
    query: str = Field(..., description="Commodity search keyword in English or Bengali")
    target_date: Optional[dt.date] = Field(None, alias="date", description="Target observation date (defaults to today)")


class RealtimePriceResponse(BaseModel):
    query: str
    canonical_name: str
    bangla_name: str
    category: str
    unit: str
    observation_date: dt.date
    price_summary: PriceSummaryOut
    channels: ChannelComparisonOut
    price_status: str
    freshness: FreshnessMetadata
    observations: List[PriceObservationOut]


class DailyPulseItem(BaseModel):
    commodity_id: int
    canonical_name: str
    bangla_name: str
    category: str
    unit: str
    price_summary: PriceSummaryOut
    channels: ChannelComparisonOut
    price_status: str
    freshness: FreshnessMetadata


class DailyPulseResponse(BaseModel):
    date: dt.date
    total_tracked: int
    items: List[DailyPulseItem]
