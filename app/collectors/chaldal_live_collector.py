"""
Resilient live collector for public digital grocery retail catalogs (Chaldal / digital storefronts).
Implements rate-limited retries, backoff, resilient JSON & HTML DOM CSS extraction,
dynamic stock status filtering, package size / unit price calculations, and seamless fallback
to verified cached fixtures.
"""

import json
import logging
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)


class ChaldalLiveCollector(BaseCollector):
    """Harvests live online retail catalog feeds with retry/backoff, DOM/JSON extraction, and fixture fallback."""

    source_code = "CHALDAL_RETAIL"
    source_name = "Chaldal Online Grocery"
    source_type = "retail_ecommerce"
    reliability_score = 0.88

    # Public catalog endpoint or mock endpoint
    DEFAULT_API_URL = "https://catalog.chaldal.com/api/products"

    # Resilient user agent for public commodity market tracking
    DEFAULT_USER_AGENT = "PricePulse-BD/1.0 (National Commodity Market Intelligence; +https://pricepulse.bd)"

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

    @staticmethod
    def _is_in_stock(item: Dict[str, Any]) -> bool:
        """Dynamically evaluate whether an extracted item is currently available in stock."""
        # 1. Explicit boolean flags
        if item.get("in_stock") is False:
            return False
        if item.get("out_of_stock") is True or item.get("is_out_of_stock") is True:
            return False
        if item.get("available") is False or item.get("is_available") is False:
            return False

        # 2. String status values
        status_str = str(item.get("stock_status") or item.get("status") or "").strip().lower()
        if status_str in ("out_of_stock", "stockout", "unavailable", "sold_out", "discontinued"):
            return False

        # 3. Numeric inventory count if present
        qty = item.get("stock_quantity") or item.get("quantity_available")
        if qty is not None:
            try:
                if float(qty) <= 0:
                    return False
            except (ValueError, TypeError):
                pass

        return True

    @staticmethod
    def _extract_item_metrics(item: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Extract canonical name, raw price, and raw package unit from item dictionary.
        Supports unit extraction from item name strings if package_unit is absent.
        """
        raw_name = str(item.get("name") or item.get("title") or item.get("product_name") or "").strip()

        # Resilient price resolution: price, discounted_price, mrp, unit_price
        price_val = 0.0
        for p_key in ("price", "discounted_price", "special_price", "mrp", "unit_price"):
            val = item.get(p_key)
            if val is not None:
                try:
                    p_float = float(val)
                    if p_float > 0:
                        price_val = p_float
                        break
                except (ValueError, TypeError):
                    continue

        # Package unit resolution
        package_unit = item.get("package_unit") or item.get("unit") or item.get("pack_size") or ""
        if not package_unit and raw_name:
            # Match customary units embedded in product name (e.g., '1 kg', '500 gm', '2 Liter', '12 pcs')
            unit_match = re.search(
                r"(\d+(?:\.\d+)?\s*(?:kg|gm|g|gram|liter|litre|ltr|l|ml|pc|pcs|হালি|পোয়া|কেজি|লিটার))",
                raw_name,
                re.IGNORECASE,
            )
            if unit_match:
                package_unit = unit_match.group(1).strip()
            else:
                package_unit = "1 kg"

        return raw_name, price_val, package_unit

    def _parse_html_catalog(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract product cards and prices from storefront HTML markup using CSS selectors."""
        soup = BeautifulSoup(html_content, "html.parser")
        items = []

        # Find product card nodes across common e-commerce CSS classes
        selectors = [
            ".productCard",
            ".product",
            "[data-product-id]",
            ".catalog-item",
            ".storefront-product",
        ]

        product_nodes = []
        for sel in selectors:
            nodes = soup.select(sel)
            if nodes:
                product_nodes = nodes
                break

        for node in product_nodes:
            # Extract name
            name_el = node.select_one(".name, .product-name, h3, .title")
            name = name_el.get_text(strip=True) if name_el else ""

            # Extract price
            price_el = node.select_one(".price, .current-price, .discountedPrice")
            price_str = price_el.get_text(strip=True) if price_el else ""
            num_match = re.search(r"(\d+(?:\.\d+)?)", price_str.replace(",", ""))
            price = float(num_match.group(1)) if num_match else 0.0

            # Extract package unit
            unit_el = node.select_one(".subText, .package-unit, .unit")
            unit = unit_el.get_text(strip=True) if unit_el else ""

            # Stock indicator
            out_of_stock = bool(node.select_one(".outOfStock, .soldOut, .unavailable"))

            if name and price > 0:
                items.append({
                    "name": name,
                    "price": price,
                    "package_unit": unit,
                    "in_stock": not out_of_stock,
                })

        return items

    def _fetch_catalog_data(self) -> Tuple[dict, bool, float, Optional[str]]:
        """
        Attempt live network fetch with retry, exponential backoff, and CSS/JSON extraction.
        Returns: (catalog_dict, is_fallback, latency_ms, error_msg)
        """
        start_time = time.perf_counter()
        last_error = None

        for attempt in range(self.max_retries):
            try:
                headers = {
                    "User-Agent": self.DEFAULT_USER_AGENT,
                    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
                }
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(self.api_url, headers=headers)
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    if resp.status_code == 200:
                        content_type = resp.headers.get("content-type", "").lower()
                        # 1. JSON endpoint
                        if "json" in content_type or resp.text.strip().startswith("{") or resp.text.strip().startswith("["):
                            try:
                                data = resp.json()
                                items_list = None
                                if isinstance(data, dict):
                                    if "items" in data and isinstance(data["items"], list):
                                        items_list = data["items"]
                                    elif "products" in data and isinstance(data["products"], list):
                                        items_list = data["products"]
                                    elif "data" in data and isinstance(data["data"], dict) and "products" in data["data"]:
                                        items_list = data["data"]["products"]
                                elif isinstance(data, list):
                                    items_list = data

                                if items_list is not None:
                                    catalog_payload = {
                                        "market_name": data.get("market_name", "Chaldal Online Hub") if isinstance(data, dict) else "Chaldal Online Hub",
                                        "catalog_date": data.get("catalog_date", date.today().isoformat()) if isinstance(data, dict) else date.today().isoformat(),
                                        "items": items_list,
                                    }
                                    source_health_service.record_attempt(
                                        source_code=self.source_code,
                                        latency_ms=latency_ms,
                                        success=True,
                                        is_fallback=False,
                                    )
                                    return catalog_payload, False, latency_ms, None
                            except Exception as json_err:
                                last_error = f"JSONDecodeError: {json_err}"

                        # 2. HTML storefront fallback parsing
                        if "html" in content_type or "<html" in resp.text.lower():
                            html_items = self._parse_html_catalog(resp.text)
                            if html_items:
                                catalog_payload = {
                                    "market_name": "Chaldal Online Hub",
                                    "catalog_date": date.today().isoformat(),
                                    "items": html_items,
                                }
                                source_health_service.record_attempt(
                                    source_code=self.source_code,
                                    latency_ms=latency_ms,
                                    success=True,
                                    is_fallback=False,
                                )
                                return catalog_payload, False, latency_ms, None

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
        """Harvest observations from live feed, HTML storefront, or cached fixture."""
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
            if not self._is_in_stock(item):
                continue

            raw_name, raw_price, package_unit = self._extract_item_metrics(item)

            if raw_price <= 0.0 or not raw_name:
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
