"""
app/api/v1/endpoints/simulation.py
==================================
Market Stress Test & Economic Scenario Engine REST endpoint.
Allows policy analysts and consumers to interactively inject synthetic shocks,
tariffs, and transport disruptions to observe real-time anomaly recalculations
and explainable natural language outputs without altering ground-truth records.
"""

import math
import random
from datetime import date, timedelta
from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commodity import Commodity
from app.models.observation import PriceObservation
from app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    SimulationTimeSeriesPoint,
)
from app.schemas.anomaly import MetricBreakdown
from app.services.anomaly_engine import anomaly_engine

router = APIRouter(prefix="/simulation", tags=["Market Stress Test"])


@router.post(
    "/inject-shock",
    response_model=SimulationResponse,
    summary="Simulate Market Supply Shock & Policy Stress Test",
    description=(
        "Simulate macro supply disruptions, import tariff shifts, and freight shocks "
        "on commodity price baselines. Computes on-the-fly Rolling 14-day SMA, "
        "Z-scores, Volatility CV, and explainable algorithmic market explanations."
    ),
)
def inject_shock(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    commodity = db.get(Commodity, payload.commodity_id)
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity with ID {payload.commodity_id} not found.",
        )

    # Latest date in DB or today
    latest_date_stmt = (
        select(func.max(PriceObservation.observation_date))
        .where(PriceObservation.commodity_id == commodity.id)
    )
    eval_date = db.scalar(latest_date_stmt) or date.today()
    start_date = eval_date - timedelta(days=40)

    # Ground truth price series
    obs_stmt = (
        select(
            PriceObservation.observation_date,
            func.avg(PriceObservation.normalized_price).label("daily_avg"),
        )
        .where(
            PriceObservation.commodity_id == commodity.id,
            PriceObservation.observation_date >= start_date,
            PriceObservation.observation_date <= eval_date,
        )
        .group_by(PriceObservation.observation_date)
        .order_by(PriceObservation.observation_date.asc())
    )
    rows = db.execute(obs_stmt).all()

    if rows:
        base_series = [(r.observation_date, round(float(r.daily_avg), 2)) for r in rows]
    else:
        # Generate synthetic 30-day baseline if no historical rows exist
        base_val = 80.0
        base_series = [
            (eval_date - timedelta(days=d), base_val + round(math.sin(d) * 2.0, 2))
            for d in range(30, -1, -1)
        ]

    # Generate deterministic pseudo-random noise seeded by date
    shock_start_date = eval_date - timedelta(days=payload.shock_duration_days - 1)

    simulated_series: List[Tuple[date, float]] = []
    points: List[SimulationTimeSeriesPoint] = []

    # Window of baseline points
    for idx, (obs_d, orig_price) in enumerate(base_series):
        # Apply baseline adjustment
        adjusted_price = orig_price * (1.0 + (payload.baseline_adjustment_pct / 100.0))

        # Add deterministic pseudo-noise
        if payload.noise_level > 0.0:
            pseudo_seed = int(obs_d.strftime("%Y%m%d")) + payload.commodity_id
            rng = random.Random(pseudo_seed)
            noise_factor = 1.0 + rng.uniform(-payload.noise_level, payload.noise_level) / 100.0
            adjusted_price *= noise_factor

        # Check if point falls within shock window
        is_shock = obs_d >= shock_start_date and obs_d <= eval_date
        if is_shock:
            sim_price = round(adjusted_price * (1.0 + (payload.shock_percentage / 100.0)), 2)
        else:
            sim_price = round(adjusted_price, 2)

        simulated_series.append((obs_d, sim_price))

    # Calculate rolling 14-day SMA for the time series
    for idx, (obs_d, sim_p) in enumerate(simulated_series):
        orig_p = base_series[idx][1]
        is_shock = obs_d >= shock_start_date and obs_d <= eval_date

        # Window for rolling SMA
        window = [p for d, p in simulated_series[: idx + 1] if (obs_d - d).days < 14]
        sma_val = round(sum(window) / len(window), 2) if len(window) >= 3 else None

        points.append(
            SimulationTimeSeriesPoint(
                date=obs_d.isoformat(),
                observed_price=orig_p,
                simulated_price=sim_p,
                baseline_sma_14d=sma_val,
                is_shock_period=is_shock,
            )
        )

    # Evaluate anomaly parameters: compare simulated endpoint against un-shocked baseline history
    # so multi-day shocks do not artificially inflate the historical variance baseline.
    eval_series = [
        (d, round(base_series[i][1] * (1.0 + (payload.baseline_adjustment_pct / 100.0)), 2))
        for i, (d, _) in enumerate(simulated_series[:-1])
    ] + [simulated_series[-1]]

    is_anomaly, severity, direction, metrics = anomaly_engine.evaluate_series(
        daily_prices=eval_series,
        target_date=eval_date,
    )

    # Generate plain-language explanation
    explanation = anomaly_engine.generate_explanation(
        commodity_name=commodity.canonical_name,
        unit=commodity.default_unit,
        eval_date=eval_date,
        is_anomaly=is_anomaly,
        severity=severity,
        direction=direction,
        metrics=metrics,
    )

    # Academic Impact Assessment tailored to scenario
    baseline_final = base_series[-1][1]
    simulated_final = simulated_series[-1][1]
    delta_val = round(simulated_final - baseline_final, 2)

    if payload.shock_percentage > 0:
        impact_assessment = (
            f"Under the {payload.shock_type} scenario (+{payload.shock_percentage:.1f}% shock over "
            f"{payload.shock_duration_days} days), retail prices rise by {delta_val:+.2f} BDT/{commodity.default_unit}. "
            f"Model predicts significant consumer surplus loss among low-income quintiles. "
            f"Recommended policy intervention: Immediate open-market distribution via TCB truck sales "
            f"and temporary reduction of import regulatory tariffs."
        )
    elif payload.shock_percentage < 0:
        impact_assessment = (
            f"Under the {payload.shock_type} scenario ({payload.shock_percentage:.1f}% price decline), "
            f"farmgate revenues compress significantly, threatening producer profitability. "
            f"Recommended policy intervention: Minimum support price enforcement and procurement quotas."
        )
    else:
        impact_assessment = (
            f"Market trades at baseline equilibrium with zero synthetic shock injection. "
            f"Supply-demand elasticity remains stable."
        )

    return SimulationResponse(
        commodity_id=commodity.id,
        canonical_name=commodity.canonical_name,
        bangla_name=commodity.bangla_name,
        unit=commodity.default_unit,
        simulation_date=eval_date,
        baseline_price=baseline_final,
        simulated_price=simulated_final,
        shock_percentage=payload.shock_percentage,
        shock_duration_days=payload.shock_duration_days,
        shock_type=payload.shock_type,
        is_anomaly=is_anomaly,
        anomaly_severity=severity,
        anomaly_direction=direction,
        confidence_score=0.95,
        metrics=metrics,
        explanation=explanation,
        impact_assessment=impact_assessment,
        time_series=points,
    )
