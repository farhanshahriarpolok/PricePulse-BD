"""
Realtime on-demand price discovery endpoints with automated fallback ingestion.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.realtime_service import RealtimePriceService
from app.schemas.search import RealtimePriceResponse

router = APIRouter(prefix="/search", tags=["Realtime Search"])


@router.get(
    "/realtime",
    response_model=RealtimePriceResponse,
    summary="On-Demand Realtime Commodity Price Search",
    description=(
        "Searches commodity pricing for a target date. Automatically triggers dynamic collector "
        "harvest if observations are missing or older than 12 hours."
    ),
    responses={
        404: {
            "description": "Commodity Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "Commodity 'unknown_item' not recognized in taxonomy.",
                            "status": 404,
                            "timestamp": "2026-09-28T02:00:00Z",
                        }
                    }
                }
            },
        }
    },
)
def search_realtime_price(
    query: str = Query(..., min_length=1, description="Commodity name in English or Bengali (e.g., 'onion', 'মিনিকেট চাল')"),
    obs_date: Optional[date] = Query(None, alias="date", description="Target calendar date (YYYY-MM-DD). Defaults to today."),
    db: Session = Depends(get_db),
):
    service = RealtimePriceService(db=db)
    result = service.get_realtime_price(query=query, target_date=obs_date)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commodity '{query}' could not be resolved in the canonical taxonomy.",
        )

    return result
