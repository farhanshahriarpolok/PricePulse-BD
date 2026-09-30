"""
Real-data collector for Shwapno Superstore retail grocery catalogs.
Fetches real product data from public Shwapno category endpoints,
maps to canonical commodities using explicit taxonomy mappings,
and falls back gracefully to verified local fixtures when offline.
"""

import json
import logging
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.collectors.base import BaseCollector, CollectionStatus, RawObservation
from app.core.config import settings
from app.services.source_health import source_health_service

logger = logging.getLogger(__name__)


# Explicit mapping from Shwapno product raw name to canonical commodity name.
# Strictly explicit - NO regex guessing or .includes() heuristic.
EXPLICIT_COMMODITY_MAPPINGS: Dict[str, str] = {
    # Vegetables & Produce
    "Fulcopy (Cauliflower)": "Cauliflower",
    "Badhakopi (Cabbage)": "Cabbage",
    "Kacha Morich (Chilli Green)": "Green Chilli",
    "Shosha (Cucumber)": "Cucumber",
    "Kacha Pepe (Green Papaya)": "Papaya (Green)",
    "Kacha Kola (Green Banana)": "Green Banana",
    "Potato Regular": "Potato (Diamond)",
    "Piyaj (Local Onion)": "Onion (Local)",
    "Tomato Local": "Tomato",
    "Carrot China (China Gajor) Kg": "Carrot",
    "Gajor (Carrot)": "Carrot",
    "Lau (Bottle Gourd)": "Bottle Gourd",
    "Lal Shak (Red Amaranth Spinach)": "Red Spinach",
    "Lomba Lebu (Lemon Long)": "Lemon",
    "Lebu Gol (Lemon Round)": "Lemon",
    "Begun Gol-Beguni (Brinjal Round)": "Brinjal (Eggplant)",
    "Begun Shobuj (Brinjal Round Green)": "Brinjal (Eggplant)",
    "Potol (Pointed Gourd)": "Pointed Gourd",
    "Dherosh (Lady Finger)": "Okra",
    # Eggs & Dairy
    "Egg Loose": "Farm Egg",
    "Deshi Dim (Layer/Farm)": "Farm Egg",
    "Paragon Brown Egg 12Pcs (12Pcs Pack)": "Farm Egg",
    "KaziFarms Kitchen Branded Egg (12Pcs Pack)": "Farm Egg",
    # Grains, Flour & Dal
    "ACI Pure Fortified Miniket Rice 5kg": "Rice (Miniket)",
    "ACI Pure Miniket (Jirashail) Rice 5kg": "Rice (Miniket)",
    "Rupchanda Miniket (Jirashail) Rice 5Kg": "Rice (Miniket)",
    "Miniket Rice Loose(P) (Jirashail) Kg": "Rice (Miniket)",
    "ACI Pure Fortified Nazirshail Rice 5kg": "Rice (Nazirshail)",
    "ACI Pure Najirshail Rice 5kg": "Rice (Nazirshail)",
    "Nazirshail Rice Loose (S) (Paijam) Kg": "Rice (Nazirshail)",
    "ACI Pure Chinigura Rice 1kg": "Chinigura Rice",
    "Fresh Chinigura Rice 1kg": "Chinigura Rice",
    "Teer Whole Wheat Atta 2kg": "Atta (Packaged)",
    "Fresh Whole Wheat Atta 2kg": "Atta (Packaged)",
    "Moshur Dal Local Loose": "Masur Dal (Medium)",
    # Oils & Spices
    "Rupchanda Fortified Soyabean Oil 5Ltr": "Soybean Oil (Bottled)",
    "Rupchanda Soyabean Oil 5Ltr.": "Soybean Oil (Bottled)",
    "Rupchanda Soyabean Oil 1Ltr.": "Soybean Oil (Bottled)",
    "Fresh Soyabean Oil 5Ltr.": "Soybean Oil (Bottled)",
    "Fresh Soyabean Oil 1Ltr.": "Soybean Oil (Bottled)",
    "Teer Soyabean Oil 5L": "Soybean Oil (Bottled)",
    "Teer Soyabean Oil 2Ltr.": "Soybean Oil (Bottled)",

    "ACI Pure Mustard Oil 1Ltr.": "Mustard Oil",
    "Radhuni Mustard Oil 1Ltr.": "Mustard Oil",
    "King's Sunflower Oil 5Ltr.": "Sunflower Oil",
    "ACI Pure Salt 1kg": "Salt (Iodized)",
    "Fresh Refined Sugar 1kg": "Sugar (Refined White)",
    "ACI Pure Coriander (Dhonia) Powder 100gm": "Coriander Powder",
    "ACI Pure Turmeric Powder 100gm": "Turmeric Powder",
}



