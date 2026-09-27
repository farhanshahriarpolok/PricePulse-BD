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
