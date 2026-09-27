"""
Resilient live collector for public digital grocery retail catalogs (Chaldal format).
Implements rate-limited retries, backoff, and seamless fallback to verified cached fixtures.
"""

import json
import logging
import time
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
import httpx

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)


class ChaldalLiveCollector(BaseCollector):
    """Harvests live online retail catalog feeds with retry/backoff and fixture fallback."""

    source_code = "CHALDAL_RETAIL"
    source_name = "Chaldal Online Grocery"
    source_type = "retail_ecommerce"
    reliability_score = 0.88

    # Public catalog endpoint or mock endpoint
    DEFAULT_API_URL = "https://catalog.chaldal.com/api/products"

    def __init__(
        self,
        api_url: Optional[str] = None,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        max_retries: int = 2,
        timeout_seconds: float = 3.0,
    ):
        self.api_url = api_url or self.DEFAULT_API_URL
        self.fixture_path = fixture_path or (settings.fixtures_dir / "chaldal_catalog_sample.json")
        self.target_date = target_date
        self.max_retries = max_retries
        self.timeout = timeout_seconds

    def _fetch_catalog_data(self) -> tuple[dict, bool, float, Optional[str]]:
        """
        Attempt live network fetch with retry and exponential backoff.
        Returns: (catalog_dict, is_fallback, latency_ms, error_msg)
        """
        start_time = time.perf_counter()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                headers = {
                    "User-Agent": "PricePulse-BD-Academic/1.0 (+http://localhost:8000)",
                    "Accept": "application/json",
                }
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(self.api_url, headers=headers)
                    latency_ms = (time.perf_counter() - start_time) * 1000.0
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict) and "items" in data:
                            source_health_service.record_attempt(
                                source_code=self.source_code,
                                latency_ms=latency_ms,
                                success=True,
                                is_fallback=False,
                            )
                            return data, False, latency_ms, None
                    last_error = f"HTTP {resp.status_code}"
            except Exception as e:
                last_error = f"{e.__class__.__name__}"
                time.sleep(0.1 * (2 ** attempt))

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        msg = f"Live catalog unreachable ({last_error}). Falling back to cached fixture."
        logger.warning(f"Chaldal Live Collector: {msg}")

        # Fallback to local verified fixture
        if not self.fixture_path.exists():
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=False,
                is_fallback=False,
                error_message="Both live fetch and local fixture missing",
            )
            raise FileNotFoundError(f"Chaldal fixture not found at {self.fixture_path}")

        source_health_service.record_attempt(
            source_code=self.source_code,
            latency_ms=latency_ms,
            success=True,
            is_fallback=True,
            error_message=msg,
        )

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            return json.load(f), True, latency_ms, msg

    def collect(self) -> List[RawObservation]:
        """Harvest observations from live feed or cached fixture."""
        data, is_fallback, _, _ = self._fetch_catalog_data()
        market_name = data.get("market_name", "Chaldal Online Hub")

        if self.target_date:
            obs_date = self.target_date
        else:
            cat_date_str = data.get("catalog_date")
            obs_date = date.today()
            if cat_date_str:
                try:
                    obs_date = datetime.strptime(cat_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass

        observations: List[RawObservation] = []

        for item in data.get("items", []):
            if not item.get("in_stock", True):
                continue

            raw_name = item.get("name", "")
            raw_price = float(item.get("price", 0.0))
            package_unit = item.get("package_unit", "1 kg")

            if raw_price <= 0.0:
                continue

            observations.append(
                RawObservation(
                    source_code=self.source_code,
                    market_name=market_name,
                    raw_commodity_name=raw_name,
                    raw_unit=package_unit,
                    raw_price=raw_price,
                    price_type="retail_avg",
                    observation_date=obs_date,
                    completeness_score=0.85 if is_fallback else 0.95,
                    is_fallback=is_fallback,
                )
            )

        return observations
