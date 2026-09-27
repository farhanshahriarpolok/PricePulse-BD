"""
Market analytics engine calculating price spreads, ranges, and status indicators.
"""

from dataclasses import dataclass
from typing import List, Optional
from app.models.observation import PriceObservation


@dataclass
class PriceRangeMetrics:
    min_price: float
    max_price: float
    avg_price: float
    sample_count: int
    currency: str = "BDT"


@dataclass
class ChannelSpreadMetrics:
    wholesale_avg: Optional[float]
    retail_avg: Optional[float]
    online_avg: Optional[float]
    spread_bdt: Optional[float]
    markup_percentage: Optional[float]


@dataclass
class MarketAnalyticsResult:
    summary: PriceRangeMetrics
    channels: ChannelSpreadMetrics
    price_status: str  # "Normal", "Elevated", "High"


class AnalyticsService:
    """Computes price statistics, channel markups, and price pressure classifications."""

    def compute_analytics(self, observations: List[PriceObservation]) -> MarketAnalyticsResult:
        if not observations:
            return MarketAnalyticsResult(
                summary=PriceRangeMetrics(0.0, 0.0, 0.0, 0),
                channels=ChannelSpreadMetrics(None, None, None, None, None),
                price_status="Normal",
            )

        prices = [obs.normalized_price for obs in observations]
        min_p = round(min(prices), 2)
        max_p = round(max(prices), 2)
        avg_p = round(sum(prices) / len(prices), 2)

        # Categorize by channel
        wholesale_prices: List[float] = []
        retail_prices: List[float] = []
        online_prices: List[float] = []

        for obs in observations:
            source_type = getattr(obs.source, "source_type", "") if obs.source else ""
            source_code = getattr(obs.source, "code", "") if obs.source else ""
            market_type = getattr(obs.market, "market_type", "") if obs.market else ""

            if source_code == "CHALDAL_RETAIL" or source_type == "retail_ecommerce" or market_type == "online":
                online_prices.append(obs.normalized_price)
            elif "wholesale" in obs.price_type:
                wholesale_prices.append(obs.normalized_price)
            else:
                retail_prices.append(obs.normalized_price)

        wholesale_avg = (
            round(sum(wholesale_prices) / len(wholesale_prices), 2) if wholesale_prices else None
        )
        retail_avg = (
            round(sum(retail_prices) / len(retail_prices), 2) if retail_prices else None
        )
        online_avg = (
            round(sum(online_prices) / len(online_prices), 2) if online_prices else None
        )

        # Calculate spread between retail and wholesale
        spread_bdt = None
        markup_pct = None
        benchmark_retail = retail_avg or online_avg

        if benchmark_retail is not None and wholesale_avg is not None and wholesale_avg > 0:
            spread_bdt = round(benchmark_retail - wholesale_avg, 2)
            markup_pct = round((spread_bdt / wholesale_avg) * 100, 2)

        # Determine price status indicator
        price_status = self._evaluate_price_status(markup_pct, min_p, max_p, avg_p)

        return MarketAnalyticsResult(
            summary=PriceRangeMetrics(
                min_price=min_p,
                max_price=max_p,
                avg_price=avg_p,
                sample_count=len(observations),
            ),
            channels=ChannelSpreadMetrics(
                wholesale_avg=wholesale_avg,
                retail_avg=retail_avg,
                online_avg=online_avg,
                spread_bdt=spread_bdt,
                markup_percentage=markup_pct,
            ),
            price_status=price_status,
        )

    def _evaluate_price_status(
        self,
        markup_pct: Optional[float],
        min_p: float,
        max_p: float,
        avg_p: float,
    ) -> str:
        """Classify market condition as Normal, Elevated, or High."""
        if markup_pct is not None:
            if markup_pct > 35.0:
                return "High"
            if markup_pct > 20.0:
                return "Elevated"
            return "Normal"

        # Fallback to dispersion spread if only one tier is available
        if avg_p > 0:
            dispersion = (max_p - min_p) / avg_p
            if dispersion > 0.35:
                return "High"
            if dispersion > 0.20:
                return "Elevated"

        return "Normal"


analytics_service = AnalyticsService()
