#!/usr/bin/env python3
"""
PricePulse BD — Production SQLite Zero-Downtime Hot Backup Utility

Performs safe, live database snapshots using Python's native SQLite Online Backup API
(sqlite3.Connection.backup). Fully compliant with SQLite Write-Ahead Logging (WAL) mode
and concurrent read/write transactions.

Workflow:
  1. Connect to live SQLite database with busy_timeout.
  2. Backup online to an ephemeral temporary file (.tmp).
  3. Validate integrity via PRAGMA integrity_check; -> 'ok'.
  4. Validate structural invariants (critical tables exist and are readable).
  5. Atomically promote/rename temporary file to permanent snapshot.
  6. Enforce configurable backup retention policy.
  7. If verification fails, safely discard temporary file and preserve previous backups.
"""

import os
import sys
import argparse
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backup_db")

DEFAULT_CRITICAL_TABLES = [
    "commodities",
    "sources",
    "price_observations",
    "districts",
    "divisions",
]


def resolve_default_db_path() -> Path:
    """Resolve default database path from environment or local repository structure."""
    db_env = os.getenv("DATABASE_URL", "")
    if db_env.startswith("sqlite:///"):
        clean_path = db_env.replace("sqlite:///", "")
        return Path(clean_path).resolve()

    project_root = Path(__file__).resolve().parent.parent
    local_db = project_root / "pricepulse.db"
    return local_db


def resolve_default_backup_dir(db_path: Path) -> Path:
    """
    Resolve default backup directory:
      1. BACKUP_DIR environment variable if explicitly set.
      2. If db_path is located in a dedicated data directory (e.g. /app/data/pricepulse.db),
         default to a 'backups' subdirectory within that same data directory so snapshots
         share the persistent Docker storage volume.
      3. Otherwise fall back to 'backups/' directory at project root.
    """
    env_backup = os.getenv("BACKUP_DIR", "").strip()
    if env_backup:
        return Path(env_backup).resolve()

    if db_path.parent.name == "data" or str(db_path.parent).rstrip("/\\").endswith("data"):
        return (db_path.parent / "backups").resolve()

    project_root = Path(__file__).resolve().parent.parent
    return (project_root / "backups").resolve()


