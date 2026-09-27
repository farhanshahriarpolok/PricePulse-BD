"""
Abstract base collector and raw observation data contracts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List


@dataclass
class RawObservation:
    """Atomic observation extracted directly from an upstream source."""
    source_code: str
    market_name: str
    raw_commodity_name: str
    raw_unit: str
    raw_price: float
    price_type: str  # e.g., 'retail_avg', 'wholesale_avg', 'wholesale_min', 'wholesale_max'
    observation_date: date
    completeness_score: float = 1.0


class BaseCollector(ABC):
    """Abstract contract for market price harvest collectors."""

    source_code: str
    source_name: str
    source_type: str
    reliability_score: float

    @abstractmethod
    def collect(self) -> List[RawObservation]:
        """Harvest raw observations from the configured source."""
        pass
