"""
Resilient live collector for Department of Agricultural Marketing (DAM) bulletins.
Attempts live HTTP harvesting with automatic, seamless fallback to verified cached fixtures.
"""

import logging
import time
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)


class DAMLiveCollector(BaseCollector):
    """Harvests live DAM daily market bulletin HTML with zero-downtime fixture fallback."""

    source_code = "DAM_DAILY"
    source_name = "Department of Agricultural Marketing"
    source_type = "government"
    reliability_score = 0.95

    # Public DAM daily bulletin portal URL
    DEFAULT_LIVE_URL = "http://www.dam.gov.bd/daily-market-price"

    def __init__(
        self,
        live_url: Optional[str] = None,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        timeout_seconds: float = 3.0,
    ):
        self.live_url = live_url or self.DEFAULT_LIVE_URL
        self.fixture_path = fixture_path or (settings.fixtures_dir / "dam_bulletin_sample.html")
        self.target_date = target_date
        self.timeout = timeout_seconds

    def _fetch_html(self) -> tuple[str, bool, float, Optional[str]]:
        """
        Attempt to fetch live HTML via HTTP.
        Returns: (html_content, is_fallback, latency_ms, error_msg)
        """
        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                headers = {"User-Agent": "PricePulse-BD-Researcher/1.0 (+http://localhost:8000)"}
                resp = client.get(self.live_url, headers=headers)
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                if resp.status_code == 200 and len(resp.text) > 200:
                    source_health_service.record_attempt(
                        source_code=self.source_code,
                        latency_ms=latency_ms,
                        success=True,
                        is_fallback=False,
                    )
                    return resp.text, False, latency_ms, None
                else:
                    msg = f"Live endpoint returned HTTP {resp.status_code}"
                    logger.warning(f"DAM Live Collector: {msg}. Falling back to cached fixture.")
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            msg = f"Network connection error ({exc.__class__.__name__})"
            logger.warning(f"DAM Live Collector: {msg}. Falling back to cached fixture.")

        # Fallback to local verified fixture
        if not self.fixture_path.exists():
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=False,
                is_fallback=False,
                error_message="Both live fetch and local fixture are missing",
            )
            raise FileNotFoundError(f"DAM fixture not found at {self.fixture_path}")

        source_health_service.record_attempt(
            source_code=self.source_code,
            latency_ms=latency_ms,
            success=True,
            is_fallback=True,
            error_message=msg,
        )

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            return f.read(), True, latency_ms, msg

    def collect(self) -> List[RawObservation]:
        """Harvest observations from live bulletin or fallback fixture."""
        html_content, is_fallback, _, _ = self._fetch_html()
        soup = BeautifulSoup(html_content, "html.parser")

        if self.target_date:
            obs_date = self.target_date
        else:
            date_elem = soup.find(class_="bulletin-date")
            obs_date = date.today()
            if date_elem and date_elem.get("data-date"):
                try:
                    obs_date = datetime.strptime(date_elem["data-date"], "%Y-%m-%d").date()
                except ValueError:
                    pass

        observations: List[RawObservation] = []
        market_sections = soup.find_all("div", class_="market-section")

        for section in market_sections:
            market_name = section.get("data-market", "Unknown Market").strip()
            rows = section.find_all("tr", class_="item-row")

            for row in rows:
                comm_elem = row.find(class_="commodity-name")
                unit_elem = row.find(class_="unit-name")
                if not comm_elem or not unit_elem:
                    continue

                raw_comm = comm_elem.get_text(strip=True)
                raw_unit = unit_elem.get_text(strip=True)

                price_mappings = [
                    ("price-retail-avg", "retail_avg"),
                    ("price-wholesale-avg", "wholesale_avg"),
                    ("price-wholesale-min", "wholesale_min"),
                    ("price-wholesale-max", "wholesale_max"),
                ]

                for css_class, price_type in price_mappings:
                    cell = row.find(class_=css_class)
                    if not cell:
                        continue
                    try:
                        price_val = float(cell.get_text(strip=True))
                    except ValueError:
                        continue

                    observations.append(
                        RawObservation(
                            source_code=self.source_code,
                            market_name=market_name,
                            raw_commodity_name=raw_comm,
                            raw_unit=raw_unit,
                            raw_price=price_val,
                            price_type=price_type,
                            observation_date=obs_date,
                            completeness_score=0.90 if is_fallback else 1.0,
                            is_fallback=is_fallback,
                        )
                    )

        return observations
