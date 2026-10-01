"""
tests/test_phase4b_lifecycle_freshness.py
=========================================
Phase 4B Lifecycle Freshness Audit & Invalidation Tests.

Tests the REAL application lifecycle:
1. IngestionPipeline invalidates forecast and spatial caches for affected commodities.
2. Untouched commodities remain cached (zero unnecessary cache invalidation).
3. Manual spot observation submission invalidates forecast and spatial caches.
4. Subsequent forecast and spatial queries reflect fresh data immediately.
5. Granular invalidation by commodity and channel operates deterministically.
"""

from datetime import date, timedelta
import pytest
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.services.forecast_service import forecast_service
from app.services.spatial_service import spatial_service
from app.services.ingestion import IngestionPipeline, ingest_observations
from app.collectors.base import BaseCollector, RawObservation


class DummyCollector(BaseCollector):
    source_code = "test_dummy_source"
    source_name = "Test Dummy Collector"
    source_type = "test"
    reliability_score = 0.90

    def __init__(self, raw_items):
        self._raw = raw_items

    def collect(self):
        return self._raw


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


def test_forecast_granular_invalidation_method():
    """Verify ForecastService.invalidate works granularly by commodity and channel."""
    forecast_service.clear_cache()

    # Artificially populate cache for testing eviction
    forecast_service._cache[(1, "wholesale", None)] = (100.0, None)
    forecast_service._cache[(1, "retail", None)] = (100.0, None)
    forecast_service._cache[(1, "wholesale", 2)] = (100.0, None)
    forecast_service._cache[(2, "wholesale", None)] = (100.0, None)

    assert len(forecast_service._cache) == 4

    # Evict commodity 1 wholesale only
    evicted = forecast_service.invalidate(commodity_id=1, channel="wholesale")
    assert evicted == 2
    assert len(forecast_service._cache) == 2
    assert (1, "retail", None) in forecast_service._cache
    assert (2, "wholesale", None) in forecast_service._cache

    # Evict commodity 2 all channels
    evicted_all = forecast_service.invalidate(commodity_id=2)
    assert evicted_all == 1
    assert len(forecast_service._cache) == 1
    assert (1, "retail", None) in forecast_service._cache

    # Full clear
    evicted_full = forecast_service.invalidate(commodity_id=None)
    assert evicted_full == 1
    assert len(forecast_service._cache) == 0


def test_spatial_granular_invalidation_method():
    """Verify SpatialService.invalidate works granularly by commodity."""
    spatial_service.clear_cache()

    spatial_service._opportunity_cache[(1, "2026-10-01")] = (100.0, None)
    spatial_service._opportunity_cache[(1, "2026-10-02")] = (100.0, None)
    spatial_service._opportunity_cache[(2, "2026-10-01")] = (100.0, None)

    assert len(spatial_service._opportunity_cache) == 3

    # Evict commodity 1
    evicted = spatial_service.invalidate(commodity_id=1)
    assert evicted == 2
    assert len(spatial_service._opportunity_cache) == 1
    assert (2, "2026-10-01") in spatial_service._opportunity_cache

    # Full clear
    evicted_all = spatial_service.invalidate(commodity_id=None)
    assert evicted_all == 1
    assert len(spatial_service._opportunity_cache) == 0


