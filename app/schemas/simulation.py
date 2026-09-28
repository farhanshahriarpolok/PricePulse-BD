"""
app/schemas/simulation.py
=========================
Pydantic schemas for the Viva Defense Interactive Simulation Sandbox.
Enables examiners to inject synthetic supply shocks, import duty spikes,
and transport strikes to evaluate real-time statistical anomaly recalculation.
"""

import datetime as dt
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.anomaly import MetricBreakdown


class SimulationRequest(BaseModel):
    commodity_id: int = Field(..., description="Target canonical commodity ID")
    shock_percentage: float = Field(
        ...,
        ge=-60.0,
        le=150.0,
        description="Percentage price shift injected during shock (+25% = supply disruption, -20% = bumper harvest)"
    )
    shock_duration_days: int = Field(
        default=3,
        ge=1,
        le=14,
        description="Duration of the shock window ending on the simulation date"
    )
    shock_type: str = Field(
        default="Supply Disruption",
        description="Scenario archetype: 'Supply Disruption', 'Import Tariff', 'Transport Strike', or 'Cartel Hoarding'"
    )
    baseline_adjustment_pct: float = Field(
        default=0.0,
        ge=-50.0,
        le=100.0,
        description="Pre-shock baseline price level shift (-50% to +100%)"
    )
    noise_level: float = Field(
        default=0.0,
        ge=0.0,
        le=25.0,
        description="Random volatility noise percentage injected across the series"
    )


class SimulationTimeSeriesPoint(BaseModel):
    date: str
    observed_price: float
    simulated_price: float
    baseline_sma_14d: Optional[float] = None
    is_shock_period: bool = False


class SimulationResponse(BaseModel):
    commodity_id: int
    canonical_name: str
    bangla_name: str
    unit: str
    simulation_date: dt.date
    baseline_price: float
    simulated_price: float
    shock_percentage: float
    shock_duration_days: int
    shock_type: str
    is_anomaly: bool
    anomaly_severity: str
    anomaly_direction: Optional[str]
    confidence_score: float
    metrics: MetricBreakdown
    explanation: str
    impact_assessment: str
    time_series: List[SimulationTimeSeriesPoint]
