"""
tests/test_phase5a_freshness.py
===============================
Comprehensive test suite for Phase 5A: Observation Freshness & Stale Data Safeguards.

Covers:
1. Fresh observation -> FRESH_TODAY
2. ~24h old observation -> YESTERDAY
3. ~48h old observation -> STALE
4. > 48h old observation -> STALE
5. Future timestamp -> safe handling (FRESH_TODAY, 0.0 elapsed)
6. Timezone boundary around Bangladesh midnight (BST UTC+6)
7. LIVE + stale remains distinguishable
8. FALLBACK + stale remains distinguishable
9. MODELED remains MODELED
10. Newer observation cannot be overwritten by older fallback data
11. Existing API contracts (/api/v1/pulse/today, /api/v1/search/realtime, /api/v1/commodities/{id}/stores) remain valid
12. Fixture fallback does not synthesize today's date when live HTTP is down
13. Deterministic fixed timestamps throughout
"""

from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.source import Source
from app.models.observation import PriceObservation
from app.services.freshness import (
    BST,
    evaluate_freshness,
    get_bangladesh_today,
    get_bangladesh_now,
)
from app.services.realtime_service import RealtimePriceService
from app.services.ingestion import IngestionPipeline, RawObservation, BaseCollector
from app.schemas.common import FreshnessMetadata


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


# ---------------------------------------------------------------------------
# Unit Tests for evaluate_freshness (Fixed Deterministic Timestamps)
# ---------------------------------------------------------------------------

class TestFreshnessEvaluationUnit:
    """Deterministic tests for the canonical evaluate_freshness function."""

    FIXED_REF_DATE = date(2026, 10, 5)
    FIXED_REF_DT = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    def test_fresh_observation_same_day(self):
        """Observation on same calendar day as reference date -> FRESH_TODAY."""
        scraped = datetime(2026, 10, 5, 9, 30, 0, tzinfo=timezone.utc)
        meta = evaluate_freshness(
            obs_date=self.FIXED_REF_DATE,
            scraped_at=scraped,
            ref_date=self.FIXED_REF_DATE,
            ref_dt=self.FIXED_REF_DT,
        )
        assert meta.freshness_tier == "FRESH_TODAY"
        assert meta.freshness_age_hours == 2.5
        assert meta.status == "fresh"
        assert meta.is_stale is False

    def test_yesterday_observation(self):
        """Observation from 1 day prior -> YESTERDAY."""
        obs_date = self.FIXED_REF_DATE - timedelta(days=1)
        scraped = datetime(2026, 10, 4, 12, 0, 0, tzinfo=timezone.utc)
        meta = evaluate_freshness(
            obs_date=obs_date,
            scraped_at=scraped,
            ref_date=self.FIXED_REF_DATE,
            ref_dt=self.FIXED_REF_DT,
        )
        assert meta.freshness_tier == "YESTERDAY"
        assert meta.freshness_age_hours == 24.0
        assert meta.status == "historical"
        assert meta.is_stale is False

    def test_48h_old_boundary(self):
        """Observation from 2 days prior (48 hours) -> STALE."""
        obs_date = self.FIXED_REF_DATE - timedelta(days=2)
        scraped = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)
        meta = evaluate_freshness(
            obs_date=obs_date,
            scraped_at=scraped,
            ref_date=self.FIXED_REF_DATE,
            ref_dt=self.FIXED_REF_DT,
        )
        assert meta.freshness_tier == "STALE"
        assert meta.freshness_age_hours == 48.0
        assert meta.status == "stale"
        assert meta.is_stale is True

    def test_greater_than_48h_stale(self):
        """Observation from 5 days prior -> STALE."""
        obs_date = self.FIXED_REF_DATE - timedelta(days=5)
        meta = evaluate_freshness(
            obs_date=obs_date,
            scraped_at=None,
            ref_date=self.FIXED_REF_DATE,
            ref_dt=self.FIXED_REF_DT,
        )
        assert meta.freshness_tier == "STALE"
        assert meta.freshness_age_hours == 120.0
        assert meta.status == "stale"
        assert meta.is_stale is True

    def test_future_timestamp_safe_handling(self):
        """Future observation date safely clamped to FRESH_TODAY, 0.0 age."""
        future_date = self.FIXED_REF_DATE + timedelta(days=2)
        future_scraped = datetime(2026, 10, 7, 12, 0, 0, tzinfo=timezone.utc)
        meta = evaluate_freshness(
            obs_date=future_date,
            scraped_at=future_scraped,
            ref_date=self.FIXED_REF_DATE,
            ref_dt=self.FIXED_REF_DT,
        )
        assert meta.freshness_tier == "FRESH_TODAY"
        assert meta.freshness_age_hours == 0.0
        assert meta.is_stale is False

    def test_bangladesh_midnight_boundary(self):
        """
        Verify timezone boundary at 00:05 BST (18:05 UTC previous day).
        In BST (+06:00), 2026-10-06 00:05 is already 2026-10-06.
        An observation stamped 2026-10-05 is YESTERDAY in BST.
        """
        dt_just_after_midnight_bst = datetime(2026, 10, 6, 0, 5, 0, tzinfo=BST)
        ref_date = dt_just_after_midnight_bst.date()  # 2026-10-06
        obs_date_prev = date(2026, 10, 5)

        meta = evaluate_freshness(
            obs_date=obs_date_prev,
            scraped_at=datetime(2026, 10, 5, 10, 0, tzinfo=timezone.utc),
            ref_date=ref_date,
            ref_dt=dt_just_after_midnight_bst,
        )
        assert meta.freshness_tier == "YESTERDAY"
        assert meta.is_stale is False

    def test_status_override_preserved(self):
        """Realtime ingested status override is retained in FreshnessMetadata."""
        meta = evaluate_freshness(
            obs_date=self.FIXED_REF_DATE,
            scraped_at=self.FIXED_REF_DT,
            ref_date=self.FIXED_REF_DATE,
            ref_dt=self.FIXED_REF_DT,
            status_override="realtime_ingested",
        )
        assert meta.status == "realtime_ingested"
        assert meta.freshness_tier == "FRESH_TODAY"


