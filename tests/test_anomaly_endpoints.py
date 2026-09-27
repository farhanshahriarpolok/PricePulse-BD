"""
Integration tests for anomaly detection and spatial spread API endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestAnomalyEndpoints:
    """Test anomaly monitoring and explainability endpoints."""

    def test_get_active_anomalies(self, client):
        response = client.get("/api/v1/anomalies/active")
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data
        assert "anomalies_detected" in data
        assert data["total_monitored"] > 0

        # Onion price shock should be actively detected
        onion_anomalies = [a for a in data["anomalies"] if a["canonical_name"] == "Onion (Local)"]
        assert len(onion_anomalies) > 0
        onion_alert = onion_anomalies[0]
        assert onion_alert["is_anomaly"] is True
        assert onion_alert["anomaly_severity"] in ["Moderate", "Severe", "Critical"]
        assert onion_alert["metrics"]["z_score_14d"] >= 1.5
        assert "Anomalous market pressure detected" in onion_alert["explanation"]

    def test_explain_commodity_anomaly_by_id(self, client):
        response = client.get("/api/v1/anomalies/1/explain")
        assert response.status_code == 200
        data = response.json()
        assert data["commodity_id"] == 1
        assert "metrics" in data
        assert data["metrics"]["current_price"] > 0
        assert "explanation" in data

    def test_explain_commodity_anomaly_by_alias(self, client):
        response = client.get("/api/v1/anomalies/onion_local/explain")
        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "Onion (Local)"

    def test_explain_nonexistent_commodity_returns_404(self, client):
        response = client.get("/api/v1/anomalies/nonexistent_xyz_999/explain")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


class TestSpatialEndpoints:
    """Test spatial spread and location hierarchy endpoints."""

    def test_spatial_spread_by_alias(self, client):
        response = client.get("/api/v1/locations/spread?commodity_id=onion_local")
        assert response.status_code == 200
        data = response.json()
        assert data["canonical_name"] == "Onion (Local)"
        assert "spread_summary" in data
        assert data["spread_summary"]["cheapest_price"] > 0
        assert data["spread_summary"]["highest_price"] >= data["spread_summary"]["cheapest_price"]
        assert len(data["districts"]) > 0
        assert "geojson_feature_collection" in data
        assert data["geojson_feature_collection"]["type"] == "FeatureCollection"

    def test_spatial_spread_by_id(self, client):
        response = client.get("/api/v1/locations/spread?commodity_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["commodity_id"] == 1

    def test_spatial_spread_unmapped_returns_404(self, client):
        response = client.get("/api/v1/locations/spread?commodity_id=unknown_xyz_random")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"

    def test_get_location_hierarchy(self, client):
        response = client.get("/api/v1/locations/hierarchy")
        assert response.status_code == 200
        data = response.json()
        assert data["total_divisions"] >= 2
        assert data["total_districts"] >= 2
        assert data["total_markets"] >= 5
        assert len(data["divisions"]) >= 2
