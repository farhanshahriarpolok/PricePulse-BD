"""
API v1 route aggregator.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import pulse, search, commodities

api_router = APIRouter(prefix="/v1")

api_router.include_router(pulse.router)
api_router.include_router(search.router)
api_router.include_router(commodities.router)
