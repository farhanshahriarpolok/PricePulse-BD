"""
Collector for parsing retail e-commerce grocery catalogs (Chaldal format).
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings


class ChaldalCollector(BaseCollector):
    """Parser for public grocery retail catalogs with varying packet sizes."""

    source_code = "CHALDAL_RETAIL"
    source_name = "Chaldal Online Grocery"
    source_type = "retail_ecommerce"
    reliability_score = 0.88

    def __init__(
        self,
        fixture_path: Optional[Path] = None,
        target_date: Optional[date] = None,
    ):
        self.fixture_path = fixture_path or (settings.fixtures_dir / "chaldal_catalog_sample.json")
        self.target_date = target_date

    def collect(self) -> List[RawObservation]:
        """Harvest raw grocery prices and packaging units."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Chaldal fixture not found at {self.fixture_path}")

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

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
                    completeness_score=0.95,
                )
            )

        return observations
