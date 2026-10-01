"""
REST API endpoints for the Consumer Bazaar Basket cost optimizer.

Endpoints:
  POST /api/v1/basket/calculate  — full channel cost breakdown for a custom basket
  GET  /api/v1/basket/presets    — three pre-defined Bangladeshi family market baskets
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.schemas.basket import (
    BasketCalculationRequest,
    BasketCalculationResponse,
    PriceAlternativeOut,
    SavedBasketCreate,
    SavedBasketDetailOut,
    SavedBasketSummaryOut,
    BasketTrendResponse,
)
from app.services.basket_service import basket_service

router = APIRouter(prefix="/basket", tags=["Bazaar Basket"])


# ---------------------------------------------------------------------------
# Pre-defined basket presets
# ---------------------------------------------------------------------------

BASKET_PRESETS = [
    {
        "id": "weekly_essentials",
        "name": "Middle-Class Weekly Essentials",
        "bangla_name": "সাপ্তাহিক পারিবারিক বাজার",
        "description": "Standard weekly grocery run for a 4-member middle-class household.",
        "items": [
            {"commodity_name": "Rice (Miniket)", "bangla_name": "মিনিকেট চাল", "quantity": 5, "unit": "kg"},
            {"commodity_name": "Lentils (Masur Dal)", "bangla_name": "মসুর ডাল", "quantity": 1, "unit": "kg"},
            {"commodity_name": "Onion (Local)", "bangla_name": "দেশি পেঁয়াজ", "quantity": 2, "unit": "kg"},
            {"commodity_name": "Potato (Diamond)", "bangla_name": "আলু", "quantity": 3, "unit": "kg"},
            {"commodity_name": "Soybean Oil (Bottled)", "bangla_name": "সয়াবিন তেল", "quantity": 2, "unit": "liter"},
            {"commodity_name": "Egg (Hen)", "bangla_name": "মুরগির ডিম", "quantity": 2, "unit": "হালি"},
        ],
    },
    {
        "id": "bachelor_fast_basket",
        "name": "Bachelor Fast Basket",
        "bangla_name": "ব্যাচেলর বাস্কেট",
        "description": "Minimal weekly essentials for a single working person.",
        "items": [
            {"commodity_name": "Egg (Hen)", "bangla_name": "মুরগির ডিম", "quantity": 1, "unit": "হালি"},
            {"commodity_name": "Potato (Diamond)", "bangla_name": "আলু", "quantity": 1, "unit": "kg"},
            {"commodity_name": "Onion (Local)", "bangla_name": "পেঁয়াজ", "quantity": 0.5, "unit": "kg"},
            {"commodity_name": "Soybean Oil (Bottled)", "bangla_name": "সয়াবিন তেল", "quantity": 500, "unit": "ml"},
            {"commodity_name": "Green Chilli", "bangla_name": "কাঁচা মরিচ", "quantity": 250, "unit": "g"},
        ],
    },
    {
        "id": "family_weekend_feast",
        "name": "Family Weekend Feast",
        "bangla_name": "উইকেন্ড পারিবারিক ভোজ",
        "description": "Special weekend feast basket for a 6-member Bangladeshi family.",
        "items": [
            {"commodity_name": "Beef (Local with Bone)", "bangla_name": "গরুর মাংস", "quantity": 2, "unit": "kg"},
            {"commodity_name": "Rice (Miniket)", "bangla_name": "পোলাও চাল", "quantity": 1, "unit": "kg"},
            {"commodity_name": "Onion (Local)", "bangla_name": "পেঁয়াজ", "quantity": 1, "unit": "kg"},
            {"commodity_name": "Mustard Oil", "bangla_name": "সরিষার তেল", "quantity": 500, "unit": "ml"},
            {"commodity_name": "Garlic", "bangla_name": "রসুন", "quantity": 250, "unit": "g"},
        ],
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/calculate",
    response_model=BasketCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate Bazaar Basket Cost",
    description=(
        "Accepts a custom market basket (commodity IDs + quantities + units) and returns "
        "a full channel cost breakdown across wholesale hub, wet-market retail, and "
        "online / super-shop channels. Includes 7-day personal inflation shift and "
        "Bengali-language procurement tips."
    ),
)
def calculate_basket(
    payload: BasketCalculationRequest,
    db: Session = Depends(get_db),
) -> BasketCalculationResponse:
    """Compute optimized channel cost breakdown for the supplied basket."""
    if not payload.items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Basket must contain at least one item.",
        )

    try:
        result = basket_service.calculate(request=payload, db=db)
    except Exception as exc:
        logger_msg = f"Basket calculation error: {exc}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Basket calculation failed. Please verify commodity IDs and try again.",
        ) from exc

    return result


@router.get(
    "/presets",
    summary="Get Pre-defined Basket Presets",
    description=(
        "Returns three canonical Bangladeshi household market basket presets: "
        "(1) Middle-Class Weekly Essentials, (2) Bachelor Fast Basket, "
        "(3) Family Weekend Feast. Each preset includes bangla names, quantities, "
        "and units ready for direct use in the basket calculator."
    ),
)
def get_basket_presets() -> dict:
    """Return all pre-defined family market basket presets."""
    return {
        "total": len(BASKET_PRESETS),
        "presets": BASKET_PRESETS,
    }


@router.get(
    "/alternatives/{commodity_id}",
    response_model=list[PriceAlternativeOut],
    summary="Get Cheaper Alternatives for Commodity",
    description=(
        "Returns empirical, verified cheaper substitute commodities strictly within "
        "the same category (Rule A) from the explicit registry (Rule B). "
        "Requires savings >= ৳2.00/unit and >= 5.0%."
    ),
)
def get_commodity_alternatives(
    commodity_id: int,
    channel: str = "retail",
    quantity: float = 1.0,
    db: Session = Depends(get_db),
) -> list[PriceAlternativeOut]:
    """Retrieve qualifying cheaper alternatives for a specific commodity."""
    from app.services.alternative_service import alternative_service
    return alternative_service.find_alternatives_for_commodity(
        db=db,
        commodity_id=commodity_id,
        channel=channel,
        basket_quantity=quantity,
    )


# ---------------------------------------------------------------------------
# Saved Basket & Personal Inflation Trend Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/saved",
    response_model=SavedBasketDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Save Customized Basket",
    description="Persist a customized household market basket to SQLite and return calculation detail.",
)
def create_saved_basket(
    payload: SavedBasketCreate,
    db: Session = Depends(get_db),
) -> SavedBasketDetailOut:
    """Save user basket and return calculation detail."""
    try:
        return basket_service.save_basket(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Failed to save basket: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save basket. Please verify input data.",
        ) from exc


@router.get(
    "/saved",
    response_model=list[SavedBasketSummaryOut],
    summary="List Saved Household Baskets",
    description="Return summary overviews for all saved household baskets with live totals and shifts.",
)
def list_saved_baskets(
    db: Session = Depends(get_db),
) -> list[SavedBasketSummaryOut]:
    """List all saved consumer baskets."""
    return basket_service.list_saved_baskets(db=db)


@router.get(
    "/saved/{basket_id}",
    response_model=SavedBasketDetailOut,
    summary="Get Saved Basket Detail",
    description="Retrieve a single saved basket by ID with full item details and channel calculation.",
)
def get_saved_basket(
    basket_id: int,
    db: Session = Depends(get_db),
) -> SavedBasketDetailOut:
    """Retrieve saved basket by ID."""
    detail = basket_service.get_saved_basket(db=db, basket_id=basket_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved basket #{basket_id} not found.",
        )
    return detail


@router.delete(
    "/saved/{basket_id}",
    summary="Delete Saved Basket",
    description="Remove a saved household basket by ID.",
)
def delete_saved_basket(
    basket_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a saved basket."""
    success = basket_service.delete_saved_basket(db=db, basket_id=basket_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved basket #{basket_id} not found.",
        )
    return {"status": "ok", "message": f"Saved basket #{basket_id} deleted successfully."}


@router.get(
    "/saved/{basket_id}/trend",
    response_model=BasketTrendResponse,
    summary="Compute 30-Day Personal Basket CPI Trend",
    description=(
        "Calculates the chronological 30-day cost trajectory, volatility coefficient of variation (CV%), "
        "personal 30-day and 7-day inflation rates, cheapest and peak dates, and academic narrative."
    ),
)
def get_basket_trend(
    basket_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
) -> BasketTrendResponse:
    """Compute 30-day personal CPI trend for a saved basket."""
    trend = basket_service.calculate_basket_trend(db=db, basket_id=basket_id, days=days)
    if not trend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved basket #{basket_id} not found or has no items.",
        )
    return trend

