"""
tests/test_phase2_spatial_consumer.py
=======================================
Phase 2C: Unit and integration tests for the consumer-facing spatial
opportunity endpoint and the enhanced ArbitrageRoute schema fields.

Tests:
  1. ArbitrageRoute carries calculation_unit and data_provenance.
  2. get_consumer_opportunity() returns ConsumerOpportunityResponse.
  3. has_opportunity is True when best net margin >= 2.0.
  4. has_opportunity is False (equilibrium) handled without raising.
  5. FreightBreakdownDetail fields are mathematically consistent.
  6. /api/v1/locations/consumer-opportunity HTTP endpoint returns 200.
  7. /api/v1/locations/consumer-opportunity returns 404 for unknown commodity.
  8. Calculation unit matches commodity.default_unit (no hardcoded 'kg').
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.commodity import Commodity
from app.models.location import Division, District, Market
from app.services.spatial_service import SpatialService
from scripts.init_db import seed_locations, seed_commodities
from scripts.generate_demo_history import generate_demo_history


# ── Shared test DB fixture ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def phase2_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with TestSession() as session:
        seed_locations(session)
        seed_commodities(session)
        generate_demo_history(session)

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def phase2_db(phase2_engine):
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=phase2_engine)
    with TestSession() as session:
        yield session


@pytest.fixture(scope="module")
def phase2_client(phase2_engine):
    """TestClient with the shared in-memory DB injected via clean session generator."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=phase2_engine)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()



# ── Phase 2A: ArbitrageRoute schema enhancement ───────────────────────────────

class TestArbitrageRoutePhase2Fields:
    """Verify new Phase 2 fields on ArbitrageRoute are present and correct."""

    def test_arbitrage_route_has_calculation_unit(self, phase2_db):
        service = SpatialService()
        result = service.get_spatial_arbitrage(phase2_db, "onion_local")
        assert result is not None
        assert len(result.routes) > 0
        for route in result.routes:
            assert hasattr(route, "calculation_unit"), "Route must carry calculation_unit"
            assert route.calculation_unit in ("kg", "liter", "pc", "bundle"), (
                f"Unexpected calculation_unit: '{route.calculation_unit}'"
            )

    def test_arbitrage_route_has_data_provenance(self, phase2_db):
        service = SpatialService()
        result = service.get_spatial_arbitrage(phase2_db, "onion_local")
        assert result is not None
        for route in result.routes:
            assert hasattr(route, "data_provenance"), "Route must carry data_provenance"
            assert route.data_provenance in ("LIVE", "FALLBACK", "MODELED", "STALE"), (
                f"Unexpected data_provenance: '{route.data_provenance}'"
            )

    def test_calculation_unit_matches_commodity_default_unit(self, phase2_db):
        """Calculation unit must match commodity.default_unit — never hardcoded."""
        service = SpatialService()
        commodity = service.resolve_commodity(phase2_db, "onion_local")
        assert commodity is not None
        result = service.get_spatial_arbitrage(phase2_db, "onion_local")
        assert result is not None
        for route in result.routes:
            assert route.calculation_unit == commodity.default_unit, (
                f"Route calculation_unit '{route.calculation_unit}' "
                f"!= commodity.default_unit '{commodity.default_unit}'"
            )


# ── Phase 2A: ConsumerOpportunityResponse ─────────────────────────────────────

