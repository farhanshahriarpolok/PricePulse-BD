"""
Real-data collector for Meena Bazar Online supermarket catalog.
Fetches real product prices from public storefront API,
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


# Explicit mapping from Meena Bazar product display/description name to canonical commodity name.
# Strictly explicit - NO regex guessing or .includes() heuristic.
EXPLICIT_COMMODITY_MAPPINGS: Dict[str, str] = {
    # Meat & Poultry
    "Beef Bone-In Premium": "Beef (Local with Bone)",
    "Broiler Chicken Without Skin": "Broiler Chicken",
    "Mutton Regular": "Mutton (Goat Meat)",
    # Grains, Rice, Atta & Dal
    "Najir Rice (Premium)": "Rice (Nazirshail)",
    "Minicate Rice (Premium)": "Rice (Miniket)",
    "Farmland Atta 2kg": "Atta (Packaged)",
    "Khesari (Grass Pea) Local Bulk": "Khesari Dal",
    # Produce & Vegetables
    "Onion Local Bulk Regular": "Onion (Local)",
    "Potato Bulk White Regular": "Potato (Diamond)",
    "Green Chili Local": "Green Chilli",
    "Shosha [cucumber]": "Cucumber",
    "Cauliflower (ফুলকপি) Pcs": "Cauliflower",
    "Cabbage [badacopi] Local Pcs": "Cabbage",
    "Lomba Kalo Begun (Long Brinjal Black)": "Brinjal (Eggplant)",
    "Lemon Local Pcs": "Lemon",
    # Eggs & Dairy
    "Farm Fresh Paragon Omega3+ Egg 12pcs": "Farm Egg",
    # Oils, Sugar & Staples
    "Rupchanda Soyabean Oil Pet 5ltr": "Soybean Oil (Bottled)",
    "White Sugar": "Sugar (Refined White)",
    # Fish
    "Rupchanda Fish 150gm+": "Pomfret (Rupchanda)",
    "Pangas Fish Pond (1.5-2.999) Kg/Pc": "Pangas Fish (Farm)",
    "Hilsha Fish 700 Gm+": "Hilsa Fish (Medium)",
}


class MeenaBazarCollector(BaseCollector):
    """Collector for Meena Bazar Online supermarket public catalog API."""

    source_code = "MEENA_BAZAR_RETAIL"
    source_name = "Meena Bazar Online"
    source_type = "retail_superstore"
    reliability_score = 0.89
    default_collection_status = CollectionStatus.LIVE

    DEFAULT_USER_AGENT = "PricePulse-BD/1.0 (National Commodity Market Intelligence; +https://pricepulse.bd)"
    BASE_API_URL = "https://mbonlineapi.com/api/front/home/section"

    def __init__(
        self,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
        max_retries: int = 2,
        timeout_seconds: float = 4.0,
        enable_network: bool = True,
    ):
        self.fixture_path = fixture_path or (settings.fixtures_dir / "meena_bazar_catalog_sample.json")
        self.target_date = target_date
        self.max_retries = max_retries
        self.timeout = timeout_seconds
        self.enable_network = enable_network

    def _extract_item(self, item: Dict[str, Any]) -> Optional[Tuple[str, float, str, Optional[str]]]:
        """
        Extract canonical mapped commodity, price, unit, and raw name.
        Returns: (canonical_name, price, package_unit, raw_name) or None if not supported/available.
        """
        raw_name = str(item.get("ItemDisplayName") or item.get("ItemDescription") or "").strip()
        if not raw_name:
            return None

        # Check stock availability
        stock = item.get("StockQuantity")
        if stock is not None:
            try:
                if float(stock) <= 0:
                    return None
            except (ValueError, TypeError):
                pass

        # Check explicit canonical mapping
        canonical_name = EXPLICIT_COMMODITY_MAPPINGS.get(raw_name)
        if not canonical_name:
            return None

        # Price extraction: DiscountSalesPrice if valid, else UnitSalesPrice
        raw_price = 0.0
        disc_price = item.get("DiscountSalesPrice")
        reg_price = item.get("UnitSalesPrice")
        for p in (disc_price, reg_price):
            if p is not None:
                try:
                    val = float(p)
                    if val > 0:
                        raw_price = val
                        break
                except (ValueError, TypeError):
                    continue

        if raw_price <= 0.0:
            return None

        # Unit resolution
        unit_str = str(item.get("Unit") or "").strip().lower()

        # Handle eggs pack of 12
        if "12pcs" in raw_name.lower() or "12 pcs" in raw_name.lower():
            package_unit = "12 pcs"
        # Check name for embedded volume/weight (e.g. 5ltr, 2kg, 1.5kg, 500g)
        elif re.search(r"\b(\d+(?:\.\d+)?\s*(?:ltr|liter|litre|kg|gm|g))\b", raw_name, re.IGNORECASE):
            m = re.search(r"\b(\d+(?:\.\d+)?\s*(?:ltr|liter|litre|kg|gm|g))\b", raw_name, re.IGNORECASE)
            package_unit = m.group(1).strip()
        elif unit_str in ("kg", "1 kg"):
            package_unit = "1 kg"
        elif unit_str in ("500g", "500 gm", "500 gram"):
            package_unit = "500 gm"
        elif unit_str in ("250g", "250 gm"):
            package_unit = "250 gm"
        elif unit_str in ("100g", "100 gm"):
            package_unit = "100 gm"
        elif unit_str in ("each", "pcs", "piece"):
            package_unit = "1 pc"
        elif unit_str in ("1.5kg", "1.5 kg"):
            package_unit = "1.5 kg"
        else:
            package_unit = "1 kg"

        return canonical_name, raw_price, package_unit, raw_name

    def _fetch_live(self) -> Tuple[List[Dict[str, Any]], bool, float, Optional[str]]:
        """
        Attempt live network fetch from Meena Bazar home section API.
        Returns: (items, is_fallback, latency_ms, error_message)
        """
        if not self.enable_network:
            return [], True, 0.0, "Network disabled by configuration"

        start_time = time.perf_counter()
        headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
        }
        params = {
            "SubUnitId": "2",
            "AreaId": "null",
            "ThumbSizeAdd": "4xl",
            "ThumbSize": "tmd",
            "ProductThumbSize": "lg",
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
                    resp = client.get(self.BASE_API_URL, params=params)
                    latency_ms = (time.perf_counter() - start_time) * 1000.0

                    if resp.status_code in (200, 201):
                        data = resp.json()
                        products = data.get("data", {}).get("homeProductSection", [])
                        if products:
                            source_health_service.record_attempt(
                                source_code=self.source_code,
                                latency_ms=latency_ms,
                                success=True,
                                is_fallback=False,
                            )
                            return products, False, latency_ms, None
                    last_error = f"HTTP {resp.status_code}"
            except Exception as e:
                last_error = f"{e.__class__.__name__}: {e}"
                time.sleep(0.1 * (2 ** attempt))

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return [], True, latency_ms, last_error or "No products fetched"

    def _load_fixture(self) -> List[Dict[str, Any]]:
        """Load fallback products from verified local fixture."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Meena Bazar fixture not found at {self.fixture_path}")
        with open(self.fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("products", [])

    def collect(self) -> List[RawObservation]:
        """Harvest raw observations from live Meena Bazar catalog or cached fixture."""
        items, is_fallback, latency_ms, error_msg = self._fetch_live()

        if is_fallback or not items:
            logger.warning(f"Meena Bazar collector falling back to fixture: {error_msg}")
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
        market_name = "Meena Bazar Hub"
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
                    source_url="https://meenabazaronline.com",
                    raw_package_size=package_unit,
                    error_message=error_msg if is_fallback else None,
                )
            )

        return observations
