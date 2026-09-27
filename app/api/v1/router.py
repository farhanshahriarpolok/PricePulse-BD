"""
API v1 route aggregator.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    pulse,
    search,
    commodities,
    anomalies,
    locations,
    observations,
    system,
)

api_router = APIRouter(prefix="/v1")

api_router.include_router(pulse.router)
api_router.include_router(search.router)
api_router.include_router(commodities.router)
api_router.include_router(anomalies.router)
api_router.include_router(locations.router)
api_router.include_router(observations.router)
api_router.include_router(system.router)

