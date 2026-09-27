"""
End-to-end integration tests for database schema, seeder, and fixture ingestion pipeline.
"""

from datetime import date
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.commodity import Commodity, CommodityAlias
from app.models.location import Division, District, Market
from app.models.source import Source
from app.models.observation import PriceObservation
from app.collectors.dam_fixture_collector import DAMFixtureCollector
from app.services.ingestion import IngestionPipeline
from scripts.init_db import seed_locations, seed_commodities


@pytest.fixture
def in_memory_db():
    """Create an isolated in-memory SQLite engine and session for integration testing."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with TestingSessionLocal() as session:
        seed_locations(session)
        seed_commodities(session)
        yield session

    Base.metadata.drop_all(bind=test_engine)


class TestIngestionPipeline:
    """Integration test suite verifying fixture harvest, normalization, and DB counts."""

    def test_schema_and_taxonomy_seeding(self, in_memory_db):
        comm_count = in_memory_db.scalar(select(func.count(Commodity.id)))
        market_count = in_memory_db.scalar(select(func.count(Market.id)))
        alias_count = in_memory_db.scalar(select(func.count(CommodityAlias.id)))

        assert comm_count >= 4, f"Expected at least 4 canonical commodities, got {comm_count}"
        assert market_count >= 2, f"Expected at least 2 markets, got {market_count}"
        assert alias_count >= 10, f"Expected at least 10 aliases, got {alias_count}"

    def test_dam_fixture_ingestion_slice(self, in_memory_db):
        collector = DAMFixtureCollector()
        pipeline = IngestionPipeline(db=in_memory_db)
        report = pipeline.run_collector(collector)

        assert report.total_harvested > 0
        assert report.inserted > 0
        assert report.skipped == 0

        # Verify staple commodity observations (Onion, Potato, Rice)
        staples = [
            "Onion (Local)",
            "Onion (Imported)",
            "Potato (Diamond)",
            "Rice (Miniket)",
            "Rice (Nazirshail)",
            "Rice (Coarse)",
        ]
        stmt = (
            select(PriceObservation)
            .join(Commodity, PriceObservation.commodity_id == Commodity.id)
            .where(Commodity.canonical_name.in_(staples))
        )
        staple_observations = in_memory_db.scalars(stmt).all()

        # Acceptance criteria: at least 8 distinct observations across Onion, Potato, and Rice
        assert (
            len(staple_observations) >= 8
        ), f"Expected at least 8 staple observations, got {len(staple_observations)}"

        # Validate normalization invariants
        for obs in staple_observations:
            assert obs.normalized_price > 0.0
            assert obs.normalized_unit in ["kg", "liter", "pc"]
            assert 0.0 <= obs.confidence_score <= 1.0
            assert obs.observation_date <= date.today()

    def test_ingestion_idempotency(self, in_memory_db):
        collector = DAMFixtureCollector()
        pipeline = IngestionPipeline(db=in_memory_db)

        # First run inserts
        report1 = pipeline.run_collector(collector)
        total_obs_1 = in_memory_db.scalar(select(func.count(PriceObservation.id)))

        # Second run should update or skip without duplicating rows
        report2 = pipeline.run_collector(collector)
        total_obs_2 = in_memory_db.scalar(select(func.count(PriceObservation.id)))

        assert report2.inserted == 0
        assert total_obs_1 == total_obs_2
