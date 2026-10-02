"""
Unit and integration tests for Phase 5D.1: Persistent Source Health Telemetry & Rolling 7-Day API.
Verifies deterministic aggregation, latency unskewing, SQLite persistence, idempotency,
rolling 7-day metrics, and full REST API backward compatibility.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.source import SourceHealthLog
from app.services.source_health import SourceHealthService, source_health_service


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    """Isolated session for testing telemetry persistence."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    # Clean up test source logs before test
    session.query(SourceHealthLog).filter(
        SourceHealthLog.source_name.like("TEST_%")
    ).delete(synchronize_session=False)
    session.commit()
    try:
        yield session
    finally:
        session.query(SourceHealthLog).filter(
            SourceHealthLog.source_name.like("TEST_%")
        ).delete(synchronize_session=False)
        session.commit()
        session.close()


# ── 1. Basic Deterministic Aggregation ─────────────────────────────────────────

def test_successful_checks_aggregation(db_session):
    """Verify 100% availability when all checks succeed."""
    service = SourceHealthService()
    test_date = date(2026, 10, 1)

    log = service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_SRC_A",
        target_date=test_date,
        successful_checks=10,
        failed_checks=0,
        avg_latency_ms=15.0,
    )
    db_session.commit()

    assert log.total_checks == 10
    assert log.successful_checks == 10
    assert log.failed_checks == 0
    assert log.availability_percent == 100.0


def test_failed_checks_aggregation(db_session):
    """Verify 0% availability when all checks fail."""
    service = SourceHealthService()
    test_date = date(2026, 10, 1)

    log = service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_SRC_B",
        target_date=test_date,
        successful_checks=0,
        failed_checks=8,
    )
    db_session.commit()

    assert log.total_checks == 8
    assert log.successful_checks == 0
    assert log.failed_checks == 8
    assert log.availability_percent == 0.0


def test_mixed_checks_aggregation(db_session):
    """Verify exact ratio calculation for mixed results."""
    service = SourceHealthService()
    test_date = date(2026, 10, 1)

    log = service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_SRC_C",
        target_date=test_date,
        successful_checks=7,
        failed_checks=3,
    )
    db_session.commit()

    assert log.total_checks == 10
    assert log.successful_checks == 7
    assert log.failed_checks == 3
    assert log.availability_percent == 70.0


def test_zero_checks_protection(db_session):
    """Verify division by zero is safely handled."""
    service = SourceHealthService()
    test_date = date(2026, 10, 1)

    log = service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_SRC_ZERO",
        target_date=test_date,
        successful_checks=0,
        failed_checks=0,
    )
    db_session.commit()

    assert log.total_checks == 0
    assert log.availability_percent == 0.0


# ── 2. Latency Integrity (Failed Requests Excluded) ───────────────────────────

def test_failed_requests_excluded_from_average_latency(db_session):
    """
    Failed requests must NOT artificially reduce or skew average latency.
    Only successful attempts contribute to latency statistics.
    """
    service = SourceHealthService()
    test_date = date(2026, 10, 2)

    # 1. First attempt: successful, 100ms
    service.record_attempt(
        source_code="TEST_LAT_SOURCE",
        latency_ms=100.0,
        success=True,
        session=db_session,
        attempt_date=test_date,
    )
    db_session.commit()

    # 2. Second attempt: failed, 0ms or error timeout
    service.record_attempt(
        source_code="TEST_LAT_SOURCE",
        latency_ms=0.0,
        success=False,
        session=db_session,
        attempt_date=test_date,
    )
    db_session.commit()

    log = db_session.query(SourceHealthLog).filter_by(
        source_name="TEST_LAT_SOURCE", date=test_date
    ).first()

    assert log.total_checks == 2
    assert log.successful_checks == 1
    assert log.failed_checks == 1
    # Average latency must still be 100ms, NOT 50ms!
    assert log.avg_latency_ms == 100.0
    assert log.availability_percent == 50.0


def test_min_max_latency_behavior(db_session):
    """Verify running min and max latency tracking across successive successful checks."""
    service = SourceHealthService()
    test_date = date(2026, 10, 2)

    service.record_attempt("TEST_MINMAX", 50.0, success=True, session=db_session, attempt_date=test_date)
    service.record_attempt("TEST_MINMAX", 150.0, success=True, session=db_session, attempt_date=test_date)
    service.record_attempt("TEST_MINMAX", 25.0, success=True, session=db_session, attempt_date=test_date)
    db_session.commit()

    log = db_session.query(SourceHealthLog).filter_by(
        source_name="TEST_MINMAX", date=test_date
    ).first()

    assert log.successful_checks == 3
    assert log.min_latency_ms == 25.0
    assert log.max_latency_ms == 150.0
    assert log.avg_latency_ms == round((50.0 + 150.0 + 25.0) / 3, 2)


# ── 3. Persistence & Idempotency ──────────────────────────────────────────────

