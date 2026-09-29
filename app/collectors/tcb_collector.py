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
from typing import Dict, List, Optional, Tuple
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

    DEFAULT_LIVE_URL = "https://tcb.gov.bd/pages/daily-rmps"
    FALLBACK_URLS = [
        "https://tcb.gov.bd/",
        "http://www.tcb.gov.bd/site/page/daily-market-prices",
    ]

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
        timeout_seconds: float = 12.0,
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

    def _fetch_live_xlsx_items(self) -> Tuple[List[Tuple[str, str, float, float]], bool, float, Optional[str]]:
        """
        Attempt to scrape the latest official TCB daily bulletin XLSX directly from tcb.gov.bd.
        Returns: (items_list, is_fallback, latency_ms, error_msg)
        where items_list = [(commodity_name, unit, min_price, max_price), ...]
        """
        import io
        import zipfile
        import xml.etree.ElementTree as ET

        start_time = time.perf_counter()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                r = client.get(self.live_url, headers=headers)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    detail_link = None
                    for a in soup.find_all("a"):
                        txt = a.get_text(strip=True)
                        href = a.get("href", "")
                        if "দেখুন" in txt and "daily-rmps" in href:
                            detail_link = href
                            break

                    if detail_link:
                        full_detail_url = "https://tcb.gov.bd" + detail_link if detail_link.startswith("/") else detail_link
                        detail_res = client.get(full_detail_url, headers=headers)
                        if detail_res.status_code == 200:
                            detail_soup = BeautifulSoup(detail_res.text, "html.parser")
                            xlsx_url = None
                            for a in detail_soup.find_all("a"):
                                h = a.get("href", "")
                                if "xlsx" in h or "oraclecloud" in h:
                                    xlsx_url = h
                                    break

                            if xlsx_url:
                                xr = client.get(xlsx_url, headers=headers)
                                if xr.status_code == 200 and len(xr.content) > 1000:
                                    z = zipfile.ZipFile(io.BytesIO(xr.content))
                                    shared = []
                                    if "xl/sharedStrings.xml" in z.namelist():
                                        for elem in ET.fromstring(z.read("xl/sharedStrings.xml")).iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
                                            shared.append(elem.text or "")
                                    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
                                    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                                    extracted = []
                                    for r_elem in sheet.findall(".//s:row", ns):
                                        cells = []
                                        for c in r_elem.findall("s:c", ns):
                                            v = c.find("s:v", ns)
                                            val = v.text if v is not None else ""
                                            if c.get("t") == "s" and val.isdigit():
                                                val = shared[int(val)]
                                            cells.append(val.strip())
                                        if len(cells) >= 4 and any(cells[2:4]):
                                            name = cells[0]
                                            unit_raw = cells[1] if len(cells) > 1 else "কেজি"
                                            unit = re.sub(r"^(প্রতি|per)\s*", "", unit_raw).strip() or "কেজি"
                                            unit = re.sub(r"\s*প্যা[ঃকেট]+", "", unit).strip() or "কেজি"

                                            # Check if unit has a quantity multiplier, e.g. "৫ লিটার" (5 liter bottle)
                                            qty_match = re.match(r"^([০-৯]+|\d+)\s*(লিটার|কেজি|হালি|ডজন)", unit)
                                            p_min_raw = cells[2] if len(cells) > 2 else ""
                                            p_max_raw = cells[3] if len(cells) > 3 else ""
                                            p_min = self._convert_bn_number(p_min_raw)
                                            p_max = self._convert_bn_number(p_max_raw)

                                            if qty_match:
                                                qty_num = self._convert_bn_number(qty_match.group(1))
                                                unit = qty_match.group(2)
                                                if qty_num and qty_num > 1:
                                                    if p_min:
                                                        p_min = round(p_min / qty_num, 2)
                                                    if p_max:
                                                        p_max = round(p_max / qty_num, 2)

                                            if (p_min or p_max) and name and len(name) > 1 and not any(ign in name for ign in ["নাম", "তারিখ", "মূল্য", "বাজার হতে", "কাগজ", "রড", "টিন", "সিমেন্ট", "কয়েল"]):
                                                if unit in ["কেজি", "লিটার", "হালি", "kg", "pc", "ডজন"]:
                                                    p_min_f = p_min or p_max
                                                    p_max_f = p_max or p_min
                                                    extracted.append((name, unit, p_min_f, p_max_f))

                                    if len(extracted) >= 5:
                                        latency_ms = (time.perf_counter() - start_time) * 1000.0
                                        source_health_service.record_attempt(
                                            source_code=self.source_code,
                                            latency_ms=latency_ms,
                                            success=True,
                                            is_fallback=False,
                                        )
                                        return extracted, False, latency_ms, None
        except Exception as exc:
            logger.debug(f"TCB live XLSX harvest attempt failed: {exc}")

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return [], True, latency_ms, "Live XLSX unavailable, using HTML table fallback"

    def _fetch_html(self) -> Tuple[str, bool, float, Optional[str]]:
        """
        Attempt to fetch live HTML via HTTP with exponential backoff retry jitter.
        Supports SSL bypass for government certs and multi-endpoint fallback.
        Returns: (html_content, is_fallback, latency_ms, error_msg)
        """
        start_time = time.perf_counter()
        last_error: Optional[str] = None
        candidate_urls = [self.live_url] + [u for u in self.FALLBACK_URLS if u != self.live_url]

        for target_url in candidate_urls:
            for attempt in range(self.max_retries + 1):
                if attempt > 0:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0.0, 0.5)
                    logger.info(f"TCB harvest retry attempt {attempt}/{self.max_retries} backing off for {delay:.2f}s")
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

                        if resp.status_code == 200 and len(resp.text.strip()) > 20:
                            source_health_service.record_attempt(
                                source_code=self.source_code,
                                latency_ms=latency_ms,
                                success=True,
                                is_fallback=False,
                            )
                            return resp.text, False, latency_ms, None
                        else:
                            last_error = f"HTTP {resp.status_code}: Endpoint returned non-200"
                except Exception as exc:
                    last_error = f"{exc.__class__.__name__}: {exc}"
                    logger.debug(f"TCB network error on {target_url} (attempt {attempt}): {exc}")

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
            raise FileNotFoundError(f"TCB fixture not found at {self.fixture_path}")

        source_health_service.record_attempt(
            source_code=self.source_code,
            latency_ms=latency_ms,
            success=True,
            is_fallback=True,
            error_message=last_error or "Fell back to cached fixture",
        )

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            return f.read(), True, latency_ms, last_error

    def _find_best_table(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Locate the commodity price table using multiple selector strategies and heuristic validation."""
        for selector in self.TABLE_SELECTORS:
            candidates = soup.select(selector)
            for table in candidates:
                rows = table.find_all("tr")
                if len(rows) < 2:
                    continue
                # Inspect table text for price bulletin keywords AND food unit indicators
                text = table.get_text()
                has_keywords = any(kw in text for kw in ["পণ্য", "commodity", "দর", "মূল্য", "সর্বনিম্ন", "খুচরা", "retail", "price"])
                has_units = any(u in text for u in ["কেজি", "লিটার", "হালি", "kg", "liter", "pc"])
                if has_keywords and has_units:
                    return table
        # Fallback to any table with at least 2 rows having >= 3 cells and unit mentions
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) >= 2:
                text = table.get_text()
                if any(u in text for u in ["কেজি", "লিটার", "হালি", "kg", "liter", "pc"]):
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
        """Harvest raw observations from TCB bulletin: HTML table or live XLSX bulletin."""
        observations: List[RawObservation] = []

        # Strategy 1: Adaptive HTML table parsing (with exponential retry backoff)
        html_content, is_fallback, _, _ = self._fetch_html()
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        table = self._find_best_table(soup)
        if table:
            rows = table.find_all("tr")
            if rows:
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

                    unit = re.sub(r"^(প্রতি|per)\s*", "", unit).strip() or "kg"
                    unit = re.sub(r"\s*প্যা[ঃকেট]+", "", unit).strip() or "kg"

                    observations.append(
                        RawObservation(
                            source_code=self.source_code,
                            market_name="Karwan Bazar",
                            raw_commodity_name=name,
                            raw_unit=unit,
                            raw_price=float(avg_price),
                            price_type="retail_avg",
                            observation_date=self.target_date,
                            completeness_score=0.90 if not is_fallback else 0.80,
                            is_fallback=is_fallback,
                        )
                    )

        # Strategy 2: If HTML had no price rows, harvest from official XLSX bulletin
        if not observations and not is_fallback:
            xlsx_items, is_xlsx_fallback, _, _ = self._fetch_live_xlsx_items()
            if xlsx_items and not is_xlsx_fallback:
                for name, unit, p_min, p_max in xlsx_items:
                    avg_p = round((p_min + p_max) / 2.0, 2)
                    observations.append(
                        RawObservation(
                            source_code=self.source_code,
                            market_name="Karwan Bazar",
                            raw_commodity_name=name,
                            raw_unit=unit,
                            raw_price=float(avg_p),
                            price_type="retail_avg",
                            observation_date=self.target_date,
                            completeness_score=0.95,
                            is_fallback=False,
                        )
                    )
                logger.info(f"TCB Collector harvested {len(observations)} live observations from official bulletin XLSX.")
                return observations

        logger.info(f"TCB Collector harvested {len(observations)} observations (Fallback={is_fallback})")
        return observations
