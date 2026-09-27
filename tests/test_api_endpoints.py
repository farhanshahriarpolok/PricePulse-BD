"""
API endpoint integration tests using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestSystemEndpoints:
    """Test health check and root endpoints."""

    def test_health_check_v1(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "PricePulse BD"
        assert data["version"] == "0.2.0"

    def test_health_check_root(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestRealtimeSearchEndpoints:
    """Test on-demand search and market pulse endpoints."""

    def test_realtime_search_onion(self, client):
        response = client.get("/api/v1/search/realtime?query=onion")
        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "Onion (Local)"
        assert data["price_summary"]["avg_price"] > 0
        assert "channels" in data
        assert "wholesale_avg" in data["channels"]
        assert data["price_status"] in ["Normal", "Elevated", "High"]
        assert data["freshness"]["status"] in ["fresh", "realtime_ingested"]
        assert len(data["observations"]) > 0

    def test_realtime_search_bengali_query(self, client):
        response = client.get("/api/v1/search/realtime?query=আলু")
        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "Potato (Diamond)"
        assert data["price_summary"]["min_price"] > 0

    def test_realtime_search_unmapped_returns_404(self, client):
        response = client.get("/api/v1/search/realtime?query=unknown_crypto_item_123")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "NOT_FOUND"

    def test_daily_pulse_today(self, client):
        response = client.get("/api/v1/pulse/today")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tracked"] > 0
        assert len(data["items"]) > 0
        first = data["items"][0]
        assert "canonical_name" in first
        assert "price_summary" in first


class TestCommoditiesEndpoints:
    """Test commodity catalog and historical series endpoints."""

    def test_list_commodities(self, client):
        response = client.get("/api/v1/commodities")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        assert len(data["items"]) >= 4

    def test_list_commodities_filtered_by_category(self, client):
        response = client.get("/api/v1/commodities?category=Vegetables")
        assert response.status_code == 200
        data = response.json()
        assert all(item["category"] == "Vegetables" for item in data["items"])

    def test_get_commodity_detail_success(self, client):
        response = client.get("/api/v1/commodities/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "aliases" in data
        assert len(data["aliases"]) > 0

    def test_get_commodity_detail_not_found(self, client):
        response = client.get("/api/v1/commodities/999999")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_commodity_history(self, client):
        response = client.get("/api/v1/commodities/1/history")
        assert response.status_code == 200
        data = response.json()
        assert data["commodity_id"] == 1
        assert "series" in data
