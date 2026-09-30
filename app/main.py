"""
FastAPI application factory, middleware configuration, and lifecycle event handlers.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.schemas.common import HealthResponse, ErrorResponse, ErrorDetail
from app.api.v1.router import api_router
from app.services.scheduler import sync_scheduler
from scripts.init_db import seed_locations, seed_commodities, seed_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycles."""
    # Ensure tables exist on boot
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_locations(session)
        seed_commodities(session)
        seed_sources(session)
        import os
        if os.getenv("PRICEPULSE_SEED_DEMO", "").lower() in ("1", "true", "yes"):
            from app.models.observation import PriceObservation
            obs_count = session.query(PriceObservation).count()
            if obs_count < 50:
                from scripts.generate_demo_history import seed_demo_history
                seed_demo_history(session)
    # Start in-process background sync scheduler
    sync_scheduler.start()
    yield
    # Gracefully terminate background scheduler
    sync_scheduler.shutdown()



def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application instance."""
    app = FastAPI(
        title="PricePulse BD API",
        description=(
            "Realtime Commodity Market Intelligence Engine and REST API for Bangladesh. "
            "Delivers canonical price discovery, wholesale vs retail spreads, and on-demand ingestion."
        ),
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Hardened CORS configuration for Web dashboards and Android clients
    cors_origins = list(settings.cors_origins)
    env_origins = os.getenv("ALLOWED_ORIGINS")
    if env_origins:
        cors_origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Global RFC 7807 compliant error handler
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code_map = {
            400: "BAD_REQUEST",
            404: "NOT_FOUND",
            422: "UNPROCESSABLE_ENTITY",
            500: "INTERNAL_SERVER_ERROR",
        }
        code_str = code_map.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=code_str,
                    message=str(exc.detail),
                    status=exc.status_code,
                    timestamp=datetime.now(timezone.utc),
                )
            ).model_dump(mode="json"),
        )

    # Health check endpoints
    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="API Health Check",
    )
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Service Health Check",
    )
    def health_check():
        return HealthResponse(
            status="ok",
            app="PricePulse BD",
            version="0.2.0",
            timestamp=datetime.now(timezone.utc),
        )

    # Mount API v1 router under /api
    app.include_router(api_router, prefix="/api")

    # Mount compiled React frontend static assets if available
    dist_dir = settings.project_root / "frontend" / "dist"
    if (dist_dir / "index.html").exists():
        from fastapi.staticfiles import StaticFiles
        from starlette.responses import FileResponse

        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            # Pass through API requests, docs, and health checks
            if (
                full_path.startswith("api")
                or full_path.startswith("docs")
                or full_path.startswith("redoc")
                or full_path == "health"
            ):
                return None
            try:
                requested_file = (dist_dir / full_path).resolve()
                dist_resolved = dist_dir.resolve()
                if (dist_resolved in requested_file.parents or requested_file == dist_resolved) and requested_file.is_file():
                    return FileResponse(requested_file)
            except Exception:
                pass
            return FileResponse(dist_dir / "index.html")

    return app


app = create_application()