class TestConsumerOpportunityResponse:
    """Verify get_consumer_opportunity() returns valid ConsumerOpportunityResponse."""

    def test_returns_consumer_opportunity_response(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert opp is not None, "get_consumer_opportunity must not return None for seeded data"

    def test_has_opportunity_is_boolean(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert isinstance(opp.has_opportunity, bool)

    def test_opportunity_summary_is_non_empty_string(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert isinstance(opp.opportunity_summary, str)
        assert len(opp.opportunity_summary) > 10

    def test_calculation_unit_present(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert opp.calculation_unit in ("kg", "liter", "pc", "bundle")

    def test_data_provenance_present(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert opp.data_provenance in ("LIVE", "FALLBACK", "MODELED", "STALE")

    def test_commodity_fields_correct(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert opp.commodity_id > 0
        assert len(opp.canonical_name) > 0
        assert len(opp.bangla_name) > 0

    def test_observation_date_present(self, phase2_db):
        import datetime
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert isinstance(opp.observation_date, datetime.date)

    def test_all_routes_count_matches_backend(self, phase2_db):
        service = SpatialService()
        full = service.get_spatial_arbitrage(phase2_db, "onion_local")
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert opp.all_routes_count == len(full.routes)

    def test_top_routes_length_at_most_five(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        assert len(opp.top_routes) <= 5

    def test_net_opportunity_math_consistent(self, phase2_db):
        """net_opportunity = gross_difference - transport_cost (within floating-point tolerance)."""
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        if (
            opp.net_opportunity_bdt is not None
            and opp.gross_difference_bdt is not None
            and opp.transport_cost_bdt is not None
        ):
            expected_net = round(opp.gross_difference_bdt - opp.transport_cost_bdt, 2)
            assert abs(opp.net_opportunity_bdt - expected_net) < 0.05, (
                f"Net opportunity math mismatch: "
                f"{opp.net_opportunity_bdt} != {expected_net}"
            )

    def test_when_has_opportunity_true_net_is_positive(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        if opp.has_opportunity:
            assert opp.net_opportunity_bdt is not None
            assert opp.net_opportunity_bdt >= 2.0, (
                "has_opportunity=True but net margin < 2.0 threshold"
            )

    def test_freight_detail_present_when_opportunity_exists(self, phase2_db):
        service = SpatialService()
        opp = service.get_consumer_opportunity(phase2_db, "onion_local")
        if opp.has_opportunity:
            assert opp.freight_detail is not None
            fd = opp.freight_detail
            assert fd.total_freight_bdt > 0
            assert fd.distance_km > 0
            assert fd.transit_hours > 0
            # Total freight must approximately equal component sum
            component_sum = round(
                fd.base_loading_bdt + fd.distance_cost_bdt + fd.toll_and_bridge_bdt, 2
            )
            assert abs(fd.total_freight_bdt - component_sum) < 0.20, (
                f"Freight components don't sum to total: "
                f"{component_sum} vs {fd.total_freight_bdt}"
            )

    def test_unknown_commodity_returns_none(self, phase2_db):
        service = SpatialService()
        result = service.get_consumer_opportunity(phase2_db, "nonexistent_xyzabc")
        assert result is None


# ── Phase 2A: HTTP endpoint test ──────────────────────────────────────────────

class TestConsumerOpportunityEndpoint:
    """Integration tests for GET /api/v1/locations/consumer-opportunity."""

    def test_endpoint_returns_200(self, phase2_client):
        resp = phase2_client.get("/api/v1/locations/consumer-opportunity?commodity_id=onion_local")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_endpoint_response_schema(self, phase2_client):
        resp = phase2_client.get("/api/v1/locations/consumer-opportunity?commodity_id=onion_local")
        assert resp.status_code == 200
        data = resp.json()
        # Consumer-layer required fields
        assert "has_opportunity" in data
        assert "opportunity_summary" in data
        assert "calculation_unit" in data
        assert "data_provenance" in data
        assert "observation_date" in data
        assert "all_routes_count" in data
        assert isinstance(data["has_opportunity"], bool)
        assert data["calculation_unit"] in ("kg", "liter", "pc", "bundle")
        assert data["data_provenance"] in ("LIVE", "FALLBACK", "MODELED", "STALE")

    def test_endpoint_404_for_unknown_commodity(self, phase2_client):
        resp = phase2_client.get(
            "/api/v1/locations/consumer-opportunity?commodity_id=does_not_exist_zzz"
        )
        assert resp.status_code == 404

    def test_endpoint_numeric_id_resolves(self, phase2_client):
        """Numeric commodity_id must resolve via the existing resolve_commodity path."""
        resp = phase2_client.get("/api/v1/locations/consumer-opportunity?commodity_id=1")
        # Should be 200 (commodity 1 is seeded) or 404 (if not seeded) — not 422 or 500
        assert resp.status_code in (200, 404), f"Unexpected status: {resp.status_code}"

    def test_endpoint_top_routes_at_most_five(self, phase2_client):
        resp = phase2_client.get("/api/v1/locations/consumer-opportunity?commodity_id=onion_local")
        if resp.status_code == 200:
            data = resp.json()
            assert len(data.get("top_routes", [])) <= 5
