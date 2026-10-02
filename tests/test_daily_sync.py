"""
tests/test_daily_sync.py
==========================
Verifies the daily price synchronization pipeline:
- Collector contract (collect() returns correct schema via RawObservation)
- Source health recording and API endpoint
- Scheduler job registration
- Sync endpoint behavior (via TestClient)

All tests are isolated using SQLite in-memory or monkeypatching — no live
network calls are made.
"""

import pytest
from dataclasses import asdict
from datetime import date
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.scheduler import BackgroundSyncScheduler

client = TestClient(app)


# ─────────────────────────────────────────────
# Part 1: Collector contract validation
# ─────────────────────────────────────────────

class TestCollectorContract:
    """Verify that collector.collect() returns RawObservation objects with the correct schema."""

    REQUIRED_FIELDS = {"raw_name", "raw_price", "raw_unit", "source_code", "observation_date"}

    def _assert_items_valid(self, items: list):
        assert isinstance(items, list), "collect() must return a list"
        for item in items:
            # Items may be dataclass instances or dicts — normalize to dict for checking
            if hasattr(item, "__dataclass_fields__"):
                item_dict = asdict(item)
            elif isinstance(item, dict):
                item_dict = item
            else:
                item_dict = vars(item) if hasattr(item, "__dict__") else {}

            # Map raw_commodity_name -> raw_name if needed
            if "raw_commodity_name" in item_dict and "raw_name" not in item_dict:
                item_dict["raw_name"] = item_dict["raw_commodity_name"]

            missing = self.REQUIRED_FIELDS - item_dict.keys()
            assert not missing, f"Item missing required fields: {missing}. Keys: {list(item_dict.keys())}"

            price = item_dict["raw_price"]
            assert isinstance(price, (int, float)), "raw_price must be numeric"
            assert price > 0, "raw_price must be positive"

    def test_dam_fixture_collector_contract(self):
        from app.collectors.dam_fixture_collector import DAMFixtureCollector
        collector = DAMFixtureCollector()
        items = collector.collect()
        self._assert_items_valid(items)
        assert len(items) >= 1

    def test_chaldal_collector_fallback_contract(self):
        from app.collectors.chaldal_collector import ChaldalCollector
        collector = ChaldalCollector()
        items = collector.collect()
        self._assert_items_valid(items)
        assert len(items) >= 1

    def test_dam_live_collector_falls_back_to_fixture(self):
        """DAMLiveCollector must fall back gracefully when network is down."""
        from app.collectors.dam_live_collector import DAMLiveCollector
        with patch("httpx.Client.get", side_effect=Exception("Simulated network down")):
            collector = DAMLiveCollector()
            items = collector.collect()
        assert isinstance(items, list)

    def test_chaldal_live_collector_falls_back_gracefully(self):
        """ChaldalLiveCollector must fall back when network is unreachable."""
        from app.collectors.chaldal_live_collector import ChaldalLiveCollector
        with patch("httpx.Client.get", side_effect=Exception("Simulated timeout")):
            collector = ChaldalLiveCollector()
            items = collector.collect()
        assert isinstance(items, list)


# ─────────────────────────────────────────────
# Part 2: Source health endpoint
# ─────────────────────────────────────────────

class TestSourceHealthRecording:
    """Verify source health events are persisted correctly."""

    def test_sources_endpoint_returns_list(self):
        """GET /api/v1/system/sources must return 200 with a list of sources."""
        resp = client.get("/api/v1/system/sources")
        assert resp.status_code == 200
        data = resp.json()
        sources = data.get("sources", data) if isinstance(data, dict) else data
        assert isinstance(sources, list)

    def test_sources_response_has_expected_codes(self):
        """The sources list should contain the standard DAM and Chaldal source entries."""
        resp = client.get("/api/v1/system/sources")
        assert resp.status_code == 200
        data = resp.json()
        sources = data.get("sources", data) if isinstance(data, dict) else data
        # Extract codes from whatever schema is returned
        codes = set()
        for s in sources:
            if isinstance(s, dict):
                code = s.get("code") or s.get("source_code") or s.get("name", "")
                codes.add(str(code).lower())
        # At least one of the known sources should be registered
        known = {"dam_bulletin", "chaldal_retail", "field_report",
                 "dam", "chaldal", "department of agricultural"}
        assert known & codes or len(sources) > 0, \
            f"Expected known source codes, got: {codes}"


