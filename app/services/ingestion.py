"""
Ingestion orchestrator: Harvest -> Normalize -> Deduplicate -> Score -> Persist.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.collectors.base import BaseCollector, RawObservation
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.source import Source
from app.models.observation import PriceObservation
from app.services.normalizer import CommodityNormalizer, commodity_normalizer
from app.services.confidence import ConfidenceScorer, confidence_scorer

logger = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    source_code: str
    total_harvested: int
    inserted: int
    updated: int
    skipped: int


class IngestionPipeline:
    """Orchestrates harvest, canonical normalization, deduplication, scoring, and persistence."""

    def __init__(
        self,
        db: Session,
        normalizer: Optional[CommodityNormalizer] = None,
        scorer: Optional[ConfidenceScorer] = None,
    ):
        self.db = db
        self.normalizer = normalizer or commodity_normalizer
        self.scorer = scorer or confidence_scorer

    def _get_or_create_source(self, collector: BaseCollector) -> Source:
        """Ensure source is registered in the database."""
        stmt = select(Source).where(Source.code == collector.source_code)
        source = self.db.scalars(stmt).first()
        if not source:
            source = Source(
                code=collector.source_code,
                name=collector.source_name,
                source_type=collector.source_type,
                reliability_score=collector.reliability_score,
            )
            self.db.add(source)
            self.db.flush()
        return source

    def _resolve_market(self, market_name: str) -> Optional[Market]:
        """Resolve raw market name to a database Market entity."""
        cleaned = market_name.strip()
        # Direct match
        stmt = select(Market).where(func.lower(Market.name) == cleaned.lower())
        market = self.db.scalars(stmt).first()
        if market:
            return market

        # Substring match
        stmt_sub = select(Market).where(Market.name.ilike(f"%{cleaned}%"))
        res = self.db.scalars(stmt_sub).first()
        if res:
            return res

        # Canonical aliases for national / Dhaka benchmarks (including online / superstore retail hubs)
        cleaned_lower = cleaned.lower()
        if any(k in cleaned_lower for k in [
            "dhaka", "benchmark", "karwan", "কাওরান", "কারওয়ান", "tcb",
            "national", "press", "prothom", "jugantor",
            "shwapno", "meena", "pandamart", "chaldal", "darkstore", "retail hub"
        ]):
            stmt_karwan = select(Market).where(Market.name == "Karwan Bazar")
            return self.db.scalars(stmt_karwan).first()

        # Unknown markets must return None so they are quarantined/skipped,
        # never arbitrarily mapped to the first row in the database.
        return None

    def _resolve_commodity_entity(self, canonical_name: str) -> Optional[Commodity]:
        """Retrieve canonical Commodity model from database."""
        stmt = select(Commodity).where(Commodity.canonical_name == canonical_name)
        return self.db.scalars(stmt).first()

    def run_collector(self, collector: BaseCollector) -> IngestionReport:
        """Execute full ingestion cycle for a collector."""
        raw_items = collector.collect()
        source = self._get_or_create_source(collector)

        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        affected_commodities: set[int] = set()

        try:
            for raw in raw_items:
                # 1. Resolve market
                market = self._resolve_market(raw.market_name)
                if not market:
                    logger.warning(f"Unresolved market: '{raw.market_name}' - skipping record.")
                    skipped_count += 1
                    continue

                # 2. Resolve commodity
                match = self.normalizer.resolve_commodity(raw.raw_commodity_name)
                if not match:
                    logger.warning(
                        f"Unresolved commodity: '{raw.raw_commodity_name}' - skipping record."
                    )
                    skipped_count += 1
                    continue

                commodity = self._resolve_commodity_entity(match.canonical_name)
                if not commodity:
                    logger.warning(
                        f"Canonical commodity '{match.canonical_name}' not seeded in DB - skipping."
                    )
                    skipped_count += 1
                    continue

                # 3. Unit & price normalization
                try:
                    norm_price, norm_unit = self.normalizer.normalize_price(raw.raw_price, raw.raw_unit)
                except ValueError as ve:
                    logger.warning(f"Unit normalization error ({ve}) - skipping record.")
                    skipped_count += 1
                    continue

                # 4. Confidence scoring
                score = self.scorer.compute(
                    source_reliability=source.reliability_score,
                    alias_weight=match.match_weight,
                    observation_date=raw.observation_date,
                    completeness_score=raw.completeness_score,
                )

                # 5. Deduplication & Upsert
                existing_stmt = select(PriceObservation).where(
                    PriceObservation.commodity_id == commodity.id,
                    PriceObservation.market_id == market.id,
                    PriceObservation.source_id == source.id,
                    PriceObservation.observation_date == raw.observation_date,
                    PriceObservation.price_type == raw.price_type,
                )
                existing_obs = self.db.scalars(existing_stmt).first()

                if existing_obs:
                    if raw.is_fallback:
                        # Fallback fixture data must not alter existing historical records
                        skipped_count += 1
                        continue

                    # Idempotent, order-independent duplicate resolution:
                    # Prefer higher confidence score; break ties deterministically by selecting the lower normalized price.
                    if score > existing_obs.confidence_score:
                        existing_obs.raw_name = raw.raw_commodity_name
                        existing_obs.raw_price = raw.raw_price
                        existing_obs.raw_unit = raw.raw_unit
                        existing_obs.normalized_price = norm_price
                        existing_obs.normalized_unit = norm_unit
                        existing_obs.confidence_score = score
                        updated_count += 1
                        affected_commodities.add(commodity.id)
                    elif score == existing_obs.confidence_score and existing_obs.raw_name != raw.raw_commodity_name:
                        if norm_price < existing_obs.normalized_price:
                            existing_obs.raw_name = raw.raw_commodity_name
                            existing_obs.raw_price = raw.raw_price
                            existing_obs.raw_unit = raw.raw_unit
                            existing_obs.normalized_price = norm_price
                            existing_obs.normalized_unit = norm_unit
                            updated_count += 1
                            affected_commodities.add(commodity.id)
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                else:
                    new_obs = PriceObservation(
                        commodity_id=commodity.id,
                        market_id=market.id,
                        source_id=source.id,
                        raw_name=raw.raw_commodity_name,
                        raw_price=raw.raw_price,
                        raw_unit=raw.raw_unit,
                        normalized_price=norm_price,
                        normalized_unit=norm_unit,
                        price_type=raw.price_type,
                        observation_date=raw.observation_date,
                        confidence_score=score,
                    )
                    self.db.add(new_obs)
                    self.db.flush()
                    inserted_count += 1
                    affected_commodities.add(commodity.id)

            self.db.commit()

            # Invalidate downstream analytical caches for updated commodities
            if affected_commodities:
                from app.services.forecast_service import forecast_service
                from app.services.spatial_service import spatial_service
                for cid in affected_commodities:
                    forecast_service.invalidate(commodity_id=cid)
                    spatial_service.invalidate(commodity_id=cid)
        except Exception as exc:
            self.db.rollback()
            logger.error(f"Ingestion transaction failed for {collector.source_code}: {exc}")
            raise

        return IngestionReport(
            source_code=collector.source_code,
            total_harvested=len(raw_items),
            inserted=inserted_count,
            updated=updated_count,
            skipped=skipped_count,
        )


def ingest_observations(
    db: Session,
    raw_items: list[RawObservation],
    collector: Optional[BaseCollector] = None,
) -> tuple[int, int]:
    """
    Convenience helper function to ingest raw observations directly into SQLite.
    Returns (inserted_count, updated_count).
    """
    if not raw_items:
        return 0, 0

    pipeline = IngestionPipeline(db)
    if collector:
        source = pipeline._get_or_create_source(collector)
    else:
        src_code = raw_items[0].source_code
        stmt = select(Source).where(Source.code == src_code)
        source = db.scalars(stmt).first()
        if not source:
            source = Source(
                code=src_code,
                name=src_code.replace("_", " ").title(),
                source_type="market_report",
                reliability_score=0.85,
            )
            db.add(source)
            db.flush()

    inserted_count = 0
    updated_count = 0
    affected_commodities: set[int] = set()

    for raw in raw_items:
        market = pipeline._resolve_market(raw.market_name)
        if not market:
            continue

        match = pipeline.normalizer.resolve_commodity(raw.raw_commodity_name)
        if not match:
            continue

        commodity = pipeline._resolve_commodity_entity(match.canonical_name)
        if not commodity:
            continue

        try:
            norm_price, norm_unit = pipeline.normalizer.normalize_price(raw.raw_price, raw.raw_unit)
        except ValueError:
            continue

        score = pipeline.scorer.compute(
            source_reliability=source.reliability_score,
            alias_weight=match.match_weight,
            observation_date=raw.observation_date,
            completeness_score=raw.completeness_score,
        )

        existing_stmt = select(PriceObservation).where(
            PriceObservation.commodity_id == commodity.id,
            PriceObservation.market_id == market.id,
            PriceObservation.source_id == source.id,
            PriceObservation.observation_date == raw.observation_date,
            PriceObservation.price_type == raw.price_type,
        )
        existing_obs = db.scalars(existing_stmt).first()

        if existing_obs:
            if raw.is_fallback:
                continue
            if existing_obs.raw_name != raw.raw_commodity_name:
                existing_obs.normalized_price = round(
                    (existing_obs.normalized_price + norm_price) / 2.0, 2
                )
                existing_obs.confidence_score = max(existing_obs.confidence_score, score)
                updated_count += 1
                affected_commodities.add(commodity.id)
            elif score >= existing_obs.confidence_score:
                existing_obs.raw_name = raw.raw_commodity_name
                existing_obs.raw_price = raw.raw_price
                existing_obs.raw_unit = raw.raw_unit
                existing_obs.normalized_price = norm_price
                existing_obs.normalized_unit = norm_unit
                existing_obs.confidence_score = score
                updated_count += 1
                affected_commodities.add(commodity.id)
        else:
            new_obs = PriceObservation(
                commodity_id=commodity.id,
                market_id=market.id,
                source_id=source.id,
                raw_name=raw.raw_commodity_name,
                raw_price=raw.raw_price,
                raw_unit=raw.raw_unit,
                normalized_price=norm_price,
                normalized_unit=norm_unit,
                price_type=raw.price_type,
                observation_date=raw.observation_date,
                confidence_score=score,
            )
            db.add(new_obs)
            db.flush()
            inserted_count += 1
            affected_commodities.add(commodity.id)

    db.commit()

    if affected_commodities:
        from app.services.forecast_service import forecast_service
        from app.services.spatial_service import spatial_service
        for cid in affected_commodities:
            forecast_service.invalidate(commodity_id=cid)
            spatial_service.invalidate(commodity_id=cid)

    return inserted_count, updated_count

