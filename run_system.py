#!/usr/bin/env python
"""
PricePulse BD — Unified System Orchestrator and Offline Launcher.
Coordinates FastAPI REST backend, database hygiene, and optional frontend static serving.
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    banner = r"""
=============================================================================
  PricePulse BD — Market Intelligence & Anomaly Detection System
  Undergraduate CSE Final Year Research Project (2026)
  Local-First Architecture | SQLite WAL | FastAPI | React 18 + Leaflet
=============================================================================
"""
    print(banner)


def verify_environment() -> bool:
    """Validate database, taxonomy seeds, and frontend build readiness."""
    print("[1/4] Checking Python environment and dependencies...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        print(f"      FastAPI {fastapi.__version__} | SQLAlchemy {sqlalchemy.__version__} | Pydantic {pydantic.__version__} [OK]")
    except ImportError as e:
        print(f"      [ERROR] Missing core dependency: {e}")
        return False

    print("[2/4] Verifying database schema and initial seed...")
    try:
        from app.core.database import SessionLocal, engine, Base
        from app.models.commodity import Commodity
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            count = session.query(Commodity).count()
            if count == 0:
                print("      Database empty. Triggering automatic taxonomy seed...")
                from scripts.init_db import seed_locations, seed_commodities
                seed_locations(session)
                seed_commodities(session)
                count = session.query(Commodity).count()
            print(f"      Database verified with {count} canonical commodities registered [OK]")
    except Exception as e:
        print(f"      [ERROR] Database initialization failed: {e}")
        return False

    print("[3/4] Verifying frontend static distribution...")
    dist_dir = PROJECT_ROOT / "frontend" / "dist"
    index_file = dist_dir / "index.html"
    if index_file.exists():
        print(f"      Frontend production build found at: {dist_dir} [OK]")
    else:
        print(f"      [WARN] Frontend production build not found at {dist_dir}")
        print("      To build frontend: cd frontend && npm install && npm run build")

    print("[4/4] Verifying spatial GeoJSON boundaries...")
    geojson_path = PROJECT_ROOT / "data" / "geo" / "bangladesh_districts_simplified.json"
    if geojson_path.exists():
        print(f"      Bangladesh district GeoJSON dataset present ({geojson_path.stat().st_size} bytes) [OK]")
    else:
        print(f"      [WARN] GeoJSON boundary file missing at: {geojson_path}")

    print("\n>>> System environment verification completed successfully! <<<\n")
    return True


def ensure_demo_history():
    """Ensure 30-day continuous observations and onion anomaly shock are seeded."""
    from app.core.database import SessionLocal
    from app.models.observation import PriceObservation
    with SessionLocal() as session:
        obs_count = session.query(PriceObservation).count()
        if obs_count < 50:
            print(f"Found only {obs_count} observations. Seeding 30-day realistic demo history...")
            from scripts.generate_demo_history import seed_demo_history
            seed_demo_history(session)
            print("30-day demo history populated successfully.")
        else:
            print(f"Observations already present in database ({obs_count} records).")


def build_unified_application(serve_frontend: bool = True):
    """Instantiate FastAPI app and optionally mount compiled frontend static assets."""
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse
    from app.main import create_application

    app = create_application()

    dist_dir = PROJECT_ROOT / "frontend" / "dist"
    if serve_frontend and (dist_dir / "index.html").exists():
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            # Pass through API requests, docs, and health checks
            if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path == "health":
                return None
            requested_file = dist_dir / full_path
            if requested_file.is_file():
                return FileResponse(requested_file)
            return FileResponse(dist_dir / "index.html")

        print("Serving compiled React frontend directly from FastAPI root.")

    return app


def main():
    parser = argparse.ArgumentParser(
        description="PricePulse BD — Unified System Orchestrator and Offline Launcher"
    )
    parser.add_argument(
        "--test", "--check",
        action="store_true",
        dest="test_mode",
        help="Validate environment, dependencies, and database readiness without starting server"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Network interface to bind (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the unified server (default: 8000)"
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Disable static frontend mounting (serve API only)"
    )
    parser.add_argument(
        "--seed-history",
        action="store_true",
        help="Force regeneration of 30-day demo history"
    )

    args = parser.parse_args()
    print_banner()

    if not verify_environment():
        sys.exit(1)

    if args.test_mode:
        print("Self-test passed. Exiting cleanly.")
        sys.exit(0)

    if args.seed_history:
        from app.core.database import SessionLocal
        from scripts.generate_demo_history import seed_demo_history
        with SessionLocal() as session:
            seed_demo_history(session)

    # Make sure demo history is present for defense
    ensure_demo_history()

    import uvicorn

    serve_frontend = not args.no_frontend
    app = build_unified_application(serve_frontend=serve_frontend)

    print(f"Starting PricePulse BD on http://{args.host}:{args.port}")
    if serve_frontend and (PROJECT_ROOT / "frontend" / "dist" / "index.html").exists():
        print(f"Web Dashboard:      http://{args.host}:{args.port}/")
    print(f"Interactive API Docs: http://{args.host}:{args.port}/docs")
    print(f"Today's Pulse API:   http://{args.host}:{args.port}/api/v1/pulse/today")
    print("Press Ctrl+C to terminate.\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
