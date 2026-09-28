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
from app.schemas.basket import BasketCalculationRequest, BasketCalculationResponse
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
