"""
Unit and integration tests for RealtimePriceService and on-demand ingestion.
"""

from datetime import date, timedelta
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.commodity import Commodity
from app.models.observation import PriceObservation
from app.services.realtime_service import RealtimePriceService
from scripts.init_db import seed_locations, seed_commodities


@pytest.fixture
def db_session():
    """Create an isolated SQLite database session for service testing."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with TestingSession() as session:
        seed_locations(session)
        seed_commodities(session)
        yield session

    Base.metadata.drop_all(bind=test_engine)


class TestRealtimePriceService:
    """Test on-demand harvesting, caching, and analytics calculation."""

    def test_on_demand_harvest_triggered_when_empty(self, db_session):
        service = RealtimePriceService(db=db_session)
        today = date.today()

        # Database starts with zero observations for today
        count_before = db_session.scalar(
            select(func.count(PriceObservation.id)).where(PriceObservation.observation_date == today)
        )
        assert count_before == 0

        # Searching for 'onion' should trigger automatic on-demand ingestion
        response = service.get_realtime_price(query="onion", target_date=today)

        assert response is not None
        assert response.canonical_name == "Onion (Local)"
        assert response.freshness.status == "realtime_ingested"
        assert response.price_summary.sample_count > 0
        assert response.price_summary.avg_price > 0

        # Verify observations now exist in the database
        count_after = db_session.scalar(
            select(func.count(PriceObservation.id)).where(PriceObservation.observation_date == today)
        )
        assert count_after > 0

    def test_cache_hit_without_reingestion(self, db_session):
        service = RealtimePriceService(db=db_session)
        today = date.today()

        # First request populates data
        service.get_realtime_price(query="potato", target_date=today)
        count_first = db_session.scalar(
            select(func.count(PriceObservation.id)).where(PriceObservation.observation_date == today)
        )

        # Second request should use existing cache without triggering additional inserts
        res2 = service.get_realtime_price(query="potato", target_date=today)
        assert res2 is not None
        assert res2.freshness.status == "fresh"

        count_second = db_session.scalar(
            select(func.count(PriceObservation.id)).where(PriceObservation.observation_date == today)
        )
        assert count_first == count_second

    def test_channel_breakdown_and_status(self, db_session):
        service = RealtimePriceService(db=db_session)
        today = date.today()

        res = service.get_realtime_price(query="onion", target_date=today)
        assert res is not None
        assert res.channels.wholesale_avg is not None
        assert res.channels.retail_avg is not None or res.channels.online_avg is not None
        assert res.price_status in ["Normal", "Elevated", "High"]

    def test_unknown_commodity_returns_none(self, db_session):
        service = RealtimePriceService(db=db_session)
        res = service.get_realtime_price(query="nonexistent_alien_fruit")
        assert res is None

    def test_daily_pulse_summary(self, db_session):
        service = RealtimePriceService(db=db_session)
        pulse = service.get_today_pulse()

        assert pulse.total_tracked > 0
        assert len(pulse.items) > 0
        for item in pulse.items:
            assert item.price_summary.avg_price > 0
            assert item.price_status in ["Normal", "Elevated", "High"]
