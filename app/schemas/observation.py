"""
Pydantic schemas for price observations, channel breakdowns, and historical series.
"""

import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PriceObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commodity_name: str
    market_name: str
    market_type: Optional[str] = "retail"
    source_name: str
    price_type: str
    raw_price: float
    raw_unit: str
    normalized_price: float
    normalized_unit: str
    currency: str = "BDT"
    confidence_score: float
    observation_date: dt.date
    scraped_at: dt.datetime


class ChannelComparisonOut(BaseModel):
    wholesale_avg: Optional[float] = None
    retail_avg: Optional[float] = None
    online_avg: Optional[float] = None
    spread_bdt: Optional[float] = None
    markup_percentage: Optional[float] = None


class PriceSummaryOut(BaseModel):
    min_price: float
    max_price: float
    avg_price: float
    currency: str = "BDT"
    sample_count: int


class HistoricalPointOut(BaseModel):
    date: dt.date
    avg_price: float
    min_price: float
    max_price: float
    sample_count: int


class CommodityHistoryResponse(BaseModel):
    commodity_id: int
    canonical_name: str
    unit: str
    series: List[HistoricalPointOut]