def verify_sqlite_backup(
    backup_path: Path,
    expected_tables: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """
    Perform deep verification on a generated backup snapshot:
      - Opens connection to candidate backup file.
      - Executes PRAGMA integrity_check;.
      - Verifies presence of critical canonical tables.
      - Verifies table readability with count queries.

    Returns:
      (True, "Verification passed: ...") or (False, "Error reason")
    """
    if not backup_path.exists():
        return False, f"Candidate backup file does not exist: {backup_path}"

    if backup_path.stat().st_size == 0:
        return False, f"Candidate backup file is empty (0 bytes): {backup_path}"

    expected_tables = expected_tables or DEFAULT_CRITICAL_TABLES

    conn = None
    try:
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()

        # 1. PRAGMA integrity_check
        cursor.execute("PRAGMA integrity_check;")
        rows = cursor.fetchall()
        if not rows or rows[0][0] != "ok":
            error_details = ", ".join(r[0] for r in rows) if rows else "No rows returned"
            return False, f"PRAGMA integrity_check failed: {error_details}"

        # 2. Check presence of critical schema tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing_tables = [t for t in expected_tables if t not in existing_tables]
        if missing_tables:
            return False, f"Backup missing critical tables: {missing_tables}"

        # 3. Verify readability of critical tables
        for table in expected_tables:
            cursor.execute(f"SELECT count(*) FROM {table};")
            count = cursor.fetchone()[0]
            logger.debug("Verified table '%s' count: %d", table, count)

        return True, "Integrity check 'ok' and critical table structures verified successfully."

    except sqlite3.DatabaseError as e:
        return False, f"SQLite database corruption or open failure: {e}"
    except Exception as e:
        return False, f"Unexpected verification error: {e}"
    finally:
        if conn:
            conn.close()


def cleanup_old_backups(
    backup_dir: Path,
    retention_count: int,
    pattern: str = "pricepulse_backup_*.db",
) -> List[Path]:
    """
    Prunes older backups beyond the configured retention limit.
    Never removes non-matching files or files in progress (.tmp).
    """
    if retention_count <= 0:
        return []

    # Filter strictly for completed .db files matching the pattern
    backups = sorted(
        [f for f in backup_dir.glob(pattern) if f.is_file() and not f.name.endswith(".tmp")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    deleted = []
    if len(backups) > retention_count:
        for old_backup in backups[retention_count:]:
            try:
                old_backup.unlink()
                deleted.append(old_backup)
                logger.info("Pruned old backup beyond retention (%d): %s", retention_count, old_backup.name)
            except OSError as e:
                logger.warning("Failed to remove old backup %s: %s", old_backup, e)

    return deleted


def perform_hot_backup(
    db_path: Path,
    backup_dir: Path,
    retention_count: int = 7,
    expected_tables: Optional[List[str]] = None,
    busy_timeout_ms: int = 5000,
) -> Path:
    """
    Executes the complete online backup lifecycle:
      Live DB -> sqlite3.backup() -> .tmp file -> verify -> atomic promote -> retention.

    Raises:
      FileNotFoundError: If source database does not exist.
      RuntimeError: If backup execution or verification fails.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Source database file not found at: {db_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    final_backup_path = backup_dir / f"pricepulse_backup_{timestamp}.db"
    tmp_backup_path = backup_dir / f"pricepulse_backup_{timestamp}.db.tmp"

    logger.info("Initiating SQLite Online Backup...")
    logger.info("  Source DB:  %s", db_path)
    logger.info("  Target TMP: %s", tmp_backup_path)

    src_conn = None
    dest_conn = None

    try:
        # Connect to source with concurrency pragmas
        src_conn = sqlite3.connect(str(db_path), timeout=busy_timeout_ms / 1000.0)
        src_conn.execute(f"PRAGMA busy_timeout = {busy_timeout_ms};")

        # Connect to destination temporary file
        dest_conn = sqlite3.connect(str(tmp_backup_path))

        # Perform atomic online page copying
        # pages=-1 copies entire database in one call
        src_conn.backup(dest_conn, pages=-1)
        dest_conn.commit()

    except Exception as e:
        if tmp_backup_path.exists():
            tmp_backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"SQLite Online Backup failed during execution: {e}") from e

    finally:
        if dest_conn:
            dest_conn.close()
        if src_conn:
            src_conn.close()

    # Step 2: Verification of temporary backup
    logger.info("Validating backup integrity and schema consistency...")
    is_valid, reason = verify_sqlite_backup(tmp_backup_path, expected_tables=expected_tables)

    if not is_valid:
        if tmp_backup_path.exists():
            tmp_backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"Backup verification failed: {reason}")

    # Step 3: Atomic promotion (rename .tmp -> .db)
    try:
        if final_backup_path.exists():
            final_backup_path.unlink()
        tmp_backup_path.rename(final_backup_path)
        logger.info("Backup verified and atomically promoted: %s (Size: %d bytes)", final_backup_path.name, final_backup_path.stat().st_size)
    except Exception as e:
        if tmp_backup_path.exists():
            tmp_backup_path.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic rename of verified backup failed: {e}") from e

    # Step 4: Retention cleanup
    cleanup_old_backups(backup_dir, retention_count=retention_count)

    return final_backup_path


def main():
    parser = argparse.ArgumentParser(
        description="PricePulse BD — Safe SQLite Online Hot Backup CLI"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to live SQLite database file (defaults to DATABASE_URL or pricepulse.db)",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Directory to store backup snapshots (defaults to backups/ in project root)",
    )
    parser.add_argument(
        "--retention-count",
        type=int,
        default=int(os.getenv("BACKUP_RETENTION_COUNT", "7")),
        help="Number of completed backup files to retain (default: 7)",
    )
    parser.add_argument(
        "--busy-timeout",
        type=int,
        default=5000,
        help="SQLite busy timeout in milliseconds (default: 5000)",
    )

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    db_path = args.db_path or resolve_default_db_path()
    backup_dir = args.backup_dir or resolve_default_backup_dir(db_path)

    try:
        backup_file = perform_hot_backup(
            db_path=db_path,
            backup_dir=backup_dir,
            retention_count=args.retention_count,
            busy_timeout_ms=args.busy_timeout,
        )
        print(f"[SUCCESS] Hot backup created and verified: {backup_file}")
        sys.exit(0)
    except Exception as e:
        logger.error("Hot backup aborted: %s", e)
        print(f"[ERROR] Hot backup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