def test_unique_source_name_and_date_constraint(db_session):
    """Enforce UNIQUE(source_name, date) constraint at DB level."""
    test_date = date(2026, 10, 3)
    log1 = SourceHealthLog(
        source_name="TEST_DUPLICATE",
        date=test_date,
        total_checks=1,
        successful_checks=1,
        failed_checks=0,
        availability_percent=100.0,
    )
    db_session.add(log1)
    db_session.commit()

    log2 = SourceHealthLog(
        source_name="TEST_DUPLICATE",
        date=test_date,
        total_checks=1,
        successful_checks=1,
        failed_checks=0,
        availability_percent=100.0,
    )
    db_session.add(log2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_repeated_aggregation_is_idempotent(db_session):
    """Calling record_daily_aggregate repeatedly updates rather than creating duplicate rows."""
    service = SourceHealthService()
    test_date = date(2026, 10, 3)

    service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_IDEMPOTENT",
        target_date=test_date,
        successful_checks=5,
        failed_checks=0,
        avg_latency_ms=10.0,
    )
    db_session.commit()

    # Re-run same aggregation with updated numbers
    service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_IDEMPOTENT",
        target_date=test_date,
        successful_checks=8,
        failed_checks=2,
        avg_latency_ms=12.5,
    )
    db_session.commit()

    rows = db_session.query(SourceHealthLog).filter_by(
        source_name="TEST_IDEMPOTENT", date=test_date
    ).all()

    assert len(rows) == 1
    assert rows[0].total_checks == 10
    assert rows[0].successful_checks == 8
    assert rows[0].failed_checks == 2
    assert rows[0].availability_percent == 80.0
    assert rows[0].avg_latency_ms == 12.5


# ── 4. Rolling 7-Day Calculation ──────────────────────────────────────────────

def test_rolling_7d_full_seven_days(db_session):
    """Verify rolling 7-day calculation across a complete 7-day window."""
    service = SourceHealthService()
    end_date = date(2026, 10, 10)

    # Insert 7 consecutive days (days 4 through 10)
    for i in range(7):
        cur_date = end_date - timedelta(days=i)
        service.record_daily_aggregate(
            session=db_session,
            source_name="TEST_ROLLING_FULL",
            target_date=cur_date,
            successful_checks=9,
            failed_checks=1,  # 90% each day
            avg_latency_ms=20.0,
        )
    db_session.commit()

    metrics = service.get_rolling_7d_telemetry(
        source_name="TEST_ROLLING_FULL",
        session=db_session,
        end_date=end_date,
    )

    assert metrics["observed_days_count"] == 7
    assert metrics["rolling_7d_availability"] == 90.0
    assert metrics["rolling_7d_avg_latency_ms"] == 20.0


def test_rolling_7d_missing_days_not_counted_as_failures(db_session):
    """
    Missing days must NOT be treated as failed checks.
    Only days with actual observations contribute to the rolling statistics.
    """
    service = SourceHealthService()
    end_date = date(2026, 10, 10)

    # Insert only 2 observed days within the 7-day window (e.g. today and 4 days ago)
    # Day 1: 100% available (10/10)
    service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_SPARSE_DAYS",
        target_date=end_date,
        successful_checks=10,
        failed_checks=0,
        avg_latency_ms=10.0,
    )
    # Day 2: 100% available (10/10)
    service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_SPARSE_DAYS",
        target_date=end_date - timedelta(days=4),
        successful_checks=10,
        failed_checks=0,
        avg_latency_ms=14.0,
    )
    db_session.commit()

    metrics = service.get_rolling_7d_telemetry(
        source_name="TEST_SPARSE_DAYS",
        session=db_session,
        end_date=end_date,
    )

    assert metrics["observed_days_count"] == 2
    # Because both observed days were 100% available, rolling availability MUST be 100%,
    # not artificially lowered to 2/7 (28.5%)!
    assert metrics["rolling_7d_availability"] == 100.0
    assert metrics["rolling_7d_avg_latency_ms"] == 12.0  # (10 + 14) / 2


def test_rolling_7d_excludes_older_than_seven_days(db_session):
    """Records older than 7 calendar days must not be included in rolling window."""
    service = SourceHealthService()
    end_date = date(2026, 10, 10)

    # Day within window (yesterday): 100% available
    service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_WINDOW_EXCLUSION",
        target_date=end_date - timedelta(days=1),
        successful_checks=10,
        failed_checks=0,
        avg_latency_ms=15.0,
    )
    # Day OUTSIDE window (8 days ago): 0% available
    service.record_daily_aggregate(
        session=db_session,
        source_name="TEST_WINDOW_EXCLUSION",
        target_date=end_date - timedelta(days=8),
        successful_checks=0,
        failed_checks=10,
        avg_latency_ms=None,
    )
    db_session.commit()

    metrics = service.get_rolling_7d_telemetry(
        source_name="TEST_WINDOW_EXCLUSION",
        session=db_session,
        end_date=end_date,
    )

    assert metrics["observed_days_count"] == 1
    assert metrics["rolling_7d_availability"] == 100.0


# ── 5. REST API Backward Compatibility ────────────────────────────────────────

def test_api_system_sources_preserves_existing_contract(client):
    """GET /api/v1/system/sources retains all legacy fields while exposing new telemetry."""
    resp = client.get("/api/v1/system/sources")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "operational"
    assert "sources" in data
    assert len(data["sources"]) >= 3

    for s in data["sources"]:
        # Legacy contract fields MUST exist
        assert "source_code" in s
        assert "source_name" in s
        assert "source_type" in s
        assert "status" in s
        assert "latency_ms" in s
        assert "is_fallback" in s
        assert "error_count" in s
        assert "success_count" in s

        # Phase 5D extended fields MUST exist
        assert "source" in s
        assert "current_status" in s
        assert "rolling_7d_availability" in s
        assert "rolling_7d_avg_latency_ms" in s
        assert "last_success" in s
        assert "last_failure" in s