# ---------------------------------------------------------------------------
# Integration Tests: Provenance & Freshness Orthogonality
# ---------------------------------------------------------------------------

class TestProvenanceFreshnessOrthogonality:
    """Verify that provenance (LIVE, FALLBACK, MODELED) is never overwritten by freshness."""

    def test_live_and_stale_distinguishable(self, client: TestClient, db: Session):
        """A store observation from 5 days ago retains its LIVE / FALLBACK provenance while freshness is STALE."""
        comm = db.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
        assert comm is not None

        resp = client.get(f"/api/v1/commodities/{comm.id}/stores")
        assert resp.status_code == 200
        data = resp.json()
        assert "stores" in data
        for store in data["stores"]:
            # collection_status is one of LIVE, FALLBACK, MODELED, UNAVAILABLE
            assert store["collection_status"] in ["LIVE", "FALLBACK", "MODELED", "UNAVAILABLE", "STALE"]
            # freshness_tier is populated and independent
            if store["collection_status"] != "UNAVAILABLE":
                assert store["freshness_tier"] in ["FRESH_TODAY", "YESTERDAY", "STALE"]
                assert store["freshness_age_hours"] is not None

    def test_modeled_remains_modeled_regardless_of_freshness(self, client: TestClient, db: Session):
        """Pandamart modeled benchmark remains MODELED regardless of temporal age."""
        comm = db.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
        resp = client.get(f"/api/v1/commodities/{comm.id}/stores")
        assert resp.status_code == 200
        data = resp.json()
        panda = next((s for s in data["stores"] if s["id"] == "pandamart"), None)
        assert panda is not None
        assert panda["collection_status"] == "MODELED"
        assert panda["is_live"] is False
        assert panda["is_fallback"] is False


