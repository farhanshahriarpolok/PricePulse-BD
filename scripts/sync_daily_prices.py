"""
Daily Price Sync CLI — PricePulse BD
=====================================
Force-fetch today's prices from all configured data sources and persist them
to the SQLite database. Intended as a manual trigger for the same ingestion
pipeline that the background APScheduler job runs at 06:00 daily.

Usage:
    python scripts/sync_daily_prices.py              # sync all sources
    python scripts/sync_daily_prices.py --source dam  # DAM only
    python scripts/sync_daily_prices.py --source chaldal

Exit codes:
    0 — at least one source returned data
    1 — all sources failed (network down / fixtures fallback only)
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.database import SessionLocal
from app.services.ingestion import ingest_observations
from app.collectors.dam_live_collector import DAMLiveCollector
from app.collectors.chaldal_live_collector import ChaldalLiveCollector
from app.collectors.tcb_collector import TCBCollector
from app.collectors.news_collector import NewsCollector
from app.services.source_health import record_health_event


def run_sync(source_filter: str | None = None) -> dict:
    """Execute ingestion pipeline for all sources or a single filtered source."""
    results = {}
    today = date.today()
    print(f"\n=== PricePulse BD: Daily Price Sync [{today}] ===\n")

    sources = {
        "dam": ("DAM Live Bulletin", DAMLiveCollector),
        "chaldal": ("Chaldal Online Grocery", ChaldalLiveCollector),
        "tcb": ("Trading Corporation of Bangladesh (TCB)", TCBCollector),
        "news": ("National Press Market Roundups", NewsCollector),
    }

    if source_filter:
        sources = {k: v for k, v in sources.items() if k == source_filter.lower()}
        if not sources:
            print(f"[ERROR] Unknown source '{source_filter}'. Valid: dam, chaldal, tcb, news")
            sys.exit(1)

    with SessionLocal() as session:
        for key, (label, CollectorClass) in sources.items():
            print(f"  [{key.upper()}] Running {label} collector...")
            t0 = time.perf_counter()
            try:
                collector = CollectorClass()
                raw_items = collector.collect()
                elapsed_ms = int((time.perf_counter() - t0) * 1000)

                if not raw_items:
                    print(f"    Warning: collector returned 0 items. Possible fallback mode.")
                    record_health_event(session, source_code=key, status="DEGRADED",
                                        latency_ms=elapsed_ms, record_count=0)
                    results[key] = {"status": "degraded", "items": 0}
                    continue

                inserted, updated = ingest_observations(session, raw_items)
                session.commit()

                status = "HEALTHY" if len(raw_items) >= 3 else "DEGRADED"
                record_health_event(session, source_code=key, status=status,
                                    latency_ms=elapsed_ms, record_count=len(raw_items))
                session.commit()

                print(f"    OK: {len(raw_items)} harvested, {inserted} inserted, {updated} updated "
                      f"[{elapsed_ms}ms]")
                results[key] = {"status": "ok", "items": len(raw_items),
                                 "inserted": inserted, "updated": updated}

            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                print(f"    ERROR: {exc}")
                try:
                    record_health_event(session, source_code=key, status="OFFLINE",
                                        latency_ms=elapsed_ms, record_count=0,
                                        error_message=str(exc))
                    session.commit()
                except Exception:
                    pass
                results[key] = {"status": "error", "error": str(exc)}

    print()
    success = any(r.get("status") == "ok" for r in results.values())
    if success:
        total_harvested = sum(r.get("items", 0) for r in results.values())
        print(f"=== Sync complete. Total harvested: {total_harvested} items ===\n")
    else:
        print("=== Sync complete with degraded/offline sources. Check health telemetry. ===\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="PricePulse BD — Daily Price Sync CLI")
    parser.add_argument(
        "--source",
        choices=["dam", "chaldal", "tcb", "news"],
        default=None,
        help="Run a single source collector (default: all sources: dam, chaldal, tcb, news)",
    )
    args = parser.parse_args()
    results = run_sync(args.source)
    all_failed = all(r.get("status") not in ("ok",) for r in results.values())
    sys.exit(1 if all_failed else 0)


if __name__ == "__main__":
    main()
