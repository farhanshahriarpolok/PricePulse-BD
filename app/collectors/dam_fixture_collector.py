"""
Deterministic HTML parser for Department of Agricultural Marketing (DAM) bulletin fixtures.
"""

from datetime import date, datetime
from pathlib import Path
from typing import List, Optional
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector, RawObservation
from app.core.config import settings


class DAMFixtureCollector(BaseCollector):
    """Parses official DAM daily market bulletin HTML fixtures."""

    source_code = "DAM_DAILY"
    source_name = "Department of Agricultural Marketing"
    source_type = "government"
    reliability_score = 0.95

    def __init__(self, fixture_path: Optional[Path] = None, target_date: Optional[date] = None):
        self.fixture_path = fixture_path or (settings.fixtures_dir / "dam_bulletin_sample.html")
        self.target_date = target_date

    def collect(self) -> List[RawObservation]:
        """Parse HTML fixture and yield raw observations for all markets and commodities."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"DAM fixture not found at {self.fixture_path}")

        with open(self.fixture_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Extract bulletin date or use target_date if specified
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

        # Find all market sections
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

                # Extract price columns
                price_mappings = [
                    ("price-retail-avg", "retail_avg"),
                    ("price-wholesale-avg", "wholesale_avg"),
                    ("price-wholesale-min", "wholesale_min"),
                    ("price-wholesale-max", "wholesale_max"),
                ]

                for css_class, price_type in price_mappings:
                    price_cell = row.find(class_=css_class)
                    if not price_cell:
                        continue

                    val_str = price_cell.get_text(strip=True)
                    try:
                        price_val = float(val_str)
                    except ValueError:
                        continue

                    # High completeness score since this bulletin provides market, unit, and date
                    observations.append(
                        RawObservation(
                            source_code=self.source_code,
                            market_name=market_name,
                            raw_commodity_name=raw_comm,
                            raw_unit=raw_unit,
                            raw_price=price_val,
                            price_type=price_type,
                            observation_date=obs_date,
                            completeness_score=1.0,
                        )
                    )

        return observations
