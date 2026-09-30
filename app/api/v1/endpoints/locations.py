"""
Geographic price spread, regional disparities, and spatial hierarchy endpoints.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.spatial_service import spatial_service
from app.schemas.spatial import (
    GeoSpatialPulseResponse,
    LocationHierarchyResponse,
    SpatialArbitrageResponse,
    ConsumerOpportunityResponse,
)

router = APIRouter(prefix="/locations", tags=["Spatial Analytics"])


@router.get(
    "/spread",
    response_model=GeoSpatialPulseResponse,
    summary="Inter-District Spatial Price Spread",
    description=(
        "Calculates price dispersion across Bangladesh markets and districts for a specific commodity, "
        "identifying the cheapest and most expensive trading nodes with Leaflet-ready GeoJSON properties."
    ),
)
def get_spatial_price_spread(
    commodity_id: str = Query(..., description="Commodity ID or canonical alias (e.g., '1', 'onion_local', 'potato')"),
    obs_date: Optional[date] = Query(None, alias="date", description="Target calendar date (YYYY-MM-DD). Defaults to latest available."),
    db: Session = Depends(get_db),
):
    result = spatial_service.get_spatial_spread(
        db=db, commodity_identifier=commodity_id, target_date=obs_date
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity '{commodity_id}' could not be resolved or has no spatial observations.",
        )
    return result


@router.get(
    "/arbitrage",
    response_model=SpatialArbitrageResponse,
    summary="Inter-District Freight & Spatial Arbitrage Estimator",
    description=(
        "Calculates freight-adjusted price spreads between regional production hubs and metropolitan consumption hubs, "
        "estimating net arbitrage margins, ROI %, and economic viability."
    ),
)
def get_spatial_arbitrage(
    commodity_id: str = Query(..., description="Commodity ID or canonical alias (e.g., '1', 'onion_local', 'potato')"),
    obs_date: Optional[date] = Query(None, alias="date", description="Target date (YYYY-MM-DD). Defaults to latest available."),
    db: Session = Depends(get_db),
):
    result = spatial_service.get_spatial_arbitrage(
        db=db, commodity_identifier=commodity_id, target_date=obs_date
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity '{commodity_id}' could not be resolved or has no arbitrage data.",
        )
    return result


@router.get(
    "/hierarchy",
    response_model=LocationHierarchyResponse,
    summary="Administrative Location Tree",
    description="Returns the full Bangladesh administrative and market tree (Divisions -> Districts -> Markets).",
)
def get_location_hierarchy(db: Session = Depends(get_db)):
    return spatial_service.get_location_hierarchy(db=db)


@router.get(
    "/consumer-opportunity",
    response_model=ConsumerOpportunityResponse,
    summary="Consumer-Facing Spatial Market Opportunity",
    description=(
        "Returns the single best actionable spatial price opportunity for a commodity in a flat, "
        "human-readable shape. Suitable for the consumer-first hybrid UI panel. "
        "Always returns a result — has_opportunity=False when no viable arbitrage exists. "
        "The freight_detail and top_routes fields comprise the expandable research layer."
    ),
)
def get_consumer_opportunity(
    commodity_id: str = Query(
        ...,
        description="Commodity ID or canonical alias (e.g., '1', 'onion_local', 'potato')",
    ),
    obs_date: Optional[date] = Query(
        None,
        alias="date",
        description="Target date (YYYY-MM-DD). Defaults to latest available.",
    ),
    db: Session = Depends(get_db),
):
    result = spatial_service.get_consumer_opportunity(
        db=db, commodity_identifier=commodity_id, target_date=obs_date
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity '{commodity_id}' could not be resolved or has no spatial data.",
        )
    return result
