"""
Transparent modeled connector for Pandamart Express Grocery.
Documents the technical and legal access limitation (Cloudflare Bot Management 403,
lack of public unauthenticated web catalog, mobile app only) and exposes
transparent modeled benchmarks without inventing scrapers or bypassing protections.
"""

import json
import logging
from datetime import date
from pathlib import Path
from typing import List, Optional

from app.collectors.base import BaseCollector, CollectionStatus, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)


class PandamartCollector(BaseCollector):
    """
    Modeled collector for Pandamart express grocery delivery.
    Explicitly marked as MODELED rather than LIVE.
    """

    source_code = "PANDAMART_MODELED"
    source_name = "Pandamart Express Grocery"
    source_type = "modeled_benchmark"
    reliability_score = 0.75
    default_collection_status = CollectionStatus.MODELED

    LIMITATION_REASON = (
        "Public web catalog unavailable; open endpoints return Cloudflare HTTP 403 / "
        "Bot Management restrictions, and storefront requires authenticated mobile app. "
        "Retaining transparent modeled benchmark (+8% express category spread)."
    )

    def __init__(
        self,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
    ):
        self.fixture_path = fixture_path or (settings.fixtures_dir / "pandamart_modeled_sample.json")
        self.target_date = target_date

    def collect(self) -> List[RawObservation]:
        """Produce transparent modeled observations and record telemetry."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Pandamart fixture not found at {self.fixture_path}")

        source_health_service.record_attempt(
            source_code=self.source_code,
            latency_ms=1.5,
            success=True,
            is_fallback=True,
            error_message=self.LIMITATION_REASON,
        )

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        market_name = data.get("market_name", "Pandamart Darkstore Network")
        obs_date = self.target_date or date.today()
        observations: List[RawObservation] = []

        for item in data.get("items", []):
            raw_name = str(item.get("name") or "").strip()
            raw_price = float(item.get("price") or 0.0)
            unit = str(item.get("unit") or "1 kg").strip()

            if not raw_name or raw_price <= 0.0:
                continue

            observations.append(
                RawObservation(
                    source_code=self.source_code,
                    market_name=market_name,
                    raw_commodity_name=raw_name,
                    raw_unit=unit,
                    raw_price=raw_price,
                    price_type="retail_avg",
                    observation_date=obs_date,
                    completeness_score=0.75,
                    is_fallback=True,
                    collection_status=CollectionStatus.MODELED.value,
                    source_url="https://foodpanda.com.bd/pandamart",
                    raw_package_size=unit,
                    error_message=self.LIMITATION_REASON,
                )
            )

        return observations
