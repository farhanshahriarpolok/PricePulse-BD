"""
System status, source health telemetry, and on-demand background sync endpoints.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from app.services.source_health import source_health_service
from app.services.scheduler import sync_scheduler

router = APIRouter(prefix="/system", tags=["System Operations"])


@router.get(
    "/sources",
    summary="Get Upstream Provider Health Status",
    description="Returns telemetry, latency, and fallback operational health for all registered market data providers.",
)
def get_source_health():
    """Returns telemetry for all registered external and crowdsourced providers."""
    sources = source_health_service.get_all_statuses()
    return {
        "status": "operational",
        "total": len(sources),
        "sources": sources,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/sync",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger On-Demand Market Ingestion",
    description="Asynchronously launches the live collector ingestion pipeline without blocking the event loop.",
)
def trigger_system_sync():
    """Trigger an immediate asynchronous data harvest and return tracking ID."""
    task_id = sync_scheduler.trigger_sync(trigger_type="manual_api")
    return {
        "task_id": task_id,
        "status": "in_progress",
        "message": "Background market data harvest initiated successfully.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/sync/{task_id}",
    summary="Poll Background Sync Task Status",
    description="Check the execution status and metrics for a specific background sync task.",
)
def get_sync_status(task_id: str):
    """Retrieve progress or completion metrics for a given task ID."""
    task = sync_scheduler.get_task_status(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync task '{task_id}' not found.",
        )
    return task


@router.get(
    "/sync",
    summary="List Recent Sync Tasks",
    description="Returns a registry of all recorded background sync runs.",
)
def list_sync_tasks():
    """List all recorded sync tasks."""
    return {
        "tasks": list(sync_scheduler.get_all_tasks().values())
    }
