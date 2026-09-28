"""
Realtime price service managing on-demand ingestion fallback, caching, and freshness markers.
"""

import math
from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.models.commodity import Commodity
from app.models.observation import PriceObservation
from app.collectors.dam_fixture_collector import DAMFixtureCollector
from app.collectors.chaldal_collector import ChaldalCollector
from app.services.normalizer import CommodityNormalizer, commodity_normalizer
from app.services.analytics import AnalyticsService, analytics_service
from app.services.ingestion import IngestionPipeline
from app.schemas.common import FreshnessMetadata
from app.schemas.observation import (
    PriceObservationOut,
    PriceSummaryOut,
    ChannelComparisonOut,
)
from app.schemas.search import (
    RealtimePriceResponse,
    DailyPulseItem,
    DailyPulseResponse,
)


class RealtimePriceService:
    """Provides on-demand commodity price discovery with dynamic collector fallback."""

    def __init__(
        self,
        db: Session,
        normalizer: Optional[CommodityNormalizer] = None,
        analytics: Optional[AnalyticsService] = None,
    ):
        self.db = db
        self.normalizer = normalizer or commodity_normalizer
        self.analytics = analytics or analytics_service

    def resolve_commodity(self, query: str) -> Optional[Commodity]:
        """Resolve user search string to a canonical database Commodity."""
        cleaned = query.strip()
        match = self.normalizer.resolve_commodity(cleaned)
        if match:
            stmt = select(Commodity).where(Commodity.canonical_name == match.canonical_name)
            comm = self.db.scalars(stmt).first()
            if comm:
                return comm

        # Fallback to direct DB search
        stmt_db = select(Commodity).where(
            (Commodity.canonical_name.ilike(f"%{cleaned}%"))
            | (Commodity.bangla_name.ilike(f"%{cleaned}%"))
        )
        return self.db.scalars(stmt_db).first()

    def _trigger_on_demand_harvest(self, target_date: date) -> None:
        """Execute on-demand collector suite to refresh observations."""
        pipeline = IngestionPipeline(db=self.db, normalizer=self.normalizer)
        dam_collector = DAMFixtureCollector(target_date=target_date)
        chaldal_collector = ChaldalCollector(target_date=target_date)

        pipeline.run_collector(dam_collector)
        pipeline.run_collector(chaldal_collector)

    def _query_observations(self, commodity_id: int, obs_date: date) -> List[PriceObservation]:
        """Fetch all observations for a commodity on a given date."""
        stmt = (
            select(PriceObservation)
            .where(
                PriceObservation.commodity_id == commodity_id,
                PriceObservation.observation_date == obs_date,
            )
            .order_by(desc(PriceObservation.confidence_score))
        )
        return list(self.db.scalars(stmt).all())

    def get_realtime_price(
        self,
        query: str,
        target_date: Optional[date] = None,
    ) -> Optional[RealtimePriceResponse]:
        """
        Query price pulse for a commodity. Triggers automated harvest if data is absent or stale.
        """
        commodity = self.resolve_commodity(query)
        if not commodity:
            return None

        eff_date = target_date or date.today()
        observations = self._query_observations(commodity.id, eff_date)

        freshness_status = "fresh"
        is_stale = False
        cache_age = 0
        latest_scraped: Optional[datetime] = None

        # Check if observations need on-demand ingestion
        needs_harvest = False
        if not observations:
            needs_harvest = True
        elif eff_date == date.today():
            latest_obs = max(observations, key=lambda o: o.scraped_at or datetime.min)
            if latest_obs.scraped_at:
                latest_scraped = latest_obs.scraped_at
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                age_seconds = (now_utc - latest_obs.scraped_at).total_seconds()
                cache_age = int(age_seconds)
                # If cached observations are older than 12 hours, refresh
                if age_seconds > (12 * 3600):
                    needs_harvest = True
                    is_stale = True

        if needs_harvest:
            self._trigger_on_demand_harvest(eff_date)
            observations = self._query_observations(commodity.id, eff_date)
            freshness_status = "realtime_ingested"
            is_stale = False
            latest_scraped = datetime.now(timezone.utc).replace(tzinfo=None)
            cache_age = 0
        else:
            if eff_date < date.today():
                freshness_status = "historical"
            elif is_stale:
                freshness_status = "stale"
            else:
                freshness_status = "fresh"

        # Compute aggregate price metrics and channel breakdown
        analytics_result = self.analytics.compute_analytics(observations)

        # Build schema observations
        obs_schemas = [
            PriceObservationOut(
                id=o.id,
                commodity_name=commodity.canonical_name,
                market_name=o.market.name if o.market else "Unknown Market",
                market_type=o.market.market_type if o.market else "retail",
                source_name=o.source.name if o.source else "Unknown Source",
                price_type=o.price_type,
                raw_price=o.raw_price,
                raw_unit=o.raw_unit,
                normalized_price=o.normalized_price,
                normalized_unit=o.normalized_unit,
                currency="BDT",
                confidence_score=o.confidence_score,
                observation_date=o.observation_date,
                scraped_at=o.scraped_at,
            )
            for o in observations
        ]

        summary_out = PriceSummaryOut(
            min_price=analytics_result.summary.min_price,
            max_price=analytics_result.summary.max_price,
            avg_price=analytics_result.summary.avg_price,
            currency="BDT",
            sample_count=analytics_result.summary.sample_count,
        )

        channels_out = ChannelComparisonOut(
            wholesale_avg=analytics_result.channels.wholesale_avg,
            retail_avg=analytics_result.channels.retail_avg,
            online_avg=analytics_result.channels.online_avg,
            spread_bdt=analytics_result.channels.spread_bdt,
            markup_percentage=analytics_result.channels.markup_percentage,
        )

        freshness_out = FreshnessMetadata(
            status=freshness_status,
            last_scraped_at=latest_scraped,
            is_stale=is_stale,
            cache_age_seconds=cache_age,
        )

        return RealtimePriceResponse(
            query=query,
            canonical_name=commodity.canonical_name,
            bangla_name=commodity.bangla_name,
            category=commodity.category,
            unit=commodity.default_unit,
            observation_date=eff_date,
            price_summary=summary_out,
            channels=channels_out,
            price_status=analytics_result.price_status,
            freshness=freshness_out,
            observations=obs_schemas,
        )

    def get_today_pulse(self) -> DailyPulseResponse:
        """Generate overall market intelligence pulse for essential commodities with 7d sparklines and channel metrics."""
        today = date.today()
        # Ensure latest data is loaded
        commodities = list(self.db.scalars(select(Commodity).order_by(Commodity.id)).all())
        
        # Check if today has data; if not, trigger harvest once for all
        obs_count = self.db.scalar(
            select(func.count(PriceObservation.id)).where(PriceObservation.observation_date == today)
        )
        if obs_count == 0:
            self._trigger_on_demand_harvest(today)

        # Efficiently fetch up to 14 days of historical daily average prices in a single query
        start_14d = today - timedelta(days=14)
        hist_stmt = (
            select(
                PriceObservation.commodity_id,
                PriceObservation.observation_date,
                func.avg(PriceObservation.normalized_price).label("daily_avg"),
            )
            .where(
                PriceObservation.observation_date >= start_14d,
                PriceObservation.observation_date <= today,
            )
            .group_by(PriceObservation.commodity_id, PriceObservation.observation_date)
            .order_by(PriceObservation.commodity_id, PriceObservation.observation_date.asc())
        )
        hist_rows = self.db.execute(hist_stmt).all()
        daily_history_by_comm = defaultdict(list)
        for r in hist_rows:
            daily_history_by_comm[r.commodity_id].append(round(float(r.daily_avg), 2))

        items: List[DailyPulseItem] = []
        for comm in commodities:
            observations = self._query_observations(comm.id, today)
            if not observations:
                continue

            analytics_result = self.analytics.compute_analytics(observations)
            latest_scraped = max((o.scraped_at for o in observations if o.scraped_at), default=None)

            # Sparkline and delta calculation
            hist_series = daily_history_by_comm[comm.id]
            sparkline_7d = hist_series[-7:] if len(hist_series) >= 7 else hist_series
            if not sparkline_7d:
                sparkline_7d = [analytics_result.summary.avg_price]

            if len(sparkline_7d) >= 2 and sparkline_7d[0] > 0:
                pct_change_7d = round(((sparkline_7d[-1] - sparkline_7d[0]) / sparkline_7d[0]) * 100.0, 2)
            else:
                pct_change_7d = 0.0

            # Source count and confidence
            unique_sources = {o.source_id for o in observations if o.source_id}
            source_count = len(unique_sources) if unique_sources else 1
            conf_list = [o.confidence_score for o in observations if o.confidence_score is not None]
            avg_confidence = round(sum(conf_list) / len(conf_list), 2) if conf_list else 0.90

            # Volatility CV% and Z-score
            if len(hist_series) >= 3:
                m_14 = sum(hist_series) / len(hist_series)
                var_14 = sum((x - m_14) ** 2 for x in hist_series) / (len(hist_series) - 1)
                std_14 = math.sqrt(var_14)
                vol_cv = round((std_14 / m_14) * 100.0, 2) if m_14 > 0 else 0.0

                if len(hist_series[:-1]) >= 2:
                    base_pts = hist_series[:-1]
                    b_mean = sum(base_pts) / len(base_pts)
                    b_var = sum((x - b_mean) ** 2 for x in base_pts) / (len(base_pts) - 1)
                    b_std = math.sqrt(b_var)
                    z_val = round((hist_series[-1] - b_mean) / b_std, 2) if b_std > 1e-5 else 0.0
                else:
                    z_val = 0.0
            else:
                vol_cv = 0.0
                z_val = 0.0

            items.append(
                DailyPulseItem(
                    commodity_id=comm.id,
                    canonical_name=comm.canonical_name,
                    bangla_name=comm.bangla_name,
                    category=comm.category,
                    unit=comm.default_unit,
                    price_summary=PriceSummaryOut(
                        min_price=analytics_result.summary.min_price,
                        max_price=analytics_result.summary.max_price,
                        avg_price=analytics_result.summary.avg_price,
                        currency="BDT",
                        sample_count=analytics_result.summary.sample_count,
                    ),
                    channels=ChannelComparisonOut(
                        wholesale_avg=analytics_result.channels.wholesale_avg,
                        retail_avg=analytics_result.channels.retail_avg,
                        online_avg=analytics_result.channels.online_avg,
                        spread_bdt=analytics_result.channels.spread_bdt,
                        markup_percentage=analytics_result.channels.markup_percentage,
                    ),
                    price_status=analytics_result.price_status,
                    freshness=FreshnessMetadata(
                        status="fresh",
                        last_scraped_at=latest_scraped,
                        is_stale=False,
                        cache_age_seconds=0,
                    ),
                    sparkline_7d=sparkline_7d,
                    percentage_change_7d=pct_change_7d,
                    min_price=analytics_result.summary.min_price,
                    max_price=analytics_result.summary.max_price,
                    wholesale_avg=analytics_result.channels.wholesale_avg,
                    retail_avg=analytics_result.channels.retail_avg,
                    online_avg=analytics_result.channels.online_avg,
                    source_count=source_count,
                    confidence_score=avg_confidence,
                    volatility_cv=vol_cv,
                    z_score=z_val,
                )
            )

        return DailyPulseResponse(
            date=today,
            total_tracked=len(items),
            items=items,
        )
