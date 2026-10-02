"""
Tests for SourceHealthService, system endpoints (/api/v1/system/sources, /api/v1/system/sync),
and async background task execution.
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.source_health import SourceHealthService, source_health_service
from app.services.scheduler import sync_scheduler


client = TestClient(app)


class TestSourceHealthServiceUnit:
    """Unit tests for SourceHealthService state transitions."""

    def test_initial_registered_sources(self):
        service = SourceHealthService()
        statuses = service.get_all_statuses()
        codes = [s["source_code"] for s in statuses]
        assert "DAM_DAILY" in codes
        assert "CHALDAL_RETAIL" in codes
        assert "field_report" in codes

    def test_record_attempt_healthy_transition(self):
        service = SourceHealthService()
        service.record_attempt("DAM_DAILY", latency_ms=45.0, success=True, is_fallback=False)
        telemetry = service.get_source_status("DAM_DAILY")
        assert telemetry["status"] == "HEALTHY"
        assert telemetry["latency_ms"] == 45.0
        assert telemetry["is_fallback"] is False
        assert telemetry["last_error"] is None

    def test_record_attempt_degraded_fallback_transition(self):
        service = SourceHealthService()
        service.record_attempt(
            "CHALDAL_RETAIL",
            latency_ms=120.0,
            success=True,
            is_fallback=True,
            error_message="Live endpoint 503 Service Unavailable",
        )
        telemetry = service.get_source_status("CHALDAL_RETAIL")
        assert telemetry["status"] == "DEGRADED"
        assert telemetry["is_fallback"] is True
        assert "503" in telemetry["last_error"]

    def test_record_attempt_offline_transition(self):
        service = SourceHealthService()
        service.record_attempt(
            "DAM_DAILY",
            latency_ms=3000.0,
            success=False,
            is_fallback=False,
            error_message="Host unreachable and fixture missing",
        )
        telemetry = service.get_source_status("DAM_DAILY")
        assert telemetry["status"] == "OFFLINE"
        assert telemetry["error_count"] > 0
        assert "unreachable" in telemetry["last_error"]


class TestSystemAPIEndpoints:
    """Integration tests for /api/v1/system/ API routes."""

    def test_get_system_sources(self):
        """GET /api/v1/system/sources returns provider telemetry."""
        resp = client.get("/api/v1/system/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        assert data["status"] == "operational"
        assert len(data["sources"]) >= 3

        source_codes = [s["source_code"] for s in data["sources"]]
        assert "DAM_DAILY" in source_codes
        assert "CHALDAL_RETAIL" in source_codes
        assert "field_report" in source_codes

    def test_trigger_manual_sync(self, monkeypatch):
        """POST /api/v1/system/sync starts async harvest and returns tracking task ID."""
        test_key = "test-system-sync-key-safe"
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", test_key)
        resp = client.post("/api/v1/system/sync", headers={"X-API-Key": test_key})
        assert resp.status_code in [200, 202]
        data = resp.json()
        assert "task_id" in data
        assert data["status"] in ["in_progress", "completed"]
        assert "task_id" in data
        task_id = data["task_id"]

        # Poll status
        poll_resp = client.get(f"/api/v1/system/sync/{task_id}")
        assert poll_resp.status_code == 200
        task_data = poll_resp.json()
        assert task_data["task_id"] == task_id
        assert task_data["status"] in ["in_progress", "completed"]

    def test_get_nonexistent_sync_task_returns_404(self):
        """GET /api/v1/system/sync/{nonexistent} returns 404."""
        resp = client.get("/api/v1/system/sync/sync_nonexistent999")
        assert resp.status_code == 404

    def test_list_sync_tasks(self):
        """GET /api/v1/system/sync lists tracked tasks."""
        resp = client.get("/api/v1/system/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
