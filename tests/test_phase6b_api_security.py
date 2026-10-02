"""
tests/test_phase6b_api_security.py
==================================
Comprehensive test suite for Phase 6B: API Security Safeguards (Admin API Key Authentication).

Verifies:
1. POST /api/v1/observations/manual requires valid X-API-Key header.
2. POST /api/v1/system/sync requires valid X-API-Key header.
3. Missing or wrong key returns HTTP 401 Unauthorized.
4. Correct key allows normal operation.
5. Fail-closed behavior: When PRICEPULSE_ADMIN_API_KEY is unset or empty, requests return 401.
6. Public endpoints (GET /health, GET /api/v1/system/sources, POST /api/v1/simulation/inject-shock, etc.)
   remain fully accessible without authentication.
7. Timing-safe comparison via secrets.compare_digest.
8. Sensitive key material is never leaked in HTTP error responses or logs.
9. OpenAPI documentation accurately reflects the security scheme and requirement.
"""

import os
import secrets
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.core.security import require_admin_api_key, API_KEY_HEADER_NAME
from app.core.database import SessionLocal
from app.models.commodity import Commodity
from app.models.location import Market

TEST_KEY = "test-phase6b-secure-admin-token-xyz789"
WRONG_KEY = "wrong-admin-token-attempt"


def _extract_error_message(response) -> str:
    """Extract message string regardless of standard FastAPI or custom error envelope."""
    data = response.json()
    if isinstance(data, dict):
        if "error" in data and isinstance(data["error"], dict):
            return data["error"].get("message", "")
        return data.get("detail", "")
    return str(data)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_ids():
    with SessionLocal() as db:
        chicken = db.scalars(select(Commodity).where(Commodity.canonical_name == "Broiler Chicken")).first()
        market = db.scalars(select(Market)).first()
        assert chicken is not None
        assert market is not None
        return {
            "commodity_id": chicken.id,
            "market_id": market.id,
        }


