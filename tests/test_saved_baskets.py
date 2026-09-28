"""
Integration tests for saved consumer bazaar baskets and 30-day personal CPI trend analysis.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.database import SessionLocal
from app.models.commodity import Commodity


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def sample_commodity_ids():
    """Retrieve existing canonical commodity IDs for Onion and Potato."""
    with SessionLocal() as db:
        onion = db.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
        potato = db.scalars(select(Commodity).where(Commodity.canonical_name == "Potato (Diamond)")).first()
        rice = db.scalars(select(Commodity).where(Commodity.canonical_name == "Rice (Miniket)")).first()
        return {
            "onion_id": onion.id if onion else 1,
            "potato_id": potato.id if potato else 2,
            "rice_id": rice.id if rice else 3,
        }


class TestSavedBasketsAPI:
    """End-to-end tests for saved consumer basket endpoints."""

    def test_create_saved_basket_success(self, client, sample_commodity_ids):
        payload = {
            "name": "My Weekly Family Basket",
            "bangla_name": "আমার সাপ্তাহিক বাজার",
            "description": "Standard test family basket for 4 members",
            "items": [
                {"commodity_id": sample_commodity_ids["onion_id"], "quantity": 2.0, "unit": "kg"},
                {"commodity_id": sample_commodity_ids["potato_id"], "quantity": 3.0, "unit": "kg"},
            ],
        }
        resp = client.post("/api/v1/basket/saved", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        assert "id" in data
        assert data["name"] == "My Weekly Family Basket"
        assert data["bangla_name"] == "আমার সাপ্তাহিক বাজার"
        assert len(data["items"]) == 2
        assert "calculation" in data
        assert data["calculation"]["benchmark_total"] > 0
        assert data["calculation"]["wholesale_total"] > 0
        assert data["calculation"]["retail_total"] > 0
        assert len(data["calculation"]["item_details"]) == 2

    def test_create_saved_basket_invalid_commodity_returns_404(self, client):
        payload = {
            "name": "Invalid Commodity Basket",
            "items": [
                {"commodity_id": 999999, "quantity": 2.0, "unit": "kg"},
            ],
        }
        resp = client.post("/api/v1/basket/saved", json=payload)
        assert resp.status_code == 404

    def test_create_saved_basket_empty_items_returns_422(self, client):
        payload = {
            "name": "Empty Basket",
            "items": [],
        }
        resp = client.post("/api/v1/basket/saved", json=payload)
        assert resp.status_code == 422

    def test_list_saved_baskets(self, client, sample_commodity_ids):
        # Create at least one basket first
        client.post(
            "/api/v1/basket/saved",
            json={
                "name": "List Test Basket",
                "items": [
                    {"commodity_id": sample_commodity_ids["potato_id"], "quantity": 1.0, "unit": "kg"}
                ],
            },
        )
        resp = client.get("/api/v1/basket/saved")
        assert resp.status_code == 200
        data = resp.json()

        assert isinstance(data, list)
        assert len(data) > 0
        first = data[0]
        assert "id" in first
        assert "name" in first
        assert "current_retail_total" in first
        assert "current_wholesale_total" in first
        assert "shift_7d_pct" in first
        assert "shift_30d_pct" in first

    def test_get_saved_basket_detail(self, client, sample_commodity_ids):
        create_resp = client.post(
            "/api/v1/basket/saved",
            json={
                "name": "Detail Test Basket",
                "items": [
                    {"commodity_id": sample_commodity_ids["rice_id"], "quantity": 5.0, "unit": "kg"}
                ],
            },
        )
        basket_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/basket/saved/{basket_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == basket_id
        assert data["name"] == "Detail Test Basket"
        assert len(data["items"]) == 1
        assert data["items"][0]["canonical_name"] == "Rice (Miniket)"
        assert data["items"][0]["line_total"] > 0

    def test_get_nonexistent_saved_basket_returns_404(self, client):
        resp = client.get("/api/v1/basket/saved/999999")
        assert resp.status_code == 404

    def test_basket_30d_trend(self, client, sample_commodity_ids):
        create_resp = client.post(
            "/api/v1/basket/saved",
            json={
                "name": "Trend Analysis Basket",
                "bangla_name": "ট্রেন্ড বাস্কেট",
                "items": [
                    {"commodity_id": sample_commodity_ids["onion_id"], "quantity": 1.0, "unit": "kg"},
                    {"commodity_id": sample_commodity_ids["potato_id"], "quantity": 2.0, "unit": "kg"},
                ],
            },
        )
        basket_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/basket/saved/{basket_id}/trend?days=30")
        assert resp.status_code == 200
        data = resp.json()

        assert data["basket_id"] == basket_id
        assert data["item_count"] == 2
        assert len(data["trend_points"]) == 30
        assert data["current_cost"] > 0
        assert data["baseline_30d_avg"] > 0
        assert data["cheapest_cost"] > 0
        assert data["peak_cost"] >= data["cheapest_cost"]
        assert data["volatility_cv"] >= 0.0
        assert "academic_narrative" in data
        assert len(data["academic_narrative"]) > 20

        # Verify trend point schema
        first_pt = data["trend_points"][0]
        assert "date" in first_pt
        assert first_pt["retail_total"] > 0
        assert first_pt["wholesale_total"] > 0
        assert first_pt["online_total"] > 0

    def test_delete_saved_basket(self, client, sample_commodity_ids):
        create_resp = client.post(
            "/api/v1/basket/saved",
            json={
                "name": "Basket to Delete",
                "items": [
                    {"commodity_id": sample_commodity_ids["potato_id"], "quantity": 1.0, "unit": "kg"}
                ],
            },
        )
        basket_id = create_resp.json()["id"]

        # Delete basket
        del_resp = client.delete(f"/api/v1/basket/saved/{basket_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "ok"

        # Subsequent fetch must return 404
        fetch_resp = client.get(f"/api/v1/basket/saved/{basket_id}")
        assert fetch_resp.status_code == 404

    def test_delete_nonexistent_basket_returns_404(self, client):
        del_resp = client.delete("/api/v1/basket/saved/999999")
        assert del_resp.status_code == 404

    def test_saved_basket_customary_units(self, client, sample_commodity_ids):
        # 1 poa (0.25 kg) onion, 1 hali (4 pc) eggs if present
        payload = {
            "name": "Customary Units Saved Basket",
            "items": [
                {"commodity_id": sample_commodity_ids["onion_id"], "quantity": 1.0, "unit": "পোয়া"},
            ],
        }
        resp = client.post("/api/v1/basket/saved", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        item = data["items"][0]
        assert item["unit"] == "পোয়া"
        assert item["quantity_normalized"] == 0.25
        assert item["standard_unit"] == "kg"