class ShwapnoCollector(BaseCollector):
    """Collector for Shwapno Superstore public category API and storefront."""

    source_code = "SHWAPNO_RETAIL"
    source_name = "Shwapno Superstore"
    source_type = "retail_superstore"
    reliability_score = 0.90
    default_collection_status = CollectionStatus.LIVE

    DEFAULT_USER_AGENT = "PricePulse-BD/1.0 (National Commodity Market Intelligence; +https://pricepulse.bd)"
    BASE_API_URL = "https://www.shwapno.com/api/category/products"

    # Supported core category IDs on Shwapno
    CATEGORY_IDS = {
        "fresh-vegetables": "65ed45e2e429af37f903ae08",
        "rice": "65ed45e3e429af37f903ae15",
        "oil": "65ed45dfe429af37f903aded",
        "eggs": "65ed45e6e429af37f903ae3e",
    }

    def __init__(
        self,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        max_retries: int = 2,
        timeout_seconds: float = 4.0,
        enable_network: bool = True,
    ):
        self.fixture_path = fixture_path or (settings.fixtures_dir / "shwapno_catalog_sample.json")
        self.target_date = target_date
        self.max_retries = max_retries
        self.timeout = timeout_seconds
        self.enable_network = enable_network

    def _extract_item(self, item: Dict[str, Any]) -> Optional[Tuple[str, float, str, Optional[str]]]:
        """
        Extract canonical mapped commodity, price, unit, and raw name.
        Returns: (canonical_name, price, package_unit, raw_name) or None if not supported/available.
        """
        raw_name = str(item.get("name") or "").strip()
        if not raw_name:
            return None

        # Check stock availability
        stock = str(item.get("stock") or "").lower()
        if stock in ("outofstock", "soldout", "unavailable"):
            return None

        # Check explicit canonical mapping
        canonical_name = EXPLICIT_COMMODITY_MAPPINGS.get(raw_name)
        if not canonical_name:
            return None

        # Price extraction: prefer unitPriceValue or priceValue
        price_obj = item.get("price") or {}
        raw_price = 0.0
        if isinstance(price_obj, dict):
            raw_price = float(price_obj.get("priceValue") or 0.0)
            unit_price = float(price_obj.get("unitPriceValue") or 0.0)
        else:
            try:
                raw_price = float(price_obj)
                unit_price = 0.0
            except (ValueError, TypeError):
                unit_price = 0.0

        if raw_price <= 0.0:
            return None

        # Unit extraction
        unit_str = str(item.get("unit") or "").strip()

        # If package size is embedded in name (e.g., '5kg', '5Ltr', '2kg', '100gm')
        pkg_match = re.search(r"(\d+(?:\.\d+)?\s*(?:kg|ltr|liter|litre|gm|g|ml|pcs|pc))\b", raw_name, re.IGNORECASE)
        if pkg_match:
            package_unit = pkg_match.group(1).strip()
        elif unit_str:
            package_unit = unit_str
        else:
            package_unit = "1 kg"

        return canonical_name, raw_price, package_unit, raw_name

    def _fetch_live(self) -> Tuple[List[Dict[str, Any]], bool, float, Optional[str]]:
        """
        Attempt live network fetch across supported categories.
        Returns: (items, is_fallback, latency_ms, error_message)
        """
        if not self.enable_network:
            return [], True, 0.0, "Network disabled by configuration"

        start_time = time.perf_counter()
        headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
        }

        all_products = []
        last_error = None

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                for cat_slug, cat_id in self.CATEGORY_IDS.items():
                    url = f"{self.BASE_API_URL}?id={cat_id}"
                    for attempt in range(self.max_retries):
                        try:
                            resp = client.get(url)
                            if resp.status_code == 200:
                                data = resp.json()
                                products = data.get("products", [])
                                all_products.extend(products)
                                break
                            else:
                                last_error = f"HTTP {resp.status_code} for {cat_slug}"
                        except Exception as req_err:
                            last_error = f"{req_err.__class__.__name__}: {req_err}"
                            time.sleep(0.1 * (2 ** attempt))

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if all_products:
                source_health_service.record_attempt(
                    source_code=self.source_code,
                    latency_ms=latency_ms,
                    success=True,
                    is_fallback=False,
                )
                return all_products, False, latency_ms, None

        except Exception as e:
            last_error = f"NetworkException: {e}"

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return [], True, latency_ms, last_error or "No products fetched"

    def _load_fixture(self) -> List[Dict[str, Any]]:
        """Load fallback products from verified local fixture."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Shwapno fixture not found at {self.fixture_path}")
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products", [])

    def collect(self) -> List[RawObservation]:
        """Harvest raw observations from live Shwapno catalog or cached fixture."""
        items, is_fallback, latency_ms, error_msg = self._fetch_live()

        if is_fallback or not items:
            logger.warning(f"Shwapno collector falling back to fixture: {error_msg}")
            items = self._load_fixture()
            is_fallback = True
            source_health_service.record_attempt(
                source_code=self.source_code,
                latency_ms=latency_ms,
                success=True,
                is_fallback=True,
                error_message=f"Live harvest unavailable ({error_msg}); used cached benchmark.",
            )

        obs_date = self.target_date or date.today()
        market_name = "Shwapno Retail Hub"
        observations: List[RawObservation] = []
        seen_commodities = set()

        for it in items:
            extracted = self._extract_item(it)
            if not extracted:
                continue

            canonical_name, raw_price, package_unit, raw_name = extracted
            # Deduplicate by canonical commodity per collection cycle
            if canonical_name in seen_commodities:
                continue
            seen_commodities.add(canonical_name)

            observations.append(
                RawObservation(
                    source_code=self.source_code,
                    market_name=market_name,
                    raw_commodity_name=canonical_name,
                    raw_unit=package_unit,
                    raw_price=raw_price,
                    price_type="retail_avg",
                    observation_date=obs_date,
                    completeness_score=0.90 if is_fallback else 0.98,
                    is_fallback=is_fallback,
                    collection_status=CollectionStatus.FALLBACK.value if is_fallback else CollectionStatus.LIVE.value,
                    source_url="https://www.shwapno.com",
                    raw_package_size=package_unit,
                    error_message=error_msg if is_fallback else None,
                )
            )

        return observations
