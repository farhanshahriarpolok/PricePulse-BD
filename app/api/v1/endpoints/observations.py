"""
REST API endpoint for manual field spot price reporting and verification.
"""

from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin_api_key
from app.models.commodity import Commodity
from app.models.location import Market, District
from app.models.source import Source
from app.models.observation import PriceObservation
from app.schemas.manual_ingestion import ManualObservationCreate, ManualObservationResponse
from app.services.normalizer import commodity_normalizer
from app.services.confidence import confidence_scorer

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.post(
    "/manual",
    response_model=ManualObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Manual Spot Price Observation",
    description=(
        "Accepts a human-in-the-loop spot price quote from field reporters. "
        "Standardizes raw units (e.g. 'হালি' -> pc, 'ডজন' -> pc) to SI base metrics, "
        "assigns calibrated Tier-4 field confidence (0.60 base scalar), and persists the record. "
        "Requires administrative authentication via X-API-Key header."
    ),
)
def submit_manual_observation(
    payload: ManualObservationCreate,
    db: Session = Depends(get_db),
    _api_key: str = Security(require_admin_api_key),
):
    # 1. Verify target commodity exists
    commodity = db.get(Commodity, payload.commodity_id)
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity with ID {payload.commodity_id} does not exist",
        )

    # 2. Verify target market exists
    market = db.get(Market, payload.market_id)
    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market location with ID {payload.market_id} does not exist",
        )

    # District name lookup for response metadata
    district_name = None
    if market.district_id:
        district = db.get(District, market.district_id)
        if district:
            district_name = district.name

    # 3. Ensure Source for field_report exists
    source_stmt = select(Source).where(Source.code == "field_report")
    source = db.scalars(source_stmt).first()
    if not source:
        source = Source(
            code="field_report",
            name="Field Spot Report (Manual)",
            source_type="field_report",
            reliability_score=0.60,
        )
        db.add(source)
        db.flush()

    # 4. Standardize unit and price using normalizer
    try:
        normalized_price, normalized_unit = commodity_normalizer.normalize_price(
            raw_price=payload.price,
            raw_unit=payload.raw_unit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unit normalization failed: {str(e)}",
        )

    # 5. Calculate calibrated confidence score for field submission
    obs_date = payload.observation_date or date.today()
    confidence = confidence_scorer.compute_field_report_confidence(
        observation_date=obs_date,
        has_note=bool(payload.reporter_note and payload.reporter_note.strip()),
    )

    # 6. Format price type identifier
    price_type = "wholesale_avg" if payload.market_tier == "wholesale" else "retail_avg"

    # 7. Check for existing observation on same date to maintain uniqueness or update
    existing_stmt = select(PriceObservation).where(
        PriceObservation.commodity_id == commodity.id,
        PriceObservation.market_id == market.id,
        PriceObservation.source_id == source.id,
        PriceObservation.observation_date == obs_date,
        PriceObservation.price_type == price_type,
    )
    existing_obs = db.scalars(existing_stmt).first()

    raw_label = f"{commodity.canonical_name} ({payload.reporter_name or 'Field Reporter'})"
    if payload.reporter_note:
        raw_label += f" - Note: {payload.reporter_note}"

    if existing_obs:
        existing_obs.raw_price = payload.price
        existing_obs.raw_unit = payload.raw_unit
        existing_obs.normalized_price = normalized_price
        existing_obs.normalized_unit = normalized_unit
        existing_obs.confidence_score = confidence
        existing_obs.raw_name = raw_label
        db.commit()
        db.refresh(existing_obs)
        persisted_record = existing_obs
    else:
        new_obs = PriceObservation(
            commodity_id=commodity.id,
            market_id=market.id,
            source_id=source.id,
            raw_name=raw_label,
            raw_price=payload.price,
            raw_unit=payload.raw_unit,
            normalized_price=normalized_price,
            normalized_unit=normalized_unit,
            price_type=price_type,
            observation_date=obs_date,
            confidence_score=confidence,
        )
        db.add(new_obs)
        db.commit()
        db.refresh(new_obs)
        persisted_record = new_obs

    # Invalidate downstream forecast and spatial opportunity caches for this commodity
    from app.services.forecast_service import forecast_service
    from app.services.spatial_service import spatial_service
    forecast_service.invalidate(commodity_id=commodity.id)
    spatial_service.invalidate(commodity_id=commodity.id)

    return ManualObservationResponse(
        id=persisted_record.id,
        commodity_id=commodity.id,
        commodity_name=commodity.canonical_name,
        commodity_bangla_name=commodity.bangla_name,
        market_id=market.id,
        market_name=market.name,
        district_name=district_name,
        raw_price=payload.price,
        raw_unit=payload.raw_unit,
        normalized_price=normalized_price,
        normalized_unit=normalized_unit,
        price_type=price_type,
        source_code=source.code,
        source_name=source.name,
        observation_date=persisted_record.observation_date,
        confidence_score=persisted_record.confidence_score,
        reporter_note=payload.reporter_note,
        created_at=persisted_record.scraped_at or datetime.now(timezone.utc),
    )
