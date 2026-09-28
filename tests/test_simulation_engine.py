"""
tests/test_simulation_engine.py
================================
Verifies the Viva Defense Simulation Sandbox REST endpoint, mathematical
recalculation of Rolling 14-day SMA, Z-Scores, anomaly classifications,
and non-destructive database preservation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from app.main import app
from app.core.database import SessionLocal
from app.models.commodity import Commodity
from app.models.observation import PriceObservation


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestSimulationEngine:
    """Mathematical and state integrity verification for viva simulation sandbox."""

    def test_simulation_inject_positive_supply_shock(self, client):
        with SessionLocal() as session:
            onion = session.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
            comm_id = onion.id

        payload = {
            "commodity_id": comm_id,
            "shock_percentage": 45.0,
            "shock_duration_days": 4,
            "shock_type": "Supply Disruption",
            "baseline_adjustment_pct": 0.0,
            "noise_level": 0.0,
        }

        resp = client.post("/api/v1/simulation/inject-shock", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["commodity_id"] == comm_id
        assert data["canonical_name"] == "Onion (Local)"
        assert data["simulated_price"] > data["baseline_price"]
        assert data["shock_percentage"] == 45.0
        assert data["shock_duration_days"] == 4
        assert data["is_anomaly"] is True
        assert data["anomaly_direction"] == "Spike"
        assert data["anomaly_severity"] in ["Moderate", "Severe", "Critical"]
        assert data["metrics"]["z_score_14d"] is not None
        assert data["metrics"]["z_score_14d"] >= 1.5
        assert "Supply Disruption" in data["impact_assessment"]
        assert len(data["time_series"]) > 0

        # Verify shock period flags
        shock_points = [p for p in data["time_series"] if p["is_shock_period"]]
        assert len(shock_points) == 4

    def test_simulation_negative_shock_price_collapse(self, client):
        with SessionLocal() as session:
            potato = session.scalars(select(Commodity).where(Commodity.canonical_name == "Potato (Diamond)")).first()
            comm_id = potato.id

        payload = {
            "commodity_id": comm_id,
            "shock_percentage": -35.0,
            "shock_duration_days": 3,
            "shock_type": "Bumper Harvest",
            "baseline_adjustment_pct": 0.0,
            "noise_level": 0.0,
        }

        resp = client.post("/api/v1/simulation/inject-shock", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["simulated_price"] < data["baseline_price"]
        assert data["is_anomaly"] is True
        assert data["anomaly_direction"] == "Drop"
        assert data["metrics"]["percentage_change_14d"] < -10.0

    def test_simulation_preserves_database_integrity(self, client):
        with SessionLocal() as session:
            onion = session.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
            comm_id = onion.id

            # Ground truth count and avg price before simulation
            count_before = session.scalar(
                select(func.count(PriceObservation.id)).where(PriceObservation.commodity_id == comm_id)
            )
            avg_before = session.scalar(
                select(func.avg(PriceObservation.normalized_price)).where(PriceObservation.commodity_id == comm_id)
            )

        payload = {
            "commodity_id": comm_id,
            "shock_percentage": 100.0,  # Extreme +100% shock
            "shock_duration_days": 7,
            "shock_type": "Cartel Hoarding",
            "baseline_adjustment_pct": 20.0,
            "noise_level": 5.0,
        }

        resp = client.post("/api/v1/simulation/inject-shock", json=payload)
        assert resp.status_code == 200

        # Verify DB remained 100% unaltered
        with SessionLocal() as session:
            count_after = session.scalar(
                select(func.count(PriceObservation.id)).where(PriceObservation.commodity_id == comm_id)
            )
            avg_after = session.scalar(
                select(func.avg(PriceObservation.normalized_price)).where(PriceObservation.commodity_id == comm_id)
            )

            assert count_after == count_before
            assert round(float(avg_after), 4) == round(float(avg_before), 4)

    def test_simulation_invalid_commodity_returns_404(self, client):
        payload = {
            "commodity_id": 99999,
            "shock_percentage": 20.0,
            "shock_duration_days": 3,
            "shock_type": "Supply Disruption",
        }
        resp = client.post("/api/v1/simulation/inject-shock", json=payload)
        assert resp.status_code == 404

    def test_simulation_with_noise_injection(self, client):
        with SessionLocal() as session:
            rice = session.scalars(select(Commodity).where(Commodity.canonical_name == "Rice (Miniket)")).first()
            comm_id = rice.id

        payload = {
            "commodity_id": comm_id,
            "shock_percentage": 20.0,
            "shock_duration_days": 5,
            "shock_type": "Transport Strike",
            "baseline_adjustment_pct": 5.0,
            "noise_level": 8.0,
        }
        resp = client.post("/api/v1/simulation/inject-shock", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["commodity_id"] == comm_id
        assert len(data["time_series"]) > 0

    def test_simulation_boundary_durations(self, client):
        with SessionLocal() as session:
            egg = session.scalars(select(Commodity).where(Commodity.canonical_name == "Farm Egg")).first()
            comm_id = egg.id

        # 1-day shock
        resp1 = client.post("/api/v1/simulation/inject-shock", json={
            "commodity_id": comm_id,
            "shock_percentage": 15.0,
            "shock_duration_days": 1,
            "shock_type": "Import Tariff",
        })
        assert resp1.status_code == 200
        shock1 = [p for p in resp1.json()["time_series"] if p["is_shock_period"]]
        assert len(shock1) == 1

        # 14-day shock
        resp14 = client.post("/api/v1/simulation/inject-shock", json={
            "commodity_id": comm_id,
            "shock_percentage": 25.0,
            "shock_duration_days": 14,
            "shock_type": "Supply Disruption",
        })
        assert resp14.status_code == 200
        shock14 = [p for p in resp14.json()["time_series"] if p["is_shock_period"]]
        assert len(shock14) == 14

    def test_arbitrage_endpoint_integration(self, client):
        resp = client.get("/api/v1/locations/arbitrage?commodity_id=onion_local")
        assert resp.status_code == 200
        data = resp.json()
        assert data["canonical_name"] == "Onion (Local)"
        assert len(data["production_hubs"]) > 0
        assert len(data["consumption_hubs"]) > 0
        assert len(data["routes"]) > 0
        assert data["routes"][0]["gross_spread_bdt"] is not None
        assert data["routes"][0]["estimated_freight_cost_bdt"] > 0

    def test_simulation_negative_impact_assessment(self, client):
        with SessionLocal() as session:
            potato = session.scalars(select(Commodity).where(Commodity.canonical_name == "Potato (Diamond)")).first()
            comm_id = potato.id

        resp = client.post("/api/v1/simulation/inject-shock", json={
            "commodity_id": comm_id,
            "shock_percentage": -20.0,
            "shock_duration_days": 3,
            "shock_type": "Bumper Harvest",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "producer profitability" in data["impact_assessment"]

    def test_simulation_zero_shock_equilibrium_assessment(self, client):
        with SessionLocal() as session:
            onion = session.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
            comm_id = onion.id

        resp = client.post("/api/v1/simulation/inject-shock", json={
            "commodity_id": comm_id,
            "shock_percentage": 0.0,
            "shock_duration_days": 3,
            "shock_type": "Equilibrium",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "baseline equilibrium" in data["impact_assessment"]

