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
        return self.db.scalars(stmt_sub).first()

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
                if existing_obs.raw_name != raw.raw_commodity_name:
                    # Multi-SKU package averaging for retail offerings (e.g., 1kg vs 2kg packs)
                    existing_obs.normalized_price = round(
                        (existing_obs.normalized_price + norm_price) / 2.0, 2
                    )
                    existing_obs.confidence_score = max(existing_obs.confidence_score, score)
                    updated_count += 1
                elif score >= existing_obs.confidence_score:
                    existing_obs.raw_name = raw.raw_commodity_name
                    existing_obs.raw_price = raw.raw_price
                    existing_obs.raw_unit = raw.raw_unit
                    existing_obs.normalized_price = norm_price
                    existing_obs.normalized_unit = norm_unit
                    existing_obs.confidence_score = score
                    updated_count += 1
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

        self.db.commit()

        return IngestionReport(
            source_code=collector.source_code,
            total_harvested=len(raw_items),
            inserted=inserted_count,
            updated=updated_count,
            skipped=skipped_count,
        )
