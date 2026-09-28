"""
app/collectors/tcb_collector.py
===============================
Autonomous harvester for Trading Corporation of Bangladesh (TCB) daily price bulletins.
Features adaptive request jitter, regex Bengali numeral parsing, and zero-downtime fixture fallback.
"""

import logging
import random
import re
import time
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)

BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


class TCBCollector(BaseCollector):
    """Harvests official TCB daily market bulletins with fallback resilience."""

    source_code = "TCB_DAILY"
    source_name = "Trading Corporation of Bangladesh"
    source_type = "statutory_body"
    reliability_score = 0.90

    DEFAULT_LIVE_URL = "http://www.tcb.gov.bd/site/page/daily-market-prices"

    def __init__(
        self,
        live_url: Optional[str] = None,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        timeout_seconds: float = 3.0,
    ):
        self.live_url = live_url or self.DEFAULT_LIVE_URL
        self.fixture_path = fixture_path or (settings.fixtures_dir / "tcb_sample_bulletin.html")
        self.target_date = target_date or date.today()
        self.timeout = timeout_seconds

    def _convert_bn_number(self, text: str) -> Optional[float]:
        """Convert Bengali numerals and range strings (e.g., '১০০-১১০') to float average."""
        if not text:
            return None
        trans = text.translate(BN_TO_EN).strip()
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", trans)]
        if not nums:
            return None
        return round(sum(nums) / len(nums), 2)

    def _fetch_html(self) -> Tuple[str, bool, float, Optional[str]]:
        """
        Fetch live TCB bulletin with adaptive jitter delay.
        Returns: (html_content, is_fallback, latency_ms, error_msg)
        """
        # Apply micro-jitter (100ms - 300ms) to prevent burst request throttling
        jitter = random.uniform(0.1, 0.3)
        time.sleep(jitter)

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "PricePulse-BD-Crawler/2.0 (Academic Research; Market Intelligence)",
                    "Accept": "text/html,application/xhtml+xml",
                }
                resp = client.get(self.live_url, headers=headers)
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                if resp.status_code == 200 and len(resp.text) > 200:
                    source_health_service.record_attempt(
                        source_code=self.source_code,
                        latency_ms=latency_ms,
                        success=True,
                    )
                    return resp.text, False, latency_ms, None
                else:
                    raise httpx.HTTPStatusError(
                        f"Non-200 HTTP response: {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(f"TCB live portal unreachable ({exc}). Falling back to cached fixture.")
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=False,
                is_fallback=True,
                error_message=str(exc),
            )
            if self.fixture_path.exists():
                return self.fixture_path.read_text(encoding="utf-8"), True, latency_ms, str(exc)
            return "", True, latency_ms, "Fixture missing"

    def collect(self) -> List[RawObservation]:
        """Harvest raw observations from TCB bulletin."""
        html_content, is_fallback, _, _ = self._fetch_html()
        if not html_content:
            return []

        observations: List[RawObservation] = []
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table")
        if not table:
            return []

        rows = table.find_all("tr")
        # Identify table headers
        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 4:
                continue

            # Standard TCB table format: [Serial, Commodity Name, Unit, Prev Price, Today Min, Today Max]
            # or [Serial, Commodity Name, Unit, Today Price Range]
            name = cells[1]
            unit = cells[2] if len(cells) > 2 else "kg"

            min_val = None
            max_val = None

            if len(cells) >= 6:
                min_val = self._convert_bn_number(cells[4])
                max_val = self._convert_bn_number(cells[5])
            elif len(cells) >= 4:
                min_val = self._convert_bn_number(cells[3])
                max_val = min_val

            if min_val is None and max_val is None:
                continue

            if min_val is not None and max_val is not None:
                avg_price = round((min_val + max_val) / 2.0, 2)
            else:
                avg_price = min_val or max_val

            observations.append(
                RawObservation(
                    source_code=self.source_code,
                    market_name="Dhaka Central Retail Benchmark",
                    raw_commodity_name=name,
                    raw_unit=unit,
                    raw_price=float(avg_price),
                    price_type="retail_avg",
                    observation_date=self.target_date,
                    completeness_score=0.90 if not is_fallback else 0.80,
                    is_fallback=is_fallback,
                )
            )

        logger.info(f"TCB Collector harvested {len(observations)} observations (Fallback={is_fallback})")
        return observations
