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

    # Multi-strategy CSS selectors for resilient table discovery across upstream DOM updates
    TABLE_SELECTORS = [
        "table.tcb-price-table",
        "table.price-table",
        "table.content-table",
        ".content-table table",
        "table.table-bordered",
        "table.table",
        "div.content table",
        "table",
    ]

    def __init__(
        self,
        live_url: Optional[str] = None,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        timeout_seconds: float = 3.0,
        max_retries: int = 2,
        base_delay: float = 0.5,
    ):
        self.live_url = live_url or self.DEFAULT_LIVE_URL
        self.fixture_path = fixture_path or (settings.fixtures_dir / "tcb_sample_bulletin.html")
        self.target_date = target_date or date.today()
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _convert_bn_number(self, text: str) -> Optional[float]:
        """
        Convert Bengali and English numerals and range strings (e.g., '১২০ - ১৩০', '120 - 130', '১২০ থেকে ১৩০')
        to a single float average price.
        """
        if not text:
            return None
        # Normalize Bengali digits to English
        trans = str(text).translate(BN_TO_EN).strip()
        # Clean currency mentions and common units from price cell
        trans = re.sub(r"(?i)(tk|taka|টাকা|bdt|\/kg|\/pc)", "", trans)
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", trans)]
        if not nums:
            return None
        if len(nums) == 1:
            return round(nums[0], 2)
        # Average range values e.g. [120, 130] -> 125.0
        return round(sum(nums) / len(nums), 2)

    def _fetch_html(self) -> Tuple[str, bool, float, Optional[str]]:
        """
        Fetch live TCB bulletin with exponential backoff and randomized jitter.
        Returns: (html_content, is_fallback, latency_ms, error_msg)
        """
        start_time = time.perf_counter()
        last_error: Optional[str] = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                # Exponential backoff with randomized jitter: base * 2^attempt + uniform(0, 0.5)
                delay = self.base_delay * (2 ** attempt) + random.uniform(0.0, 0.5)
                logger.info(f"TCB harvest retry attempt {attempt}/{self.max_retries} backing off for {delay:.2f}s")
                time.sleep(delay)
            else:
                # Micro-jitter to prevent burst requests
                time.sleep(random.uniform(0.05, 0.15))

            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                    headers = {
                        "User-Agent": "PricePulse-BD-Crawler/2.0 (Academic Research; Market Intelligence)",
                        "Accept": "text/html,application/xhtml+xml",
                    }
                    resp = client.get(self.live_url, headers=headers)
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    if resp.status_code == 200 and len(resp.text) > 50:
                        source_health_service.record_attempt(
                            source_code=self.source_code,
                            latency_ms=latency_ms,
                            success=True,
                            is_fallback=False,
                        )
                        return resp.text, False, latency_ms, None
                    else:
                        last_error = f"HTTP {resp.status_code}: Non-200 bulletin response"
                        logger.warning(f"TCB live endpoint returned non-200: {resp.status_code}")
            except httpx.ConnectTimeout as exc:
                last_error = f"ConnectTimeout: {exc}"
                logger.warning(f"TCB attempt {attempt} timed out: {exc}")
            except httpx.ConnectError as exc:
                last_error = f"ConnectError: {exc}"
                logger.warning(f"TCB attempt {attempt} connection failed: {exc}")
            except Exception as exc:
                last_error = f"{exc.__class__.__name__}: {exc}"
                logger.warning(f"TCB attempt {attempt} error: {exc}")

        # Fallback to local verified fixture
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(f"TCB live portal unreachable ({last_error}). Falling back to cached fixture.")

        if self.fixture_path.exists():
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=True,
                is_fallback=True,
                error_message=last_error,
            )
            return self.fixture_path.read_text(encoding="utf-8"), True, latency_ms, last_error

        source_health_service.record_attempt(
            source_code=self.source_code,
            latency_ms=latency_ms,
            success=False,
            is_fallback=False,
            error_message="Fixture missing",
        )
        return "", True, latency_ms, "Fixture missing"

    def _find_best_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Locate the commodity price table using multiple selector strategies and heuristic validation."""
        for selector in self.TABLE_SELECTORS:
            candidates = soup.select(selector)
            for table in candidates:
                rows = table.find_all("tr")
                if len(rows) < 2:
                    continue
                # Inspect table text for price bulletin keywords
                text = table.get_text()
                if any(kw in text for kw in ["পণ্য", "commodity", "দর", "মূল্য", "সর্বনিম্ন", "খুচরা", "retail", "price"]):
                    return table
        # Fallback to any table with at least 2 rows having >= 3 cells
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) >= 2:
                cells = rows[1].find_all(["td", "th"])
                if len(cells) >= 3:
                    return table
        return None

    def _detect_column_indices(self, header_cells: List[str]) -> Dict[str, int]:
        """Dynamically detect column mapping from header cells to survive upstream column order mutations."""
        mapping: Dict[str, int] = {}
        for idx, text in enumerate(header_cells):
            t = text.lower()
            if any(k in t for k in ["পণ্য", "commodity", "item", "নাম"]):
                mapping.setdefault("name", idx)
            elif any(k in t for k in ["একক", "unit"]):
                mapping.setdefault("unit", idx)
            elif any(k in t for k in ["সর্বনিম্ন", "min"]):
                mapping.setdefault("min", idx)
            elif any(k in t for k in ["সর্বোচ্চ", "max"]):
                mapping.setdefault("max", idx)
            elif any(k in t for k in ["আজকের", "দর", "মূল্য", "price", "খুচরা", "retail"]):
                mapping.setdefault("price", idx)
        return mapping

    def collect(self) -> List[RawObservation]:
        """Harvest raw observations from TCB bulletin with adaptive DOM parsing."""
        html_content, is_fallback, _, _ = self._fetch_html()
        if not html_content:
            return []

        observations: List[RawObservation] = []
        soup = BeautifulSoup(html_content, "html.parser")
        table = self._find_best_table(soup)
        if not table:
            logger.warning("No suitable price table found in TCB bulletin HTML.")
            return []

        rows = table.find_all("tr")
        if not rows:
            return []

        # Detect column mapping from the first row (headers)
        first_row_cells = [c.get_text(strip=True) for c in rows[0].find_all(["td", "th"])]
        col_map = self._detect_column_indices(first_row_cells)

        for row in rows[1:]:
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 3:
                continue

            # Adaptive extraction based on detected column mapping
            name = None
            unit = "kg"
            avg_price = None

            if "name" in col_map and col_map["name"] < len(cells):
                name = cells[col_map["name"]]
            elif len(cells) >= 2:
                name = cells[1]

            if not name or len(name) < 2:
                continue

            if "unit" in col_map and col_map["unit"] < len(cells):
                unit = cells[col_map["unit"]] or "kg"
            elif len(cells) >= 3:
                unit = cells[2] or "kg"

            # Price extraction: check min/max columns first
            min_val = None
            max_val = None
            if "min" in col_map and col_map["min"] < len(cells):
                min_val = self._convert_bn_number(cells[col_map["min"]])
            if "max" in col_map and col_map["max"] < len(cells):
                max_val = self._convert_bn_number(cells[col_map["max"]])

            if min_val is not None and max_val is not None:
                avg_price = round((min_val + max_val) / 2.0, 2)
            elif min_val is not None:
                avg_price = min_val
            elif max_val is not None:
                avg_price = max_val
            elif "price" in col_map and col_map["price"] < len(cells):
                avg_price = self._convert_bn_number(cells[col_map["price"]])
            else:
                # Positional fallback
                if len(cells) >= 6:
                    p_min = self._convert_bn_number(cells[4])
                    p_max = self._convert_bn_number(cells[5])
                    if p_min is not None and p_max is not None:
                        avg_price = round((p_min + p_max) / 2.0, 2)
                    else:
                        avg_price = p_min or p_max
                elif len(cells) >= 4:
                    avg_price = self._convert_bn_number(cells[3])
                elif len(cells) >= 3:
                    avg_price = self._convert_bn_number(cells[2])

            if avg_price is None or avg_price <= 0:
                continue

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
