"""
Commodity catalog and time-series historical price endpoints.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.commodity import Commodity
from app.models.observation import PriceObservation
from app.schemas.commodity import (
    CommodityOut,
    CommodityDetailOut,
    CommodityListResponse,
)
from app.schemas.observation import (
    CommodityHistoryResponse,
    HistoricalPointOut,
)

router = APIRouter(prefix="/commodities", tags=["Commodities"])


@router.get(
    "",
    response_model=CommodityListResponse,
    summary="List Canonical Commodities",
    description="Returns all registered commodities in the taxonomy, optionally filtered by category.",
)
def list_commodities(
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'Vegetables', 'Grains')"),
    db: Session = Depends(get_db),
):
    stmt = select(Commodity)
    if category:
        stmt = stmt.where(Commodity.category.ilike(category))
    stmt = stmt.order_by(Commodity.id)
    items = list(db.scalars(stmt).all())

    return CommodityListResponse(
        total=len(items),
        items=[CommodityOut.model_validate(item) for item in items],
    )


@router.get(
    "/compare",
    summary="Compare Multiple Commodities",
    description="Returns side-by-side pricing, wholesale vs retail spreads, 14-day trends, and volatility metrics for comparison.",
)
def compare_commodities(
    ids: str = Query(..., description="Comma-separated commodity IDs to compare (e.g., '1,2,3')"),
    district_id: Optional[int] = Query(None, description="Optional district filter"),
    db: Session = Depends(get_db),
):
    from app.services.anomaly_engine import AnomalyEngine
    from app.models.location import Market

    anomaly_engine = AnomalyEngine()
    try:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids parameter must be comma-separated integers (e.g., '1,2,3')",
        )

    if not id_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one commodity ID must be provided",
        )

    results = []
    for c_id in id_list:
        commodity = db.get(Commodity, c_id)
        if not commodity:
            continue

        # Retail and wholesale price queries
        base_query = select(PriceObservation).where(PriceObservation.commodity_id == c_id)
        if district_id:
            base_query = base_query.join(Market).where(Market.district_id == district_id)

        retail_obs = (
            db.scalars(
                base_query.where(PriceObservation.price_type.like("%retail%"))
                .order_by(PriceObservation.observation_date.desc(), PriceObservation.id.desc())
            ).first()
        )

        wholesale_obs = (
            db.scalars(
                base_query.where(PriceObservation.price_type.like("%wholesale%"))
                .order_by(PriceObservation.observation_date.desc(), PriceObservation.id.desc())
            ).first()
        )

        retail_price = round(retail_obs.normalized_price, 2) if retail_obs else None
        wholesale_price = round(wholesale_obs.normalized_price, 2) if wholesale_obs else None

        spread_bdt = None
        spread_pct = None
        if retail_price is not None and wholesale_price is not None and wholesale_price > 0:
            spread_bdt = round(retail_price - wholesale_price, 2)
            spread_pct = round(((retail_price - wholesale_price) / wholesale_price) * 100, 1)

        # Anomaly evaluation
        detail = anomaly_engine.analyze_commodity(db, commodity)
        metrics = detail.metrics

        results.append({
            "commodity_id": commodity.id,
            "canonical_name": commodity.canonical_name,
            "bangla_name": commodity.bangla_name,
            "category": commodity.category,
            "unit": commodity.default_unit,
            "retail_price": retail_price or (metrics.current_price if metrics else None),
            "wholesale_price": wholesale_price,
            "spread_bdt": spread_bdt,
            "spread_pct": spread_pct,
            "baseline_sma_14d": metrics.baseline_sma_14d if metrics else None,
            "delta_pct": metrics.percentage_change_14d if metrics else None,
            "z_score": metrics.z_score_14d if metrics else None,
            "volatility_cv": metrics.volatility_cv if metrics else None,
            "is_anomaly": detail.is_anomaly,
            "severity": detail.anomaly_severity,
            "direction": detail.anomaly_direction,
        })


    return {
        "total_compared": len(results),
        "district_id": district_id,
        "items": results,
    }


@router.get(
    "/{commodity_id}",

    response_model=CommodityDetailOut,
    summary="Get Commodity Details",
    description="Retrieve details and registered alias mappings for a specific canonical commodity.",
)
def get_commodity_detail(commodity_id: int, db: Session = Depends(get_db)):
    stmt = select(Commodity).where(Commodity.id == commodity_id)
    commodity = db.scalars(stmt).first()
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity with id {commodity_id} does not exist.",
        )

    aliases = [a.alias for a in commodity.aliases]
    return CommodityDetailOut(
        id=commodity.id,
        canonical_name=commodity.canonical_name,
        bangla_name=commodity.bangla_name,
        category=commodity.category,
        default_unit=commodity.default_unit,
        aliases=aliases,
    )


@router.get(
    "/{commodity_id}/history",
    response_model=CommodityHistoryResponse,
    summary="Get Commodity Price History",
    description="Returns aggregate historical daily time-series prices for Android and Web charting.",
)
def get_commodity_history(
    commodity_id: int,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    market_id: Optional[int] = Query(None, description="Filter by market ID"),
    db: Session = Depends(get_db),
):
    stmt_comm = select(Commodity).where(Commodity.id == commodity_id)
    commodity = db.scalars(stmt_comm).first()
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity with id {commodity_id} does not exist.",
        )

    query = (
        select(
            PriceObservation.observation_date,
            func.avg(PriceObservation.normalized_price).label("avg_price"),
            func.min(PriceObservation.normalized_price).label("min_price"),
            func.max(PriceObservation.normalized_price).label("max_price"),
            func.count(PriceObservation.id).label("sample_count"),
        )
        .where(PriceObservation.commodity_id == commodity_id)
    )

    if start_date:
        query = query.where(PriceObservation.observation_date >= start_date)
    if end_date:
        query = query.where(PriceObservation.observation_date <= end_date)
    if market_id:
        query = query.where(PriceObservation.market_id == market_id)

    query = query.group_by(PriceObservation.observation_date).order_by(
        PriceObservation.observation_date.asc()
    )

    rows = db.execute(query).all()
    series = [
        HistoricalPointOut(
            date=row.observation_date,
            avg_price=round(float(row.avg_price), 2),
            min_price=round(float(row.min_price), 2),
            max_price=round(float(row.max_price), 2),
            sample_count=int(row.sample_count),
        )
        for row in rows
    ]

    return CommodityHistoryResponse(
        commodity_id=commodity.id,
        canonical_name=commodity.canonical_name,
        unit=commodity.default_unit,
        series=series,
    )
