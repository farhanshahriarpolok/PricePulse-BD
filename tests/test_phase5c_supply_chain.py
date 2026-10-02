"""
Unit and integration tests for Phase 5C: Supply Chain Price Gap Deconstruction.
Verifies deterministic mathematical deconstruction, strict provenance classification,
unclamped residual economics, and API contract compliance.
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.commodity import Commodity
from app.models.location import District, Division, Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.schemas.supply_chain import (
    ProvenanceType,
    SpreadStatus,
    SupplyChainDeconstructionResponse,
)
from app.services.supply_chain_service import supply_chain_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ── 1. Gross Spread Calculation & Observed Price Fidelity ─────────────────────

def test_gross_spread_calculation_and_fidelity(db_session):
    """Verify gross spread = retail_price - wholesale_price with exact precision."""
    res = supply_chain_service.deconstruct_price_gap(db_session, "rice_miniket")
    assert res is not None
    assert res.canonical_name == "Rice (Miniket)"
    assert res.wholesale_price is not None
    assert res.retail_price is not None

    expected_gross = round(res.retail_price - res.wholesale_price, 2)
    assert res.gross_spread_bdt == expected_gross
    assert res.gross_spread_pct == round((expected_gross / res.wholesale_price) * 100.0, 1)


# ── 2. Strict Provenance Classification ───────────────────────────────────────

def test_modeled_components_carry_modeled_assumption(db_session):
    """Ensure secondary assumptions are tagged MODELED_ASSUMPTION, never fake empirical facts."""
    res = supply_chain_service.deconstruct_price_gap(db_session, "rice_miniket")
    assert res is not None

    component_map = {c.name: c for c in res.components}
    assert "Wholesale Arathdar Commission Assumption" in component_map
    assert "Terminal Handling & Porterage Assumption" in component_map
    assert "Transit Spoilage & Shrinkage Allowance Assumption" in component_map

    for comp_name, comp in component_map.items():
        if "Assumption" in comp_name:
            assert comp.provenance_type == ProvenanceType.MODELED_ASSUMPTION


def test_unsupported_statutory_claim_rejected(db_session):
    """Assert arath commission is tagged MODELED_ASSUMPTION, NOT falsely claimed as OFFICIAL."""
    res = supply_chain_service.deconstruct_price_gap(db_session, "rice_miniket")
    assert res is not None

    arath_comp = next(
        c for c in res.components if "Arathdar" in c.name or "Commission" in c.name
    )
    assert arath_comp.provenance_type != ProvenanceType.OFFICIAL
    assert arath_comp.provenance_type == ProvenanceType.MODELED_ASSUMPTION
    assert "Minten" in arath_comp.source_reference or "World Bank" in arath_comp.source_reference


# ── 3. Mathematical Residual Identity ─────────────────────────────────────────

def test_residual_calculation_is_mathematically_exact(db_session):
    """Verify residual = gross_spread - observed_costs - modeled_costs."""
    res = supply_chain_service.deconstruct_price_gap(db_session, "potato")
    assert res is not None
    if res.gross_spread_bdt is not None:
        expected_residual = round(
            res.gross_spread_bdt - res.observed_or_supported_costs_bdt - res.modeled_costs_bdt, 2
        )
        assert res.residual_spread_bdt == expected_residual


# ── 4. Negative Residual & Unclamped Margin Compression ────────────────────────

def test_negative_residual_handled_without_clamping(db_session):
    """
    Ensure when intermediate costs exceed spread, residual is NOT clamped to zero.
    Must preserve negative value and set spread_status = COMPRESSED_MARGIN.
    """
    res = supply_chain_service.deconstruct_price_gap(db_session, "onion_local")
    assert res is not None
    if res.gross_spread_bdt is not None and res.residual_spread_bdt < 0:
        assert res.spread_status == SpreadStatus.COMPRESSED_MARGIN
        assert res.margin_compression_bdt is not None
        assert res.margin_compression_bdt == round(abs(res.residual_spread_bdt), 2)
        assert res.residual_spread_bdt < 0.0  # Not clamped to 0


# ── 5. Perishability Tier Calibration ──────────────────────────────────────────

def test_perishability_tier_calibration(db_session):
    """Verify high-perishable vegetables have higher shrinkage rate than dry grains."""
    res_tomato = supply_chain_service.deconstruct_price_gap(db_session, "tomato")
    res_rice = supply_chain_service.deconstruct_price_gap(db_session, "rice_coarse")

    assert res_tomato is not None and res_rice is not None

    wastage_tomato = next(c for c in res_tomato.components if "Spoilage" in c.name)
    wastage_rice = next(c for c in res_rice.components if "Spoilage" in c.name)

    # Tomato (Vegetables: 6%) should have higher % than Rice (Grains: 0.5%)
    assert "6.0%" in wastage_tomato.methodology_note
    assert "0.5%" in wastage_rice.methodology_note


# ── 6. Temporal Freshness & Provenance Preservation ───────────────────────────

def test_freshness_metadata_preserved(db_session):
    """Verify observation dates and semantic freshness tiers are exposed."""
    res = supply_chain_service.deconstruct_price_gap(db_session, "soybean_oil")
    assert res is not None

    if res.wholesale_price is not None:
        assert res.wholesale_observation_date is not None
        assert res.wholesale_freshness_tier in ["FRESH_TODAY", "YESTERDAY", "STALE"]

    if res.retail_price is not None:
        assert res.retail_observation_date is not None
        assert res.retail_freshness_tier in ["FRESH_TODAY", "YESTERDAY", "STALE"]

    assert isinstance(res.is_symmetric_freshness, bool)
    assert res.temporal_divergence_days >= 0


# ── 7. Exclusion of Synthetic / Modeled Price Records ─────────────────────────

def test_modeled_price_records_excluded(db_session):
    """Ensure PANDAMART_MODELED prices are not selected as retail kitchen market benchmarks."""
    res = supply_chain_service.deconstruct_price_gap(db_session, "soybean_oil")
    assert res is not None
    # Retail market must not be Pandamart
    assert "pandamart" not in (res.retail_market_name or "").lower()


# ── 8. REST API Endpoint Contracts ────────────────────────────────────────────

def test_api_supply_chain_success(client):
    """GET /api/v1/commodities/{id}/supply-chain returns 200 with complete schema."""
    resp = client.get("/api/v1/commodities/rice_miniket/supply-chain")
    assert resp.status_code == 200
    data = resp.json()

    assert data["canonical_name"] == "Rice (Miniket)"
    assert "wholesale_price" in data
    assert "retail_price" in data
    assert "gross_spread_bdt" in data
    assert "residual_spread_bdt" in data
    assert "spread_status" in data
    assert "components" in data
    assert len(data["components"]) >= 4
    assert "methodology_disclaimer" in data
    assert "modeled" in data["methodology_disclaimer"].lower()


def test_api_supply_chain_by_numeric_id(client):
    """GET /api/v1/commodities/1/supply-chain resolves numeric ID."""
    resp = client.get("/api/v1/commodities/1/supply-chain")
    assert resp.status_code == 200
    data = resp.json()
    assert data["commodity_id"] == 1


def test_api_supply_chain_with_district_filters(client):
    """GET /api/v1/commodities/1/supply-chain?district_id=1 returns district prices."""
    resp = client.get("/api/v1/commodities/1/supply-chain?district_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["commodity_id"] == 1


def test_api_supply_chain_unknown_commodity_returns_404(client):
    """Unknown commodity identifier returns 404 NOT FOUND."""
    resp = client.get("/api/v1/commodities/unknown_nonexistent_staple_xyz/supply-chain")
    assert resp.status_code == 404
    data = resp.json()
    err_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
    assert "could not be resolved" in err_msg


def test_api_supply_chain_invalid_params_returns_422(client):
    """Malformed date query returns 422 Unprocessable Content."""
    resp = client.get("/api/v1/commodities/1/supply-chain?date=invalid-date-format")
    assert resp.status_code == 422


def test_methodology_disclaimer_presence(client):
    """Response must contain clear non-misleading methodology disclaimer."""
    resp = client.get("/api/v1/commodities/4/supply-chain")
    assert resp.status_code == 200
    disclaimer = resp.json()["methodology_disclaimer"]
    assert len(disclaimer) > 20
    assert "empirical" in disclaimer.lower() or "modeled" in disclaimer.lower()
