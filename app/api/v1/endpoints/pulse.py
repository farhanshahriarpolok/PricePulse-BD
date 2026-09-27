"""
Market pulse endpoints providing daily macro price summaries.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.realtime_service import RealtimePriceService
from app.schemas.search import DailyPulseResponse

router = APIRouter(prefix="/pulse", tags=["Market Pulse"])


@router.get(
    "/today",
    response_model=DailyPulseResponse,
    summary="Daily Market Pulse for Essential Commodities",
    description="Returns aggregate pricing, wholesale/retail spreads, and freshness status for today's market staples.",
)
def get_daily_pulse(db: Session = Depends(get_db)):
    service = RealtimePriceService(db=db)
    return service.get_today_pulse()
