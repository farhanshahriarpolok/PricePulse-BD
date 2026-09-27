"""
Unit and integration tests for manual field spot price reporting endpoint.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.database import SessionLocal
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.observation import PriceObservation
from app.models.source import Source


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def sample_ids():
    with SessionLocal() as db:
        chicken = db.scalars(select(Commodity).where(Commodity.canonical_name == "Broiler Chicken")).first()
        egg = db.scalars(select(Commodity).where(Commodity.canonical_name == "Farm Egg")).first()
        market = db.scalars(select(Market)).first()
        assert chicken is not None, "Broiler Chicken must be seeded in database"
        assert egg is not None, "Farm Egg must be seeded in database"
        assert market is not None, "At least one market must be seeded in database"
        return {
            "chicken_id": chicken.id,
            "egg_id": egg.id,
            "market_id": market.id,
        }


class TestManualIngestionValidation:
    """Test payload validation constraints for field submissions."""

    def test_negative_or_zero_price_rejected(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["chicken_id"],
            "market_id": sample_ids["market_id"],
            "price": 0.0,
            "raw_unit": "kg",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 422

    def test_invalid_commodity_id_returns_404(self, client, sample_ids):
        payload = {
            "commodity_id": 999999,
            "market_id": sample_ids["market_id"],
            "price": 180.0,
            "raw_unit": "kg",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 404
        data = res.json()
        msg = data.get("detail") or data.get("error", {}).get("message", "")
        assert "does not exist" in msg

    def test_invalid_market_id_returns_404(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["chicken_id"],
            "market_id": 999999,
            "price": 180.0,
            "raw_unit": "kg",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 404

    def test_unsupported_unit_returns_422(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["chicken_id"],
            "market_id": sample_ids["market_id"],
            "price": 180.0,
            "raw_unit": "alien_galactic_unit_xyz",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 422
        data = res.json()
        msg = data.get("detail") or data.get("error", {}).get("message", "")
        assert "Unit normalization failed" in msg



class TestManualIngestionPersistence:
    """Test successful persistence, unit normalization, and confidence scoring."""

    def test_submit_standard_kg_price(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["chicken_id"],
            "market_id": sample_ids["market_id"],
            "price": 195.0,
            "raw_unit": "কেজি",
            "market_tier": "retail",
            "reporter_note": "Morning price observed at Karwan Bazar",
            "reporter_name": "Inspector Field Test",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["normalized_price"] == 195.0
        assert data["normalized_unit"] == "kg"
        assert data["price_type"] == "retail_avg"
        assert data["source_code"] == "field_report"
        # Calibrated Tier 4 confidence (0.4*0.6 + 0.3*1.0 + 0.15*1.0 + 0.15*1.0 = 0.84)
        assert data["confidence_score"] == 0.84

    def test_submit_hali_egg_price_normalizes_to_piece(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["egg_id"],
            "market_id": sample_ids["market_id"],
            "price": 52.0,
            "raw_unit": "হালি",
            "market_tier": "retail",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        # 52 BDT for 1 hali (4 pcs) -> 13.00 BDT/pc
        assert data["normalized_price"] == 13.0
        assert data["normalized_unit"] == "pc"

    def test_submit_dozen_egg_price_normalizes_to_piece(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["egg_id"],
            "market_id": sample_ids["market_id"],
            "price": 156.0,
            "raw_unit": "ডজন",
            "market_tier": "retail",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        # 156 BDT for 1 dozen (12 pcs) -> 13.00 BDT/pc
        assert data["normalized_price"] == 13.0
        assert data["normalized_unit"] == "pc"

    def test_submit_wholesale_tier_sets_wholesale_avg(self, client, sample_ids):
        payload = {
            "commodity_id": sample_ids["chicken_id"],
            "market_id": sample_ids["market_id"],
            "price": 175.0,
            "raw_unit": "kg",
            "market_tier": "wholesale",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["price_type"] == "wholesale_avg"
        assert data["normalized_price"] == 175.0

    def test_db_persistence_verification(self, client, sample_ids):
        with SessionLocal() as db:
            src = db.scalars(select(Source).where(Source.code == "field_report")).first()
            assert src is not None
            assert src.reliability_score == 0.60

            obs = db.scalars(
                select(PriceObservation)
                .where(
                    PriceObservation.commodity_id == sample_ids["chicken_id"],
                    PriceObservation.source_id == src.id,
                )
            ).first()
            assert obs is not None
            assert obs.confidence_score == 0.84
