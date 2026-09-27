"""
Pydantic schemas for statistical anomaly detection, metric breakdowns, and plain-language explanations.
"""

import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field


class MetricBreakdown(BaseModel):
    current_price: float = Field(..., description="Observed price for the target date in BDT")
    baseline_sma_7d: Optional[float] = Field(None, description="7-day Rolling Simple Moving Average")
    baseline_sma_14d: Optional[float] = Field(None, description="14-day Rolling Simple Moving Average")
    baseline_sma_30d: Optional[float] = Field(None, description="30-day Rolling Simple Moving Average")
    std_dev_14d: Optional[float] = Field(None, description="14-day Sample Standard Deviation")
    z_score_14d: Optional[float] = Field(None, description="Standard Score (Z = (P - SMA) / StdDev)")
    percentage_change_14d: Optional[float] = Field(None, description="Percentage deviation from 14-day baseline")
    volatility_cv: Optional[float] = Field(None, description="Coefficient of Variation (StdDev / SMA * 100%)")


class AnomalyDetailOut(BaseModel):
    commodity_id: int
    canonical_name: str
    bangla_name: str
    unit: str
    observation_date: dt.date
    is_anomaly: bool
    anomaly_severity: str = Field(..., description="'Normal', 'Moderate', 'Severe', or 'Critical'")
    anomaly_direction: Optional[str] = Field(None, description="'Spike', 'Drop', or None")
    confidence_score: float
    metrics: MetricBreakdown
    explanation: str


class AnomalyMonitorResponse(BaseModel):
    date: dt.date
    total_monitored: int
    anomalies_detected: int
    anomalies: List[AnomalyDetailOut]