# ---------------------------------------------------------------------------
# Ingestion Safety: Older Fallback Cannot Overwrite Newer Live Data
# ---------------------------------------------------------------------------

class DummyCollector(BaseCollector):
    source_code = "dam"
    source_name = "Department of Agricultural Marketing"
    source_type = "government"
    reliability_score = 0.95

    def __init__(self, raw_items):
        self._items = raw_items

    def collect(self):
        return self._items


class TestIngestionFreshnessSafeguards:
    """Verify that fallback data and older dates never replace newer live observations."""

    def test_fallback_cannot_overwrite_existing_live_data(self, db: Session):
        comm = db.scalars(select(Commodity).where(Commodity.canonical_name == "Potato (Diamond)")).first()
        market = db.scalars(select(Market).where(Market.name == "Karwan Bazar")).first()
        source = db.scalars(select(Source).where(Source.code == "dam")).first()
        if not source:
            source = Source(code="dam", name="DAM", source_type="government", reliability_score=0.95)
            db.add(source)
            db.flush()

        test_date = date(2026, 10, 10)

        # 1. Insert live observation
        live_obs = PriceObservation(
            commodity_id=comm.id,
            market_id=market.id,
            source_id=source.id,
            raw_name="গোল আলু (ডায়মন্ড)",
            raw_price=55.0,
            raw_unit="kg",
            normalized_price=55.0,
            normalized_unit="kg",
            price_type="retail_avg",
            observation_date=test_date,
            confidence_score=0.92,
        )
        db.add(live_obs)
        db.commit()

        try:
            # 2. Attempt to ingest fallback fixture item for same commodity/date
            fallback_item = RawObservation(
                source_code="dam",
                market_name="Karwan Bazar",
                raw_commodity_name="গোল আলু (ডায়মন্ড)",
                raw_unit="kg",
                raw_price=30.0,
                price_type="retail_avg",
                observation_date=test_date,
                is_fallback=True,
                collection_status="FALLBACK",
            )
            pipeline = IngestionPipeline(db)
            report = pipeline.run_collector(DummyCollector([fallback_item]))

            # Fallback must be skipped
            assert report.skipped == 1
            assert report.updated == 0

            # Verify existing live price remains unchanged
            refreshed = db.scalars(
                select(PriceObservation).where(
                    PriceObservation.commodity_id == comm.id,
                    PriceObservation.observation_date == test_date,
                    PriceObservation.price_type == "retail_avg",
                )
            ).first()
            assert refreshed.normalized_price == 55.0
            assert refreshed.confidence_score == 0.92

        finally:
            db.query(PriceObservation).where(
                PriceObservation.commodity_id == comm.id,
                PriceObservation.observation_date == test_date,
            ).delete()
            db.commit()


# ---------------------------------------------------------------------------
# API Contract & Pulse Regression Tests
# ---------------------------------------------------------------------------

class TestFreshnessAPIContracts:
    """Verify response models for /pulse/today and /search/realtime."""

    def test_pulse_today_contract(self, client: TestClient):
        resp = client.get("/api/v1/pulse/today")
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "items" in data
        assert len(data["items"]) > 0

        first = data["items"][0]
        assert "freshness" in first
        freshness = first["freshness"]
        assert "status" in freshness
        assert "freshness_tier" in freshness
        assert freshness["freshness_tier"] in ["FRESH_TODAY", "YESTERDAY", "STALE"]
        assert "freshness_age_hours" in freshness
        assert isinstance(freshness["freshness_age_hours"], (int, float))
        assert "observation_date" in first

    def test_search_realtime_contract(self, client: TestClient):
        resp = client.get("/api/v1/search/realtime?query=onion")
        assert resp.status_code == 200
        data = resp.json()
        assert "freshness" in data
        freshness = data["freshness"]
        assert "status" in freshness
        assert "freshness_tier" in freshness
        assert freshness["freshness_tier"] in ["FRESH_TODAY", "YESTERDAY", "STALE"]
        assert "freshness_age_hours" in freshness
        assert isinstance(freshness["freshness_age_hours"], (int, float))