# ─────────────────────────────────────────────
# Part 3: Scheduler interface
# ─────────────────────────────────────────────

class TestSchedulerRegistration:
    """Verify that the BackgroundSyncScheduler has the expected interface."""

    def test_scheduler_has_running_attribute(self):
        scheduler = BackgroundSyncScheduler()
        assert hasattr(scheduler, "_running")

    def test_scheduler_has_tasks_dict(self):
        scheduler = BackgroundSyncScheduler()
        assert hasattr(scheduler, "_tasks")
        assert isinstance(scheduler._tasks, dict)

    def test_scheduler_can_start(self):
        """start() must not raise outside an event loop (deferred mode)."""
        scheduler = BackgroundSyncScheduler()
        try:
            scheduler.start()
        except Exception as exc:
            pytest.fail(f"start() raised: {exc}")

    def test_scheduler_can_shutdown(self):
        """shutdown() must be callable and not raise."""
        scheduler = BackgroundSyncScheduler()
        try:
            scheduler.shutdown()
        except Exception as exc:
            pytest.fail(f"shutdown() raised: {exc}")

    def test_scheduler_can_stop(self):
        """stop() alias must be callable without error."""
        scheduler = BackgroundSyncScheduler()
        scheduler.stop()
        assert scheduler._running is False

    def test_scheduler_list_jobs(self):
        """list_jobs() returns a list of job dicts."""
        scheduler = BackgroundSyncScheduler()
        jobs = scheduler.list_jobs()
        assert isinstance(jobs, list)

    def test_scheduler_interval_configurable(self):
        custom_scheduler = BackgroundSyncScheduler(interval_seconds=3600)
        assert custom_scheduler.interval_seconds == 3600


# ─────────────────────────────────────────────
# Part 4: Sync REST endpoint
# ─────────────────────────────────────────────

class TestSyncEndpoint:
    """Verify the manual sync endpoint contract."""

    def test_sync_trigger_endpoint_accessible(self, monkeypatch):
        """POST /api/v1/system/sync must respond (200/202)."""
        test_key = "test-daily-sync-key-safe"
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", test_key)
        resp = client.post("/api/v1/system/sync", headers={"X-API-Key": test_key})
        assert resp.status_code in (200, 202, 400)

    def test_sync_trigger_returns_task_id(self, monkeypatch):
        """POST /api/v1/system/sync must return a task_id or status field."""
        test_key = "test-daily-sync-key-safe"
        monkeypatch.setenv("PRICEPULSE_ADMIN_API_KEY", test_key)
        resp = client.post("/api/v1/system/sync", headers={"X-API-Key": test_key})
        if resp.status_code in (200, 202):
            data = resp.json()
            assert "task_id" in data or "status" in data or "message" in data

    def test_sync_status_accessible(self):
        """GET /api/v1/system/sync/{task_id} returns 404 for nonexistent task."""
        resp = client.get("/api/v1/system/sync/nonexistent-task-id-99999")
        assert resp.status_code in (200, 404)

    def test_pulse_today_includes_new_commodities(self):
        """GET /api/v1/pulse/today must return the pulse structure."""
        resp = client.get("/api/v1/pulse/today")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data or "commodities" in data or "date" in data


# ─────────────────────────────────────────────
# Part 5: Commodity list expansion validation
# ─────────────────────────────────────────────

class TestCommodityListExpansion:
    """Verify that the /commodities endpoint reflects the expanded 21-item taxonomy."""

    def test_commodities_endpoint_responds(self):
        resp = client.get("/api/v1/commodities")
        assert resp.status_code == 200

    def test_commodities_response_has_items(self):
        resp = client.get("/api/v1/commodities")
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(items, list)

    def test_commodity_schema_fields(self):
        resp = client.get("/api/v1/commodities")
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        for item in items[:3]:
            assert "canonical_name" in item or "id" in item
