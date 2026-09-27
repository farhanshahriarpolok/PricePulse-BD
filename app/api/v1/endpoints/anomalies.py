"""
Statistical anomaly detection and explainability endpoints.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.anomaly_engine import anomaly_engine
from app.services.spatial_service import spatial_service
from app.schemas.anomaly import AnomalyDetailOut, AnomalyMonitorResponse

router = APIRouter(prefix="/anomalies", tags=["Statistical Anomalies"])


@router.get(
    "/active",
    response_model=AnomalyMonitorResponse,
    summary="List Active Commodity Anomalies",
    description=(
        "Scans all registered essential commodities for the target date and returns active anomalies "
        "identified via rolling 14-day Z-scores and compound delta rules."
    ),
)
def get_active_anomalies(
    obs_date: Optional[date] = Query(None, alias="date", description="Target calendar date (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
):
    return anomaly_engine.detect_active_anomalies(db=db, target_date=obs_date)


@router.get(
    "/{commodity_id}/explain",
    response_model=AnomalyDetailOut,
    summary="Explain Commodity Price Anomaly",
    description=(
        "Provides a statistical breakdown (SMA 7/14/30d, standard deviation, Z-score, CV) "
        "and a rule-based natural language justification explaining why a commodity's price is abnormal or stable."
    ),
)
def explain_anomaly(
    commodity_id: str,
    obs_date: Optional[date] = Query(None, alias="date", description="Target calendar date (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
):
    commodity = spatial_service.resolve_commodity(db, commodity_id)
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity '{commodity_id}' could not be resolved in the canonical taxonomy.",
        )

    return anomaly_engine.analyze_commodity(
        db=db, commodity=commodity, target_date=obs_date
    )