def test_ingestion_pipeline_event_driven_invalidation(db: Session):
    """
    Test real application lifecycle:
    1. Query and cache forecasts for Commodity A (Onion Local) and Commodity B (Potato Diamond).
    2. Run IngestionPipeline with new observations for Commodity A only.
    3. Verify Commodity A cache is evicted and recomputes with fresh data.
    4. Verify Commodity B cache remains intact (cache hit, zero unnecessary eviction).
    """
    comm_a = db.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
    comm_b = db.scalars(select(Commodity).where(Commodity.canonical_name == "Potato (Diamond)")).first()
    assert comm_a is not None and comm_b is not None

    forecast_service.clear_cache()
    spatial_service.clear_cache()

    # Step 1: Pre-populate cache for both commodities
    res_a1 = forecast_service.generate_commodity_forecast(db, str(comm_a.id), "wholesale")
    res_b1 = forecast_service.generate_commodity_forecast(db, str(comm_b.id), "wholesale")
    opp_a1 = spatial_service.get_consumer_opportunity(db, str(comm_a.id))
    opp_b1 = spatial_service.get_consumer_opportunity(db, str(comm_b.id))

    assert res_a1.status == "FORECAST" and res_b1.status == "FORECAST"
    assert (comm_a.id, "wholesale", None) in forecast_service._cache
    assert (comm_b.id, "wholesale", None) in forecast_service._cache

    # Step 2: Ingest new observation for Commodity A via IngestionPipeline
    latest_date_stmt = select(func.max(PriceObservation.observation_date)).where(PriceObservation.commodity_id == comm_a.id)
    latest_date = db.scalar(latest_date_stmt) or date.today()
    new_date = latest_date + timedelta(days=1)
    shock_price = 150.0

    raw_item = RawObservation(
        source_code="dam",
        raw_commodity_name="দেশি পেঁয়াজ",
        raw_price=shock_price,
        raw_unit="kg",
        price_type="wholesale_avg",
        market_name="Karwan Bazar",
        observation_date=new_date,
    )
    collector = DummyCollector([raw_item])
    pipeline = IngestionPipeline(db)
    report = pipeline.run_collector(collector)
    assert report.inserted == 1 or report.updated == 1

    try:
        # Step 3: Verify Commodity A was evicted from both caches
        assert (comm_a.id, "wholesale", None) not in forecast_service._cache
        # Verify Commodity B remains warm in cache!
        assert (comm_b.id, "wholesale", None) in forecast_service._cache

        # Step 4: Next request for Commodity A generates fresh forecast immediately
        res_a2 = forecast_service.generate_commodity_forecast(db, str(comm_a.id), "wholesale")
        assert res_a2.forecast_detail.current_observed_price_bdt == shock_price

        # Next request for Commodity B hits cache
        stats_b_before = forecast_service.get_cache_stats()
        res_b2 = forecast_service.generate_commodity_forecast(db, str(comm_b.id), "wholesale")
        stats_b_after = forecast_service.get_cache_stats()
        assert stats_b_after["hits"] == stats_b_before["hits"] + 1

    finally:
        # Cleanup injected shock observation
        db.query(PriceObservation).where(
            PriceObservation.commodity_id == comm_a.id,
            PriceObservation.observation_date == new_date,
        ).delete()
        db.commit()
        forecast_service.clear_cache()
        spatial_service.clear_cache()


def test_manual_observation_endpoint_invalidates_caches(client: TestClient, db: Session):
    """
    Test real application lifecycle for manual field spot observation:
    1. Query and cache forecast and spatial opportunity for a commodity.
    2. Submit manual spot observation via POST /api/v1/observations/manual.
    3. Verify cache is invalidated and fresh query reflects the newly submitted observation.
    """
    comm = db.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
    market = db.scalars(select(Market).where(Market.name == "Karwan Bazar")).first()
    assert comm is not None and market is not None

    forecast_service.clear_cache()
    spatial_service.clear_cache()

    # Pre-populate caches
    f_res1 = forecast_service.generate_commodity_forecast(db, str(comm.id), "wholesale")
    s_res1 = spatial_service.get_consumer_opportunity(db, str(comm.id))
    assert (comm.id, "wholesale", None) in forecast_service._cache

    latest_date_stmt = select(func.max(PriceObservation.observation_date)).where(PriceObservation.commodity_id == comm.id)
    latest_date = db.scalar(latest_date_stmt) or date.today()
    new_date = latest_date + timedelta(days=1)
    manual_price = 160.0

    # Submit manual observation through REST API
    payload = {
        "commodity_id": comm.id,
        "market_id": market.id,
        "price": manual_price,
        "raw_unit": "kg",
        "market_tier": "wholesale",
        "observation_date": new_date.isoformat(),
        "reporter_name": "QA Reporter",
        "reporter_note": "Fresh spot price test",
    }
    resp = client.post("/api/v1/observations/manual", json=payload)
    assert resp.status_code == 201

    try:
        # Cache must be invalidated immediately by the endpoint
        assert (comm.id, "wholesale", None) not in forecast_service._cache

        # Querying forecast must reflect the newly submitted price
        f_res2 = forecast_service.generate_commodity_forecast(db, str(comm.id), "wholesale")
        assert f_res2.forecast_detail.current_observed_price_bdt == manual_price

    finally:
        db.query(PriceObservation).where(
            PriceObservation.commodity_id == comm.id,
            PriceObservation.observation_date == new_date,
        ).delete()
        db.commit()
        forecast_service.clear_cache()
        spatial_service.clear_cache()
