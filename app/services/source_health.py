"""
Service for monitoring upstream data provider connectivity, latency, and fallback health.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class SourceTelemetry:
    source_code: str
    source_name: str
    source_type: str
    status: str  # "HEALTHY", "DEGRADED", "OFFLINE"
    latency_ms: float
    last_sync: Optional[datetime] = None
    is_fallback: bool = False
    error_count: int = 0
    success_count: int = 0
    last_error: Optional[str] = None


class SourceHealthService:
    """Tracks latency, operational status, and graceful degradation for data providers."""

    def __init__(self):
        self._sources: Dict[str, SourceTelemetry] = {
            "DAM_DAILY": SourceTelemetry(
                source_code="DAM_DAILY",
                source_name="Department of Agricultural Marketing (DAM)",
                source_type="government",
                status="HEALTHY",
                latency_ms=12.4,
                last_sync=datetime.now(timezone.utc),
                is_fallback=False,
                success_count=1,
            ),
            "CHALDAL_RETAIL": SourceTelemetry(
                source_code="CHALDAL_RETAIL",
                source_name="Chaldal Online Grocery",
                source_type="retail_ecommerce",
                status="HEALTHY",
                latency_ms=28.6,
                last_sync=datetime.now(timezone.utc),
                is_fallback=False,
                success_count=1,
            ),
            "field_report": SourceTelemetry(
                source_code="field_report",
                source_name="Field Spot Report (Manual)",
                source_type="crowdsource",
                status="HEALTHY",
                latency_ms=2.1,
                last_sync=datetime.now(timezone.utc),
                is_fallback=False,
                success_count=1,
            ),
            "TCB_DAILY": SourceTelemetry(
                source_code="TCB_DAILY",
                source_name="Trading Corporation of Bangladesh (TCB)",
                source_type="statutory_body",
                status="HEALTHY",
                latency_ms=18.5,
                last_sync=datetime.now(timezone.utc),
                is_fallback=False,
                success_count=1,
            ),
            "PRESS_REPORT": SourceTelemetry(
                source_code="PRESS_REPORT",
                source_name="National Daily Press Spot Roundups",
                source_type="press",
                status="HEALTHY",
                latency_ms=8.2,
                last_sync=datetime.now(timezone.utc),
                is_fallback=False,
                success_count=1,
            ),
        }

    def record_attempt(
        self,
        source_code: str,
        latency_ms: float,
        success: bool,
        is_fallback: bool = False,
        error_message: Optional[str] = None,
    ) -> None:
        """Record telemetry from a harvest attempt."""
        if source_code not in self._sources:
            self._sources[source_code] = SourceTelemetry(
                source_code=source_code,
                source_name=source_code,
                source_type="external",
                status="HEALTHY",
                latency_ms=latency_ms,
            )

        telemetry = self._sources[source_code]
        telemetry.latency_ms = round(latency_ms, 2)
        telemetry.last_sync = datetime.now(timezone.utc)
        telemetry.is_fallback = is_fallback

        if success:
            telemetry.success_count += 1
            if is_fallback:
                telemetry.status = "DEGRADED"
                telemetry.last_error = error_message or "Live network unavailable; running on verified cached fixture"
            else:
                telemetry.status = "HEALTHY"
                telemetry.last_error = None
        else:
            telemetry.error_count += 1
            telemetry.status = "OFFLINE"
            telemetry.last_error = error_message or "Collector connection failed completely"

    def get_source_status(self, source_code: str) -> Optional[dict]:
        """Retrieve telemetry for a specific source."""
        telemetry = self._sources.get(source_code)
        if not telemetry:
            return None
        return asdict(telemetry)

    def get_source_telemetry(self, source_code: str) -> Optional[dict]:
        """Alias for get_source_status."""
        return self.get_source_status(source_code)

    def get_all_statuses(self) -> List[dict]:
        """Retrieve telemetry dictionary for all registered sources."""
        return [asdict(t) for t in self._sources.values()]


source_health_service = SourceHealthService()
