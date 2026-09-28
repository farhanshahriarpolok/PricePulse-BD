"""
tests/test_national_spatial.py
==============================
Verifies the full 64-District administrative spatial tree,
Spatial Price Dispersion Index D(t), and freight-adjusted arbitrage model.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.commodity import Commodity
from app.models.location import Division, District, Market
from app.services.spatial_service import SpatialService
from scripts.init_db import seed_locations, seed_commodities
from scripts.generate_demo_history import generate_demo_history


@pytest.fixture
def spatial_db():
    test_engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with TestingSession() as session:
        seed_locations(session)
        seed_commodities(session)
        generate_demo_history(session)
        yield session

    Base.metadata.drop_all(bind=test_engine)


class TestNationalSpatialHierarchy:
    """Validate 64-district administrative hierarchy and GeoJSON features."""

    def test_eight_divisions_seeded(self, spatial_db):
        divisions = spatial_db.query(Division).all()
        assert len(divisions) == 8
        div_names = {d.name for d in divisions}
        assert "Dhaka" in div_names
        assert "Chittagong" in div_names
        assert "Rajshahi" in div_names
        assert "Khulna" in div_names
        assert "Barisal" in div_names
        assert "Sylhet" in div_names
        assert "Rangpur" in div_names
        assert "Mymensingh" in div_names

    def test_sixty_four_districts_seeded(self, spatial_db):
        districts = spatial_db.query(District).all()
        assert len(districts) == 64
        dist_names = {d.name for d in districts}
        assert "Bogura" in dist_names
        assert "Cox's Bazar" in dist_names
        assert "Dinajpur" in dist_names
        assert "Jashore" in dist_names

    def test_location_hierarchy_endpoint_service(self, spatial_db):
        service = SpatialService()
        tree = service.get_location_hierarchy(spatial_db)
        assert tree.total_divisions == 8
        assert tree.total_districts == 64
        assert tree.total_markets >= 64


class TestSpatialDispersionAndArbitrage:
    """Validate mathematical computation of Dispersion Index and Arbitrage routes."""

    def test_spatial_dispersion_index_calculated(self, spatial_db):
        service = SpatialService()
        spread = service.get_spatial_spread(spatial_db, "onion_local")
        assert spread is not None
        assert spread.spread_summary.spatial_dispersion_index is not None
        assert spread.spread_summary.spatial_dispersion_index >= 0.0
        assert spread.spread_summary.mean_market_price is not None
        assert spread.spread_summary.mean_market_price > 0.0

    def test_haversine_distance_computation(self):
        # Dhaka (23.8103, 90.4125) to Chattogram (22.3569, 91.7832) ~ 240-280 km with road circuity
        dist = SpatialService.haversine_distance(23.8103, 90.4125, 22.3569, 91.7832)
        assert 230 <= dist <= 310

    def test_spatial_arbitrage_estimator(self, spatial_db):
        service = SpatialService()
        arbitrage = service.get_spatial_arbitrage(spatial_db, "onion_local")
        assert arbitrage is not None
        assert len(arbitrage.production_hubs) > 0
        assert len(arbitrage.consumption_hubs) > 0
        assert len(arbitrage.routes) > 0

        top = arbitrage.routes[0]
        assert top.gross_spread_bdt is not None
        assert top.estimated_freight_cost_bdt > 0.0
        assert top.net_arbitrage_margin_bdt == round(top.gross_spread_bdt - top.estimated_freight_cost_bdt, 2)
        assert top.economic_feasibility in ["Highly Feasible", "Marginal", "Infeasible (Transport Barrier)"]
