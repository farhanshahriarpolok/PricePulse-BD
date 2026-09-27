"""
In-process background scheduler and async sync manager for PricePulse BD.
Periodically harvests commodity prices and provides on-demand background sync.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.core.database import SessionLocal
from app.collectors.dam_live_collector import DAMLiveCollector
from app.collectors.chaldal_live_collector import ChaldalLiveCollector
from app.services.ingestion import IngestionPipeline

logger = logging.getLogger(__name__)


class BackgroundSyncScheduler:
    """Manages periodic background harvests and asynchronous on-demand sync tasks."""

    def __init__(self, interval_seconds: int = 43200):  # Default: every 12 hours
        self.interval_seconds = interval_seconds
        self._loop_task: Optional[asyncio.Task] = None
        self._running = False
        self._tasks: Dict[str, Dict[str, Any]] = {}

    def start(self) -> None:
        """Start the periodic background scheduler task."""
        if self._running:
            return
        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._loop_task = loop.create_task(self._periodic_loop())
            logger.info("BackgroundSyncScheduler started successfully.")
        except RuntimeError:
            logger.warning("No active running event loop; scheduler deferred.")

    def shutdown(self) -> None:
        """Gracefully shut down the periodic background scheduler."""
        self._running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            logger.info("BackgroundSyncScheduler cancelled.")

    async def _periodic_loop(self) -> None:
        """Periodic loop executing harvests at regular intervals."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                if self._running:
                    logger.info("Executing scheduled periodic harvest...")
                    await self._execute_sync("scheduled_periodic")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error in periodic sync loop: {exc}", exc_info=True)

    def trigger_sync(self, trigger_type: str = "manual_on_demand") -> str:
        """
        Trigger an on-demand sync task asynchronously.
        Returns the unique task ID immediately.
        """
        task_id = f"sync_{uuid.uuid4().hex[:10]}"
        task_record = {
            "task_id": task_id,
            "trigger_type": trigger_type,
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "total_harvested": 0,
            "total_inserted": 0,
            "total_updated": 0,
            "total_skipped": 0,
            "error": None,
        }
        self._tasks[task_id] = task_record

        # Schedule execution on the current asyncio event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._execute_sync(trigger_type, task_id))
        except RuntimeError:
            # If no running event loop (e.g. synchronous unit test context), run in thread/sync
            import threading
            threading.Thread(
                target=lambda: asyncio.run(self._execute_sync(trigger_type, task_id)),
                daemon=True,
            ).start()

        return task_id

    async def _execute_sync(self, trigger_type: str, task_id: Optional[str] = None) -> None:
        """Execute the ingestion pipeline in a non-blocking thread."""
        if not task_id:
            task_id = f"sync_{uuid.uuid4().hex[:10]}"
            self._tasks[task_id] = {
                "task_id": task_id,
                "trigger_type": trigger_type,
                "status": "in_progress",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "total_harvested": 0,
                "total_inserted": 0,
                "total_updated": 0,
                "total_skipped": 0,
                "error": None,
            }

        def _sync_worker():
            with SessionLocal() as db:
                pipeline = IngestionPipeline(db=db)
                collectors = [DAMLiveCollector(), ChaldalLiveCollector()]
                total_harvested = 0
                total_inserted = 0
                total_updated = 0
                total_skipped = 0

                for collector in collectors:
                    try:
                        report = pipeline.run_collector(collector)
                        total_harvested += report.total_harvested
                        total_inserted += report.inserted
                        total_updated += report.updated
                        total_skipped += report.skipped
                    except Exception as err:
                        logger.error(f"Collector {collector.source_code} failed: {err}")

                return {
                    "total_harvested": total_harvested,
                    "total_inserted": total_inserted,
                    "total_updated": total_updated,
                    "total_skipped": total_skipped,
                }

        try:
            result = await asyncio.to_thread(_sync_worker)
            self._tasks[task_id].update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "total_harvested": result["total_harvested"],
                    "total_inserted": result["total_inserted"],
                    "total_updated": result["total_updated"],
                    "total_skipped": result["total_skipped"],
                }
            )
            logger.info(
                f"Sync task {task_id} completed: "
                f"{result['total_harvested']} harvested, {result['total_inserted']} inserted, {result['total_updated']} updated."
            )
        except Exception as exc:
            logger.error(f"Sync task {task_id} failed: {exc}", exc_info=True)
            self._tasks[task_id].update(
                {
                    "status": "failed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                }
            )

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve execution report for a sync task."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all recorded sync task runs."""
        return self._tasks


# Singleton scheduler instance
sync_scheduler = BackgroundSyncScheduler()
