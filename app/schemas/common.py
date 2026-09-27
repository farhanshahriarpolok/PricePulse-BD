"""
Common API schemas including health, freshness metadata, and RFC 7807 error models.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class FreshnessMetadata(BaseModel):
    status: str = Field(..., description="'fresh', 'stale', 'realtime_ingested', or 'historical'")
    last_scraped_at: Optional[datetime] = Field(None, description="Timestamp of latest observation scraping")
    is_stale: bool = Field(False, description="True if observation is older than 12 hours")
    cache_age_seconds: Optional[int] = Field(None, description="Age in seconds of the cached observation")


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "PricePulse BD"
    version: str = "0.2.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorDetail(BaseModel):
    code: str
    message: str
    status: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    error: ErrorDetail
