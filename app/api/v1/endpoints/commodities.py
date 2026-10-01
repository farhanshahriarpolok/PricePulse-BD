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
    StorePriceOut,
    CommodityStoresResponse,
)

from app.schemas.observation import (
    CommodityHistoryResponse,
    HistoricalPointOut,
)
from app.schemas.forecast import CommodityForecastResponse
from app.services.forecast_service import forecast_service

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


@router.get(
    "/{commodity_id}/stores",
    response_model=CommodityStoresResponse,
    summary="Get Multi-Store Retail Comparison with Real Data Provenance",
    description="Returns live observed or transparently modeled prices across quick-commerce and superstore channels.",
)
def get_commodity_stores(
    commodity_id: int,
    db: Session = Depends(get_db),
):
    from app.models.source import Source

    stmt_comm = select(Commodity).where(Commodity.id == commodity_id)
    commodity = db.scalars(stmt_comm).first()
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity with id {commodity_id} does not exist.",
        )

    # 1. Base retail price for modeled fallback calculations
    base_retail_stmt = (
        select(PriceObservation.normalized_price)
        .where(
            PriceObservation.commodity_id == commodity_id,
            PriceObservation.price_type.like("%retail%"),
        )
        .order_by(PriceObservation.observation_date.desc(), PriceObservation.id.desc())
    )
    base_retail = db.scalars(base_retail_stmt).first()
    if not base_retail or base_retail <= 0:
        base_retail = 100.0

    # 2. Query latest observation per retail source
    store_configs = [
        {
            "id": "chaldal",
            "source_code": "CHALDAL_RETAIL",
            "name_bn": "চালডাল",
            "name_en": "Chaldal",
            "url": "https://chaldal.com",
            "default_spread": -0.02,
        },
        {
            "id": "shwapno",
            "source_code": "SHWAPNO_RETAIL",
            "name_bn": "স্বপ্ন অনলাইন",
            "name_en": "Shwapno Online",
            "url": "https://shwapno.com",
            "default_spread": 0.02,
        },
        {
            "id": "meenabazar",
            "source_code": "MEENA_BAZAR_RETAIL",
            "name_bn": "মীনা বাজার",
            "name_en": "Meena Bazar",
            "url": "https://meenabazaronline.com",
            "default_spread": 0.05,
        },
        {
            "id": "pandamart",
            "source_code": "PANDAMART_MODELED",
            "name_bn": "পান্ডামার্ট",
            "name_en": "Pandamart",
            "url": "https://foodpanda.com.bd/pandamart",
            "default_spread": 0.08,
        },
    ]

    stores_out: List[StorePriceOut] = []

    for cfg in store_configs:
        source = db.scalars(select(Source).where(Source.code == cfg["source_code"])).first()
        obs = None
        if source:
            obs = db.scalars(
                select(PriceObservation)
                .where(
                    PriceObservation.commodity_id == commodity_id,
                    PriceObservation.source_id == source.id,
                )
                .order_by(PriceObservation.observation_date.desc(), PriceObservation.id.desc())
            ).first()

        if obs and obs.normalized_price > 0:
            # Provenance: derive collection_status from actual source health telemetry,
            # not from confidence_score heuristic.
            from app.services.source_health import source_health_service
            src_telemetry = source_health_service.get_source_status(cfg["source_code"])

            if cfg["id"] == "pandamart":
                # Pandamart is always MODELED regardless of observation presence
                coll_status = "MODELED"
                is_live = False
                is_fallback = False
                label_bn = "এক্সপ্রেস প্রাক্কলন (+৮%)"
                label_en = "Express Est. (+8%)"
            elif (
                src_telemetry
                and src_telemetry.get("status") == "HEALTHY"
                and not src_telemetry.get("is_fallback", True)
            ):
                coll_status = "LIVE"
                is_live = True
                is_fallback = False
                label_bn = "লাইভ দাম"
                label_en = "Live Observed"
            elif src_telemetry and src_telemetry.get("is_fallback", True):
                coll_status = "FALLBACK"
                is_live = False
                is_fallback = True
                label_bn = "ফলব্যাক বেঞ্চমার্ক"
                label_en = "Catalog Benchmark ✓"
            else:
                # Status UNKNOWN or OFFLINE but observation exists in DB from a prior run
                coll_status = "FALLBACK"
                is_live = False
                is_fallback = True
                label_bn = "ক্যাশড ডেটা"
                label_en = "Cached Observation"

            from app.services.freshness import evaluate_freshness
            obs_freshness = evaluate_freshness(
                obs_date=obs.observation_date,
                scraped_at=obs.scraped_at,
            )

            stores_out.append(
                StorePriceOut(
                    id=cfg["id"],
                    source_code=cfg["source_code"],
                    name_bn=cfg["name_bn"],
                    name_en=cfg["name_en"],
                    price=round(obs.normalized_price, 2),
                    unit=obs.normalized_unit or commodity.default_unit,
                    collection_status=coll_status,
                    status_label_bn=label_bn,
                    status_label_en=label_en,
                    is_live=is_live,
                    is_fallback=is_fallback,
                    url=cfg["url"],
                    observation_date=obs.observation_date.isoformat() if obs.observation_date else None,
                    raw_name=obs.raw_name,
                    freshness_tier=obs_freshness.freshness_tier,
                    freshness_age_hours=obs_freshness.freshness_age_hours,
                )
            )

        else:
            # Honest representation: no observation found for this store and commodity.
            # Never create synthetic numeric prices merely to avoid an empty card or screen.
            coll_status = "UNAVAILABLE"
            label_bn = "তথ্য উপলব্ধ নেই"
            label_en = "Offer Unavailable"
            err_msg = f"No verified price observation currently recorded for {commodity.canonical_name} at {cfg['name_en']}."

            stores_out.append(
                StorePriceOut(
                    id=cfg["id"],
                    source_code=cfg["source_code"],
                    name_bn=cfg["name_bn"],
                    name_en=cfg["name_en"],
                    price=None,
                    unit=commodity.default_unit,
                    collection_status=coll_status,
                    status_label_bn=label_bn,
                    status_label_en=label_en,
                    is_live=False,
                    is_fallback=False,
                    url=cfg["url"],
                    observation_date=None,
                    raw_name=None,
                    error_message=err_msg,
                )
            )

    return CommodityStoresResponse(
        commodity_id=commodity.id,
        canonical_name=commodity.canonical_name,
        bangla_name=commodity.bangla_name,
        default_unit=commodity.default_unit,
        stores=stores_out,
    )


@router.get(
    "/{commodity_id}/forecast",
    response_model=CommodityForecastResponse,
    summary="Get 7-Day Price Forecast with Model Selection and Direction Signal",
    description=(
        "Returns near-term 7-day price forecast, rolling backtest candidate evaluations, "
        "volatility-aware directional outlook, and provenance telemetry. "
        "Empirical observations only; modeled sources (PANDAMART_MODELED) are strictly excluded."
    ),
)
def get_commodity_forecast(
    commodity_id: str,
    channel: str = Query("wholesale", description="Channel filter: 'wholesale', 'retail', 'online', or 'all'"),
    market_id: Optional[int] = Query(None, description="Optional physical market ID filter"),
    db: Session = Depends(get_db),
):
    res = forecast_service.generate_commodity_forecast(
        db=db,
        commodity_identifier=commodity_id,
        channel=channel,
        market_id=market_id,
    )
    if res.status == "UNAVAILABLE" and res.commodity_id == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity '{commodity_id}' could not be resolved or has no price series.",
        )
    return res

