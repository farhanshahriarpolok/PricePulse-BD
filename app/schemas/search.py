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
    observation_date: Optional[dt.date] = Field(None, description="Calendar date of the price observation")
    sparkline_7d: List[float] = Field(default_factory=list, description="Last 7 daily representative prices in chronological order")
    percentage_change_7d: float = Field(0.0, description="7-day percentage change relative to 7d SMA or start of window")
    min_price: float = Field(0.0, description="Observed daily minimum price in BDT")
    max_price: float = Field(0.0, description="Observed daily maximum price in BDT")
    wholesale_avg: Optional[float] = Field(None, description="Observed wholesale price in BDT")
    retail_avg: Optional[float] = Field(None, description="Observed physical retail price in BDT")
    online_avg: Optional[float] = Field(None, description="Observed e-commerce retail price in BDT")
    source_count: int = Field(1, description="Number of independent publisher sources")
    confidence_score: float = Field(0.9, description="Average confidence score (0.0 to 1.0)")
    volatility_cv: float = Field(0.0, description="14-day Coefficient of Variation percentage")
    z_score: float = Field(0.0, description="14-day Standard Score Z")


class DailyPulseResponse(BaseModel):
    date: dt.date
    total_tracked: int
    items: List[DailyPulseItem]
