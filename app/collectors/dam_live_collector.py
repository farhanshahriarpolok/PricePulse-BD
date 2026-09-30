"""
Resilient live collector for Department of Agricultural Marketing (DAM) bulletins.
Attempts live HTTP harvesting with automatic, seamless fallback to verified cached fixtures.
"""

import logging
import random
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)

BN_TO_EN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


class DAMLiveCollector(BaseCollector):
    """Harvests live DAM daily market bulletin HTML with zero-downtime fixture fallback."""

    source_code = "DAM_DAILY"
    source_name = "Department of Agricultural Marketing"
    source_type = "government"
    reliability_score = 0.95

    # Public DAM daily bulletin portal URLs
    DEFAULT_LIVE_URL = "https://market.dam.gov.bd/market_daily_price_report?L=B"
    FALLBACK_LIVE_URLS = [
        "https://market.dam.gov.bd/",
    ]

    def __init__(
        self,
        live_url: Optional[str] = None,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        timeout_seconds: float = 15.0,
        max_retries: int = 2,
        base_delay: float = 0.5,
    ):
        self.live_url = live_url or self.DEFAULT_LIVE_URL
        self.fixture_path = fixture_path or (settings.fixtures_dir / "dam_bulletin_sample.html")
        self.target_date = target_date
        self.timeout = timeout_seconds
        self.max_retries = max_retries
        self.base_delay = base_delay

    @staticmethod
    def _convert_num(text: Optional[str]) -> Optional[float]:
        """Convert English or Bengali numeric string to float."""
        if not text:
            return None
        trans = str(text).translate(BN_TO_EN).strip()
        trans = re.sub(r"(?i)(tk|taka|টাকা|bdt|\/kg|\/pc)", "", trans)
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", trans)]
        if not nums:
            return None
        return nums[0] if len(nums) == 1 else round(sum(nums) / len(nums), 2)

    def _fetch_html(self) -> Tuple[str, bool, float, Optional[str]]:
        """
        Attempt to fetch live HTML via HTTP with exponential backoff retry jitter.
        Supports SSL bypass for government self-signed certs and multi-endpoint fallback.
        Returns: (html_content, is_fallback, latency_ms, error_msg)
        """
        start_time = time.perf_counter()
        last_error: Optional[str] = None
        candidate_urls = [self.live_url] + [u for u in self.FALLBACK_LIVE_URLS if u != self.live_url]

        for target_url in candidate_urls:
            for attempt in range(self.max_retries + 1):
                if attempt > 0:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0.0, 0.5)
                    logger.info(f"DAM harvest retry attempt {attempt}/{self.max_retries} backing off for {delay:.2f}s")
                    time.sleep(delay)
                else:
                    time.sleep(random.uniform(0.05, 0.15))

                try:
                    with httpx.Client(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        }
                        resp = client.get(target_url, headers=headers)
                        latency_ms = (time.perf_counter() - start_time) * 1000.0

                        if resp.status_code == 200 and len(resp.text) > 200:
                            # Verify page has real commodity price rows or tables
                            test_soup = BeautifulSoup(resp.text, "html.parser")
                            has_price_content = (
                                len(test_soup.find_all(class_="item-row")) > 0
                                or len(test_soup.find_all(class_="stockbox")) > 0
                                or any(
                                    any(k in t.get_text() for k in ["পণ্যের নাম", "খুচরা", "পাইকারি"])
                                    and len(t.find_all("tr")) >= 3
                                    for t in test_soup.find_all("table")
                                )
                            )
                            if has_price_content:
                                source_health_service.record_attempt(
                                    source_code=self.source_code,
                                    latency_ms=latency_ms,
                                    success=True,
                                    is_fallback=False,
                                )
                                return resp.text, False, latency_ms, None
                            else:
                                last_error = "Page retrieved but lacked tabular commodity price rows"
                        else:
                            last_error = f"HTTP {resp.status_code}: Endpoint returned non-200"
                except Exception as exc:
                    last_error = f"{exc.__class__.__name__}: {exc}"
                    logger.debug(f"DAM Live Collector network error on {target_url} (attempt {attempt}): {exc}")

        # Fallback to local verified fixture
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        if not self.fixture_path.exists():
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=False,
                is_fallback=False,
                error_message=last_error or "Both live fetch and local fixture are missing",
            )
            raise FileNotFoundError(f"DAM fixture not found at {self.fixture_path}")

        source_health_service.record_attempt(
            source_code=self.source_code,
            latency_ms=latency_ms,
            success=True,
            is_fallback=True,
            error_message=last_error or "Fell back to cached fixture",
        )

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            return f.read(), True, latency_ms, last_error

    def _detect_dam_columns(self, header_cells: List[str]) -> Dict[str, int]:
        """Dynamically detect column mapping for wholesale vs retail prices in DAM tables."""
        mapping: Dict[str, int] = {}
        for idx, text in enumerate(header_cells):
            t = text.lower()
            if any(k in t for k in ["পণ্যের নাম", "commodity", "item", "নাম"]):
                mapping.setdefault("commodity", idx)
            elif any(k in t for k in ["একক", "unit"]):
                mapping.setdefault("unit", idx)
            elif any(k in t for k in ["খুচরা", "retail"]):
                mapping.setdefault("retail_avg", idx)
            elif any(k in t for k in ["পাইকারি সর্বনিম্ন", "wholesale min"]):
                mapping.setdefault("wholesale_min", idx)
            elif any(k in t for k in ["পাইকারি সর্বোচ্চ", "wholesale max"]):
                mapping.setdefault("wholesale_max", idx)
            elif any(k in t for k in ["পাইকারি গড়", "পাইকারি গড়", "wholesale avg", "wholesale price", "wholesale", "পাইকারি"]):
                mapping.setdefault("wholesale_avg", idx)
        return mapping

    def _parse_table_rows(
        self,
        table: BeautifulSoup,
        market_name: str,
        obs_date: date,
        is_fallback: bool,
    ) -> List[RawObservation]:
        """Parse observations from a table using CSS classes or adaptive header mapping."""
        observations: List[RawObservation] = []
        rows = table.find_all("tr")
        if not rows:
            return observations

        # Detect headers
        header_row = rows[0]
        header_cells = [c.get_text(strip=True) for c in header_row.find_all(["th", "td"])]
        col_map = self._detect_dam_columns(header_cells)

        for row in rows[1:]:
            # Strategy A: Use class names if present
            comm_elem = row.find(class_="commodity-name")
            unit_elem = row.find(class_="unit-name")

            if comm_elem and unit_elem:
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
                    price_val = self._convert_num(cell.get_text(strip=True))
                    if price_val is not None and price_val > 0:
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
                continue

            # Strategy B: Adaptive column index mapping
            cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
            if len(cells) < 3:
                continue

            raw_comm = None
            if "commodity" in col_map and col_map["commodity"] < len(cells):
                raw_comm = cells[col_map["commodity"]]
            elif len(cells) >= 2:
                raw_comm = cells[1]

            if not raw_comm or len(raw_comm) < 2:
                continue

            raw_unit = "kg"
            if "unit" in col_map and col_map["unit"] < len(cells):
                raw_unit = cells[col_map["unit"]] or "kg"
            elif len(cells) >= 3:
                raw_unit = cells[2] or "kg"

            column_targets = [
                ("retail_avg", "retail_avg"),
                ("wholesale_avg", "wholesale_avg"),
                ("wholesale_min", "wholesale_min"),
                ("wholesale_max", "wholesale_max"),
            ]

            for key, price_type in column_targets:
                if key in col_map and col_map[key] < len(cells):
                    price_val = self._convert_num(cells[col_map[key]])
                    if price_val is not None and price_val > 0:
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

    def collect(self) -> List[RawObservation]:
        """Harvest observations from live bulletin or fallback fixture with adaptive DOM parsing."""
        html_content, is_fallback, _, _ = self._fetch_html()
        return self._parse_html(html_content, is_fallback)

    def _parse_html(self, html_content: str, is_fallback: bool = False) -> List[RawObservation]:
        """Parse HTML string into RawObservation objects."""
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

        # Strategy 1: Check for live stockbox elements (used on DAM daily market price portal ticker)
        stockboxes = soup.find_all(class_="stockbox")
        if stockboxes:
            for s in stockboxes:
                stext = s.get_text(strip=True)
                m = re.match(r"^(.*?):\s*([০-৯0-9\.]+)\s*-\s*([০-৯0-9\.]+)", stext)
                if m:
                    comm_name = m.group(1).strip()
                    p_min = self._convert_num(m.group(2))
                    p_max = self._convert_num(m.group(3))

                    if any(u in comm_name for u in ["ডিম", "হালি"]):
                        unit = "হালি"
                    elif any(u in comm_name for u in ["তেল", "লিটার"]):
                        unit = "লিটার"
                    else:
                        unit = "কেজি"

                    market_name = "Dhaka Central Market"
                    is_wholesale = any(w in comm_name.lower() or w in stext.lower() for w in ["পাইকারি", "wholesale"])
                    price_type = "wholesale_avg" if is_wholesale else "retail_avg"
                    comm_name_clean = re.sub(r"\s*\((খুচরা|পাইকারি|retail|wholesale)\)", "", comm_name, flags=re.IGNORECASE).strip()

                    # An intra-day ticker range (e.g. 30 - 35 Tk) represents min-max prices within that tier,
                    # NOT wholesale vs retail. Compute the arithmetic mean for the channel average observation.
                    if p_min is not None and p_max is not None and p_min > 0 and p_max > 0:
                        avg_price = round((p_min + p_max) / 2.0, 2)
                    elif p_min is not None and p_min > 0:
                        avg_price = p_min
                    elif p_max is not None and p_max > 0:
                        avg_price = p_max
                    else:
                        avg_price = None

                    if avg_price is not None and avg_price > 0:
                        observations.append(
                            RawObservation(
                                source_code=self.source_code,
                                market_name=market_name,
                                raw_commodity_name=comm_name_clean,
                                raw_unit=unit,
                                raw_price=avg_price,
                                price_type=price_type,
                                observation_date=obs_date,
                                completeness_score=1.0 if not is_fallback else 0.90,
                                is_fallback=is_fallback,
                            )
                        )
            if observations:
                logger.info(f"DAM Collector harvested {len(observations)} live ticker observations (Fallback={is_fallback})")
                return observations

        # Strategy 2: Tabular market sections
        market_sections = soup.find_all("div", class_="market-section")

        if market_sections:
            for section in market_sections:
                market_name = section.get("data-market", "Unknown Market").strip()
                table = section.find("table")
                if table:
                    observations.extend(self._parse_table_rows(table, market_name, obs_date, is_fallback))
                else:
                    # Look for tr.item-row directly in section
                    pass
        else:
            # Fallback to any tables in the document
            for table in soup.find_all("table"):
                market_name = table.get("data-market", "Karwan Bazar")
                observations.extend(self._parse_table_rows(table, market_name, obs_date, is_fallback))

        if not observations and not is_fallback and self.fixture_path.exists():
            logger.warning("DAM live response contained no parseable commodity rows; falling back to fixture")
            is_fallback = True
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                fix_soup = BeautifulSoup(f.read(), "html.parser")
                for table in fix_soup.find_all("table"):
                    market_name = table.get("data-market", "Karwan Bazar")
                    observations.extend(self._parse_table_rows(table, market_name, obs_date, is_fallback=True))

        logger.info(f"DAM Collector harvested {len(observations)} observations (Fallback={is_fallback})")
        return observations