class TestManualObservationSecurity:
    """Authentication behavior for POST /api/v1/observations/manual."""

    def test_missing_api_key_returns_401(self, client, sample_ids, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        payload = {
            "commodity_id": sample_ids["commodity_id"],
            "market_id": sample_ids["market_id"],
            "price": 185.0,
            "raw_unit": "kg",
        }
        res = client.post("/api/v1/observations/manual", json=payload)
        assert res.status_code == 401
        assert "WWW-Authenticate" in res.headers
        assert res.headers["WWW-Authenticate"] == API_KEY_HEADER_NAME
        msg = _extract_error_message(res)
        assert "Missing" in msg or "required" in msg
        assert TEST_KEY not in msg

    def test_wrong_api_key_returns_401(self, client, sample_ids, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        payload = {
            "commodity_id": sample_ids["commodity_id"],
            "market_id": sample_ids["market_id"],
            "price": 185.0,
            "raw_unit": "kg",
        }
        res = client.post(
            "/api/v1/observations/manual",
            json=payload,
            headers={API_KEY_HEADER_NAME: WRONG_KEY},
        )
        assert res.status_code == 401
        msg = _extract_error_message(res)
        assert "Invalid" in msg
        assert TEST_KEY not in msg
        assert WRONG_KEY not in msg

    def test_empty_api_key_returns_401(self, client, sample_ids, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        payload = {
            "commodity_id": sample_ids["commodity_id"],
            "market_id": sample_ids["market_id"],
            "price": 185.0,
            "raw_unit": "kg",
        }
        res = client.post(
            "/api/v1/observations/manual",
            json=payload,
            headers={API_KEY_HEADER_NAME: ""},
        )
        assert res.status_code == 401
        msg = _extract_error_message(res)
        assert TEST_KEY not in msg

    def test_correct_api_key_allows_submission(self, client, sample_ids, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        payload = {
            "commodity_id": sample_ids["commodity_id"],
            "market_id": sample_ids["market_id"],
            "price": 190.0,
            "raw_unit": "kg",
            "market_tier": "retail",
            "reporter_name": "Phase 6B Auth Validator",
        }
        res = client.post(
            "/api/v1/observations/manual",
            json=payload,
            headers={API_KEY_HEADER_NAME: TEST_KEY},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["normalized_price"] == 190.0
        assert data["source_code"] == "field_report"


class TestSystemSyncSecurity:
    """Authentication behavior for POST /api/v1/system/sync."""

    def test_missing_api_key_returns_401(self, client, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        res = client.post("/api/v1/system/sync")
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == API_KEY_HEADER_NAME
        msg = _extract_error_message(res)
        assert TEST_KEY not in msg

    def test_wrong_api_key_returns_401(self, client, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        res = client.post(
            "/api/v1/system/sync",
            headers={API_KEY_HEADER_NAME: WRONG_KEY},
        )
        assert res.status_code == 401
        msg = _extract_error_message(res)
        assert "Invalid" in msg
        assert TEST_KEY not in msg

    def test_correct_api_key_allows_sync(self, client, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", TEST_KEY)
        res = client.post(
            "/api/v1/system/sync",
            headers={API_KEY_HEADER_NAME: TEST_KEY},
        )
        assert res.status_code in [200, 202]
        data = res.json()
        assert "task_id" in data
        assert data["status"] in ["in_progress", "completed"]


class TestFailClosedBehavior:
    """Fail-closed safeguards when PRICEPULSE_ADMIN_API_KEY is not configured."""

    def test_unset_key_blocks_mutation_endpoints(self, client, sample_ids, monkeypatch):
        # Unset env var
        monkeypatch.delenv("PRICEPULSE_ADMIN_API_KEY", raising=False)
        assert settings.admin_api_key == ""

        # Attempt manual observation even with a putative key
        res_obs = client.post(
            "/api/v1/observations/manual",
            json={
                "commodity_id": sample_ids["commodity_id"],
                "market_id": sample_ids["market_id"],
                "price": 180.0,
                "raw_unit": "kg",
            },
            headers={API_KEY_HEADER_NAME: "any-arbitrary-key"},
        )
        assert res_obs.status_code == 401
        msg_obs = _extract_error_message(res_obs)
        assert "not configured" in msg_obs

        # Attempt system sync
        res_sync = client.post(
            "/api/v1/system/sync",
            headers={API_KEY_HEADER_NAME: "any-arbitrary-key"},
        )
        assert res_sync.status_code == 401
        msg_sync = _extract_error_message(res_sync)
        assert "not configured" in msg_sync

    def test_empty_string_key_blocks_mutation_endpoints(self, client, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", "   ")
        assert settings.admin_api_key == ""

        res = client.post("/api/v1/system/sync", headers={API_KEY_HEADER_NAME: "   "})
        assert res.status_code == 401
        msg = _extract_error_message(res)
        assert "not configured" in msg


class TestPublicEndpointsRemainAccessible:
    """Ensure public read and simulation endpoints remain accessible without auth."""

    def test_health_endpoint_public(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["ok", "healthy"]

    def test_system_sources_endpoint_public(self, client):
        res = client.get("/api/v1/system/sources")
        assert res.status_code == 200
        data = res.json()
        assert "sources" in data
        assert data["status"] == "operational"

    def test_system_sync_list_and_poll_public(self, client):
        res = client.get("/api/v1/system/sync")
        assert res.status_code == 200
        assert "tasks" in res.json()

    def test_commodities_public(self, client):
        res = client.get("/api/v1/commodities")
        assert res.status_code == 200

    def test_pulse_today_public(self, client):
        res = client.get("/api/v1/pulse/today")
        assert res.status_code == 200

    def test_simulation_shock_remains_public(self, client):
        """Simulation sandbox remains public (guarded by Nginx rate limiting, not API key)."""
        res = client.post(
            "/api/v1/simulation/inject-shock",
            json={
                "commodity_id": "1",
                "shock_percentage": 10.0,
                "duration_days": 7,
            },
        )
        # Should NOT return 401 Unauthorized
        assert res.status_code != 401
        assert res.status_code in [200, 404, 422]


class TestSecurityInternalsAndOpenAPI:
    """Internal security architecture validation."""

    def test_timing_safe_comparison_invoked(self, monkeypatch):
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", "safe-expected-key")

        with patch("secrets.compare_digest", wraps=secrets.compare_digest) as mock_compare:
            # Test valid key
            key = require_admin_api_key(provided_key="safe-expected-key")
            assert key == "safe-expected-key"
            assert mock_compare.called
            assert mock_compare.call_args[0] == ("safe-expected-key", "safe-expected-key")

    def test_openapi_schema_contains_security_definition(self):
        schema = app.openapi()
        # Verify security schemes
        security_schemes = schema.get("components", {}).get("securitySchemes", {})
        assert "APIKeyHeader" in security_schemes
        sec_meta = security_schemes["APIKeyHeader"]
        assert sec_meta["type"] == "apiKey"
        assert sec_meta["name"] == "X-API-Key"
        assert sec_meta["in"] == "header"

        # Verify mutation endpoints require security
        paths = schema.get("paths", {})
        manual_post = paths.get("/api/v1/observations/manual", {}).get("post", {})
        assert "security" in manual_post
        assert {"APIKeyHeader": []} in manual_post["security"]

        sync_post = paths.get("/api/v1/system/sync", {}).get("post", {})
        assert "security" in sync_post
        assert {"APIKeyHeader": []} in sync_post["security"]

        # Verify public endpoints have no security requirement
        health_get = paths.get("/health", {}).get("get", {})
        assert "security" not in health_get or not health_get["security"]

        sources_get = paths.get("/api/v1/system/sources", {}).get("get", {})
        assert "security" not in sources_get or not sources_get["security"]
