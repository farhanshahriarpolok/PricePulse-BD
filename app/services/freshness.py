"""
Canonical freshness evaluation engine for PricePulse BD.
Determines temporal age, semantic freshness tiers (FRESH_TODAY, YESTERDAY, STALE),
and preserves distinct source provenance without artificial scoring or stochastic models.
"""

from datetime import date, datetime, timezone, timedelta
from typing import Optional
from app.schemas.common import FreshnessMetadata

# Bangladesh Standard Time (BST) is UTC+6
BST = timezone(timedelta(hours=6))


def get_bangladesh_now() -> datetime:
    """Return the current datetime in Bangladesh Standard Time (UTC+6)."""
    return datetime.now(BST)


def get_bangladesh_today() -> date:
    """Return current calendar date in Bangladesh Standard Time (UTC+6)."""
    return get_bangladesh_now().date()


def evaluate_freshness(
    obs_date: date,
    scraped_at: Optional[datetime] = None,
    ref_date: Optional[date] = None,
    ref_dt: Optional[datetime] = None,
    status_override: Optional[str] = None,
    is_stale_override: Optional[bool] = None,
) -> FreshnessMetadata:
    """
    Evaluate deterministic observation freshness relative to Bangladesh local calendar.

    Semantic Tiers:
    - FRESH_TODAY: Observation was recorded on today's market date.
    - YESTERDAY: Observation is from the previous calendar day (valid recent history).
    - STALE: Observation is 2 or more calendar days old.

    Args:
        obs_date: Calendar date of the market price observation.
        scraped_at: UTC or timezone-aware harvest timestamp.
        ref_date: Reference calendar date (defaults to Bangladesh today).
        ref_dt: Reference datetime for hourly age (defaults to current time).
        status_override: Optional status string override (e.g. 'realtime_ingested').
        is_stale_override: Optional explicit boolean flag override.

    Returns:
        FreshnessMetadata schema object with freshness_tier, freshness_age_hours,
        status, and backward-compatible fields.
    """
    anchor_date = ref_date or get_bangladesh_today()
    anchor_dt = ref_dt or datetime.now(timezone.utc)

    # 1. Determine Semantic Tier
    if obs_date > anchor_date:
        # Safe handling for clock drift / future timestamps: treat as current
        freshness_tier = "FRESH_TODAY"
        days_diff = 0
    elif obs_date == anchor_date:
        freshness_tier = "FRESH_TODAY"
        days_diff = 0
    elif obs_date == anchor_date - timedelta(days=1):
        freshness_tier = "YESTERDAY"
        days_diff = 1
    else:
        freshness_tier = "STALE"
        days_diff = (anchor_date - obs_date).days

    # 2. Compute Elapsed Age in Hours
    if scraped_at is not None:
        # Normalize anchor_dt to UTC
        anchor_utc = anchor_dt if anchor_dt.tzinfo else anchor_dt.replace(tzinfo=timezone.utc)
        scraped_utc = scraped_at if scraped_at.tzinfo else scraped_at.replace(tzinfo=timezone.utc)
        elapsed_seconds = max(0.0, (anchor_utc - scraped_utc).total_seconds())
        freshness_age_hours = round(elapsed_seconds / 3600.0, 1)
        cache_age_seconds = int(elapsed_seconds)
    else:
        freshness_age_hours = round(days_diff * 24.0, 1)
        cache_age_seconds = int(freshness_age_hours * 3600)

    # 3. Determine status and is_stale for backward compatibility
    if status_override:
        status = status_override
    else:
        if freshness_tier == "FRESH_TODAY":
            status = "fresh"
        elif freshness_tier == "YESTERDAY":
            status = "historical"
        else:
            status = "stale"

    if is_stale_override is not None:
        is_stale = is_stale_override
    else:
        is_stale = (freshness_tier == "STALE") or (freshness_age_hours >= 48.0)

    return FreshnessMetadata(
        status=status,
        last_scraped_at=scraped_at,
        is_stale=is_stale,
        cache_age_seconds=cache_age_seconds,
        freshness_tier=freshness_tier,
        freshness_age_hours=freshness_age_hours,
    )
