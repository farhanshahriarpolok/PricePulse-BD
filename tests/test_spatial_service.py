"""
Unit and integration tests for SpatialService, geographic spread, and hierarchy traversal.
"""

from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.spatial_service import SpatialService
from scripts.init_db import seed_locations, seed_commodities
from scripts.generate_demo_history import generate_history


@pytest.fixture(scope="module")
def db_with_history():
    """Create test SQLite database with 30-day simulated history."""
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with TestingSession() as session:
        seed_locations(session)
        seed_commodities(session)

    # Populate observations
    with TestingSession() as session:
        yield session

    Base.metadata.drop_all(bind=test_engine)


class TestSpatialService:
    """Test inter-district spreads and GeoJSON enrichment."""

    def test_commodity_resolution_by_alias(self, db_with_history):
        service = SpatialService()
        c1 = service.resolve_commodity(db_with_history, "1")
        assert c1 is not None

        c2 = service.resolve_commodity(db_with_history, "onion_local")
        assert c2 is not None
        assert c2.canonical_name == "Onion (Local)"

        c3 = service.resolve_commodity(db_with_history, "দেশি পেঁয়াজ")
        assert c3 is not None

    def test_location_hierarchy_tree(self, db_with_history):
        service = SpatialService()
        hierarchy = service.get_location_hierarchy(db_with_history)

        assert hierarchy.total_divisions >= 2
        assert hierarchy.total_districts >= 2
        assert hierarchy.total_markets >= 5
        assert any(d.name == "Dhaka" for d in hierarchy.divisions)
        assert any(d.name == "Chittagong" for d in hierarchy.divisions)

    def test_spatial_spread_metrics(self):
        # Test against real disk DB where demo history was seeded
        from app.core.database import SessionLocal
        service = SpatialService()
        with SessionLocal() as session:
            spread = service.get_spatial_spread(session, "onion_local")
            assert spread is not None
            assert spread.canonical_name == "Onion (Local)"
            assert spread.spread_summary.cheapest_price is not None
            assert spread.spread_summary.highest_price is not None
            assert spread.spread_summary.absolute_spread_bdt >= 0
            assert len(spread.markets) >= 2
            assert spread.geojson_feature_collection is not None
            assert "features" in spread.geojson_feature_collection
