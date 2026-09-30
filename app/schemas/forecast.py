"""
app/schemas/forecast.py
=======================
Pydantic v2 schemas for Phase 3 commodity price forecasting,
channel-separated time series, rolling backtest results, and direction signals.
"""

from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DailyForecastPoint(BaseModel):
    """Single-day forecast point within the 7-day horizon."""
    day_offset: int = Field(..., ge=1, le=7, description="Day offset into future (1 to 7)")
    target_date: Optional[date] = Field(None, description="Projected calendar date")
    predicted_price_bdt: float = Field(..., description="Point forecast in BDT")
    lower_bound_bdt: float = Field(..., description="Lower confidence/error bound (95%)")
    upper_bound_bdt: float = Field(..., description="Upper confidence/error bound (95%)")


class ModelBacktestMetric(BaseModel):
    """Out-of-sample backtest score for a single candidate model."""
    model_name: str = Field(..., description="Candidate model identifier (e.g., NAIVE, SMA_7, SMA_14, ARIMA_1_1_0)")
    is_selected: bool = Field(False, description="True if chosen as the winning model")
    windows_evaluated: int = Field(..., description="Number of rolling 7-day validation windows")
    mae_bdt: float = Field(..., description="Mean Absolute Error in BDT")
    rmse_bdt: float = Field(..., description="Root Mean Squared Error in BDT")
    mape_pct: Optional[float] = Field(None, description="Mean Absolute Percentage Error (%)")
    fit_successful: bool = Field(True, description="False if model fitting encountered an exception")


class DataEligibilityDetail(BaseModel):
    """Provenance and data sufficiency telemetry for the series."""
    eligible: bool = Field(..., description="True if series has enough continuous historical data")
    observation_count: int = Field(..., description="Total empirical observations utilized")
    distinct_dates_count: int = Field(..., description="Distinct dates in historical training series")
    date_start: Optional[date] = Field(None, description="Earliest observation date")
    date_end: Optional[date] = Field(None, description="Latest observation date")
    longest_daily_streak: int = Field(0, description="Longest consecutive daily observation run")
    modeled_observations_excluded: int = Field(0, description="Count of modeled records rejected (e.g. PANDAMART)")
    reason: Optional[str] = Field(None, description="Failure reason if ineligible")


class SeriesScopeMetadata(BaseModel):
    """Channel and geographic context of the forecast series."""
    scope: str = Field(..., description="'national' or 'market'")
    channel: str = Field("all", description="'wholesale', 'retail', 'online', or 'all'")
    market_id: Optional[int] = Field(None, description="Physical market ID if market-level")
    market_name: Optional[str] = Field(None, description="Market name if market-level")
    district_name: Optional[str] = Field(None, description="District name if market-level")


class DirectionSignalDetail(BaseModel):
    """Directional classification derived from forecast and volatility."""
    direction: str = Field(..., description="'UP', 'DOWN', 'STABLE', or 'UNAVAILABLE'")
    recent_change_pct: float = Field(..., description="7-day projected price delta (%)")
    base_threshold_pct: float = Field(3.0, description="Base direction deadband (±3.0%)")
    historical_cv_pct: float = Field(0.0, description="14-day price volatility coefficient of variation")
    effective_threshold_pct: float = Field(3.0, description="Volatility-modulated deadband threshold (%)")
    direction_summary: str = Field(..., description="Human-readable plain language explanation")


class ForecastSummaryDetail(BaseModel):
    """Forecast metrics and point estimates."""
    horizon_days: int = Field(7, description="Forecast horizon (strictly 7 days)")
    selected_model: str = Field(..., description="Winning model name")
    candidate_models: List[str] = Field(default_factory=list, description="All evaluated candidate models")
    selection_metric: str = Field("MAE", description="Metric used to select model (MAE)")
    fallback_reason: Optional[str] = Field(None, description="Reason if formal ARIMA fell back to baseline")
    interval_method: str = Field(..., description="Methodology used to calculate prediction interval")
    current_observed_price_bdt: float = Field(..., description="Latest empirical baseline price")
    forecast_day7_bdt: float = Field(..., description="Day 7 point forecast in BDT")
    forecast_day7_lower_bdt: float = Field(..., description="Day 7 lower bound in BDT")
    forecast_day7_upper_bdt: float = Field(..., description="Day 7 upper bound in BDT")
    daily_schedule: List[DailyForecastPoint] = Field(default_factory=list, description="Day 1..7 projections")


class CommodityForecastResponse(BaseModel):
    """Complete consumer + research response contract for commodity forecasting."""
    commodity_id: int
    canonical_name: str
    bangla_name: Optional[str] = None
    calculation_unit: str = Field("kg", description="Canonical commodity unit")
    status: str = Field(..., description="'FORECAST', 'INSUFFICIENT_DATA', or 'UNAVAILABLE'")
    series_metadata: SeriesScopeMetadata
    data_eligibility: DataEligibilityDetail
    direction_signal: DirectionSignalDetail
    forecast_detail: Optional[ForecastSummaryDetail] = None
    backtest_metrics: List[ModelBacktestMetric] = Field(default_factory=list)
