"""
tests/test_phase4_caching.py
============================
Phase 4 Verification Test Suite:
1. Forecast in-memory TTL caching (hit, miss, clear_cache).
2. Channel key isolation (wholesale vs retail vs online).
3. Market key isolation (national vs market-level).
4. TTL expiration logic.
5. Cross-commodity key isolation.
6. Spatial consumer opportunity in-memory caching.
"""

import time
import pytest
from app.core.database import SessionLocal
from app.services.forecast_service import ForecastService
from app.services.spatial_service import SpatialService


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def forecast_service():
    svc = ForecastService(cache_ttl=3600)
    svc.clear_cache()
    return svc


@pytest.fixture
def spatial_service():
    svc = SpatialService(cache_ttl=3600)
    svc.clear_cache()
    return svc


# ── 1. Forecast In-Memory Caching Tests ────────────────────────────────────────

def test_forecast_cache_hit_and_miss(db, forecast_service):
    """Test cache miss on initial generation and cache hit on repeat."""
    assert forecast_service.get_cache_stats()["hits"] == 0
    assert forecast_service.get_cache_stats()["misses"] == 0

    # 1st call -> Cache Miss
    res1 = forecast_service.generate_commodity_forecast(db, "1", channel="wholesale")
    assert res1.status == "FORECAST"
    stats1 = forecast_service.get_cache_stats()
    assert stats1["misses"] == 1
    assert stats1["hits"] == 0
    assert stats1["size"] == 1

    # 2nd call with identical parameters -> Cache Hit
    res2 = forecast_service.generate_commodity_forecast(db, "1", channel="wholesale")
    assert res2.status == "FORECAST"
    stats2 = forecast_service.get_cache_stats()
    assert stats2["misses"] == 1
    assert stats2["hits"] == 1
    assert stats2["size"] == 1
    assert res1.forecast_detail.forecast_day7_bdt == res2.forecast_detail.forecast_day7_bdt


def test_forecast_cache_channel_isolation(db, forecast_service):
    """Verify distinct channels (wholesale, retail, online) do not collide in cache."""
    res_w = forecast_service.generate_commodity_forecast(db, "1", channel="wholesale")
    res_r = forecast_service.generate_commodity_forecast(db, "1", channel="retail")

    stats = forecast_service.get_cache_stats()
    assert stats["misses"] == 2
    assert stats["size"] == 2
    assert res_w.series_metadata.channel == "wholesale"
    assert res_r.series_metadata.channel == "retail"


def test_forecast_cache_market_isolation(db, forecast_service):
    """Verify national scope and market-level scope do not collide in cache."""
    res_nat = forecast_service.generate_commodity_forecast(db, "1", channel="wholesale", market_id=None)
    res_mkt = forecast_service.generate_commodity_forecast(db, "1", channel="wholesale", market_id=1)

    stats = forecast_service.get_cache_stats()
    assert stats["misses"] == 2
    assert stats["size"] == 2
    assert res_nat.series_metadata.scope == "national"
    assert res_mkt.series_metadata.scope == "market"
    assert res_mkt.series_metadata.market_id == 1


def test_forecast_cache_ttl_expiration(db):
    """Verify entries expire and recompute when TTL has elapsed."""
    short_ttl_svc = ForecastService(cache_ttl=1)  # 1 second TTL
    short_ttl_svc.clear_cache()

    res1 = short_ttl_svc.generate_commodity_forecast(db, "1", channel="wholesale")
    assert res1.status == "FORECAST"
    assert short_ttl_svc.get_cache_stats()["misses"] == 1

    # Immediate second call -> Hit
    short_ttl_svc.generate_commodity_forecast(db, "1", channel="wholesale")
    assert short_ttl_svc.get_cache_stats()["hits"] == 1

    # Sleep beyond TTL (1.1s)
    time.sleep(1.1)

    # Third call after TTL -> Miss (recomputed)
    short_ttl_svc.generate_commodity_forecast(db, "1", channel="wholesale")
    stats = short_ttl_svc.get_cache_stats()
    assert stats["misses"] == 2
    assert stats["hits"] == 1


def test_forecast_cache_cross_commodity_isolation(db, forecast_service):
    """Verify different commodities maintain isolated cache entries."""
    forecast_service.generate_commodity_forecast(db, "1", channel="wholesale")
    forecast_service.generate_commodity_forecast(db, "3", channel="wholesale")

    stats = forecast_service.get_cache_stats()
    assert stats["misses"] == 2
    assert stats["size"] == 2


def test_forecast_cache_sparse_not_cached_as_valid(db, forecast_service):
    """Verify sparse commodities (INSUFFICIENT_DATA) do not pollute valid forecast cache."""
    res_sparse = forecast_service.generate_commodity_forecast(db, "2", channel="wholesale")
    assert res_sparse.status == "INSUFFICIENT_DATA"
    stats = forecast_service.get_cache_stats()
    # Should not be stored in valid forecast cache
    assert stats["size"] == 0


# ── 2. Spatial Consumer Opportunity Caching Tests ──────────────────────────────

def test_spatial_cache_hit_and_miss(db, spatial_service):
    """Test spatial consumer opportunity cache miss on 1st call and hit on 2nd call."""
    res1 = spatial_service.get_consumer_opportunity(db, "1")
    assert res1 is not None
    stats1 = spatial_service.get_cache_stats()
    assert stats1["misses"] == 1
    assert stats1["hits"] == 0
    assert stats1["size"] == 1

    # Repeat call
    res2 = spatial_service.get_consumer_opportunity(db, "1")
    assert res2 is not None
    stats2 = spatial_service.get_cache_stats()
    assert stats2["misses"] == 1
    assert stats2["hits"] == 1
    assert stats2["size"] == 1
    assert res1.cheapest_district == res2.cheapest_district


def test_spatial_cache_cross_commodity_isolation(db, spatial_service):
    """Test distinct commodities maintain isolated spatial cache entries."""
    spatial_service.get_consumer_opportunity(db, "1")
    spatial_service.get_consumer_opportunity(db, "3")
    stats = spatial_service.get_cache_stats()
    assert stats["misses"] == 2
    assert stats["size"] == 2
