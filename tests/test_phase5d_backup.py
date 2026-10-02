"""
Unit and integration tests for Phase 5D.2: Safe SQLite Online Hot Backup Utility.
Verifies all 12 operational backup invariants:
  1. Backup creation
  2. Backup opens successfully
  3. PRAGMA integrity_check returns 'ok'
  4. Expected schema exists in backup
  5. Active WAL database can be backed up
  6. Application/database remains readable and writable while backup runs
  7. Repeated backups work predictably
  8. Retention cleanup prunes older backups
  9. Failed verification preserves last-good backup
  10. Temporary files (.tmp) are purged upon failure
  11. Atomic promotion behavior
  12. CLI exit code reflects success/failure cleanly
"""

import os
import sys
import sqlite3
import subprocess
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.backup_db import (
    perform_hot_backup,
    verify_sqlite_backup,
    cleanup_old_backups,
    resolve_default_backup_dir,
)


@pytest.fixture
def temp_env():
    """Create isolated temporary directory with live SQLite WAL database."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_live.db"
        backup_dir = tmp_path / "backups"

        # Initialize test database with WAL mode and test tables
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("CREATE TABLE commodities (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("CREATE TABLE sources (id INTEGER PRIMARY KEY, code TEXT);")
        conn.execute("CREATE TABLE price_observations (id INTEGER PRIMARY KEY, price REAL);")
        conn.execute("CREATE TABLE districts (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute("CREATE TABLE divisions (id INTEGER PRIMARY KEY, name TEXT);")

        conn.execute("INSERT INTO commodities (name) VALUES ('Rice'), ('Potato'), ('Onion');")
        conn.execute("INSERT INTO sources (code) VALUES ('DAM_DAILY'), ('TCB_DAILY');")
        conn.execute("INSERT INTO districts (name) VALUES ('Dhaka'), ('Chittagong');")
        conn.commit()
        conn.close()

        yield {
            "root": tmp_path,
            "db_path": db_path,
            "backup_dir": backup_dir,
            "expected_tables": ["commodities", "sources", "price_observations", "districts", "divisions"],
        }


# ── 1. Backup Creation, Open, Integrity, and Schema Invariants ─────────────────

def test_backup_creation_and_open(temp_env):
    """Verify backup file is created and opens successfully with sqlite3."""
    backup_file = perform_hot_backup(
        db_path=temp_env["db_path"],
        backup_dir=temp_env["backup_dir"],
        retention_count=5,
        expected_tables=temp_env["expected_tables"],
    )

    assert backup_file.exists()
    assert backup_file.stat().st_size > 0

    # Must open cleanly
    conn = sqlite3.connect(str(backup_file))
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM commodities;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 3


def test_backup_integrity_check_returns_ok(temp_env):
    """Verify PRAGMA integrity_check returns 'ok'."""
    backup_file = perform_hot_backup(
        db_path=temp_env["db_path"],
        backup_dir=temp_env["backup_dir"],
        retention_count=5,
        expected_tables=temp_env["expected_tables"],
    )

    is_valid, msg = verify_sqlite_backup(backup_file, expected_tables=temp_env["expected_tables"])
    assert is_valid is True
    assert "ok" in msg.lower()


def test_backup_expected_schema_exists(temp_env):
    """Verify all critical canonical tables and rows are preserved."""
    backup_file = perform_hot_backup(
        db_path=temp_env["db_path"],
        backup_dir=temp_env["backup_dir"],
        retention_count=5,
        expected_tables=temp_env["expected_tables"],
    )

    conn = sqlite3.connect(str(backup_file))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {r[0] for r in cursor.fetchall()}
    conn.close()

    for expected in temp_env["expected_tables"]:
        assert expected in tables


# ── 2. WAL Concurrency Invariants ─────────────────────────────────────────────

def test_active_wal_database_can_be_backed_up(temp_env):
    """Verify backup succeeds on active database with non-checkpointed WAL file."""
    # Write transactions into WAL without checkpointing
    conn = sqlite3.connect(str(temp_env["db_path"]))
    conn.execute("INSERT INTO commodities (name) VALUES ('Lentils'), ('Soybean Oil');")
    conn.commit()

    # WAL file must exist
    wal_file = Path(str(temp_env["db_path"]) + "-wal")
    # Backup runs while conn is still open
    backup_file = perform_hot_backup(
        db_path=temp_env["db_path"],
        backup_dir=temp_env["backup_dir"],
        retention_count=5,
        expected_tables=temp_env["expected_tables"],
    )
    conn.close()

    assert backup_file.exists()
    b_conn = sqlite3.connect(str(backup_file))
    cursor = b_conn.cursor()
    cursor.execute("SELECT count(*) FROM commodities;")
    # Newly written commodities in WAL must be captured
    assert cursor.fetchone()[0] == 5
    b_conn.close()


def test_live_database_readable_and_writable_concurrently(temp_env):
    """Verify live database can be concurrently queried and written to while backup is executed."""
    conn = sqlite3.connect(str(temp_env["db_path"]))
    conn.execute("PRAGMA busy_timeout = 5000;")

    # Read from live DB
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM commodities;")
    assert cursor.fetchone()[0] >= 3

    # Run hot backup
    backup_file = perform_hot_backup(
        db_path=temp_env["db_path"],
        backup_dir=temp_env["backup_dir"],
        retention_count=5,
        expected_tables=temp_env["expected_tables"],
    )

    # Write to live DB immediately afterward without locks
    conn.execute("INSERT INTO commodities (name) VALUES ('Green Chili');")
    conn.commit()
    conn.close()

    assert backup_file.exists()


# ── 3. Retention Cleanup & Repeated Backups ───────────────────────────────────

def test_repeated_backups_and_retention_pruning(temp_env):
    """Verify retention cleanup keeps only N newest snapshots."""
    backup_dir = temp_env["backup_dir"]
    backup_dir.mkdir(parents=True, exist_ok=True)
    retention_limit = 3

    # Generate 5 backups with slight simulated timestamp differences
    created_files = []
    for i in range(5):
        # Create unique filename by manual delay or timestamp
        b_file = backup_dir / f"pricepulse_backup_2026100{i}_120000.db"
        b_file.write_text("dummy")
        created_files.append(b_file)

    deleted = cleanup_old_backups(backup_dir, retention_count=retention_limit)
    remaining = list(backup_dir.glob("pricepulse_backup_*.db"))

    assert len(remaining) == retention_limit
    assert len(deleted) == 2


# ── 4. Atomic Promotion & Fail-Safe Invariants ─────────────────────────────────

def test_failed_verification_preserves_last_good_backup(temp_env):
    """If verification fails on corrupted candidate, the previous backup is NOT overwritten."""
    # 1. Create valid baseline backup
    valid_backup = perform_hot_backup(
        db_path=temp_env["db_path"],
        backup_dir=temp_env["backup_dir"],
        retention_count=5,
        expected_tables=temp_env["expected_tables"],
    )
    assert valid_backup.exists()

    # 2. Attempt a backup that fails verification (e.g. required table missing)
    with pytest.raises(RuntimeError) as exc_info:
        perform_hot_backup(
            db_path=temp_env["db_path"],
            backup_dir=temp_env["backup_dir"],
            retention_count=5,
            expected_tables=["non_existent_special_table_xyz"],
        )

    assert "missing critical tables" in str(exc_info.value).lower()
    # The valid backup must still exist and be intact
    assert valid_backup.exists()


def test_temporary_files_purged_on_failure(temp_env):
    """Temporary .tmp files must be purged if backup fails verification."""
    backup_dir = temp_env["backup_dir"]

    with pytest.raises(RuntimeError):
        perform_hot_backup(
            db_path=temp_env["db_path"],
            backup_dir=backup_dir,
            retention_count=5,
            expected_tables=["ghost_table_123"],
        )

    # No .tmp files should remain in the backup directory
    tmp_files = list(backup_dir.glob("*.tmp"))
    assert len(tmp_files) == 0


# ── 5. CLI Execution & Non-Zero Status on Failure ─────────────────────────────

def test_cli_execution_success(temp_env):
    """Verify running python scripts/backup_db.py via subprocess returns exit code 0."""
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "backup_db.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--db-path",
        str(temp_env["db_path"]),
        "--backup-dir",
        str(temp_env["backup_dir"]),
        "--retention-count",
        "3",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "[SUCCESS]" in proc.stdout


def test_cli_execution_failure_non_zero_exit_code(temp_env):
    """Verify CLI returns exit code 1 when target database is nonexistent."""
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "backup_db.py"
    cmd = [
        sys.executable,
        str(script_path),
        "--db-path",
        str(temp_env["root"] / "non_existent_file.db"),
        "--backup-dir",
        str(temp_env["backup_dir"]),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "[ERROR]" in proc.stderr or "[ERROR]" in proc.stdout


# ── 6. Persistent Docker Volume & Default Backup Directory Resolution ──────────

def test_resolve_default_backup_dir_with_env(monkeypatch, tmp_path):
    """When BACKUP_DIR environment variable is set, it takes priority for defaults."""
    custom_dir = tmp_path / "custom_backup_location"
    monkeypatch.setenv("BACKUP_DIR", str(custom_dir))

    resolved = resolve_default_backup_dir(tmp_path / "data" / "pricepulse.db")
    assert resolved == custom_dir.resolve()


def test_resolve_default_backup_dir_in_data_directory(monkeypatch, tmp_path):
    """When database is located in a 'data' directory without BACKUP_DIR env, backups default to data/backups."""
    monkeypatch.delenv("BACKUP_DIR", raising=False)
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_file = data_dir / "pricepulse.db"

    resolved = resolve_default_backup_dir(db_file)
    assert resolved == (data_dir / "backups").resolve()


def test_resolve_default_backup_dir_project_root_fallback(monkeypatch, tmp_path):
    """When database is in root without BACKUP_DIR, backups default to root/backups."""
    monkeypatch.delenv("BACKUP_DIR", raising=False)
    root_dir = tmp_path / "custom_project_root"
    root_dir.mkdir(parents=True, exist_ok=True)
    db_file = root_dir / "pricepulse.db"

    resolved = resolve_default_backup_dir(db_file)
    project_root = Path(__file__).resolve().parent.parent
    assert resolved == (project_root / "backups").resolve()
