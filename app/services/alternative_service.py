"""
Smart Cheaper Alternative Recommendations Service — Phase 5B.

Provides mathematically auditable, empirical price alternative discovery:
  - Strictly intra-category (Rule A).
  - Explicit registry membership in alternative_registry.json (Rule B).
  - Empirical observations only (no imputed or synthetic modeled data).
  - Unit-normalized comparison.
  - Qualification threshold: absolute savings >= ৳2.00 AND percentage savings >= 5.0%.
  - Preserves Phase 5A freshness metadata and source provenance.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.services.freshness import evaluate_freshness, get_bangladesh_today
from app.services.normalizer import commodity_normalizer
from app.schemas.basket import PriceAlternativeOut

logger = logging.getLogger(__name__)

REGISTRY_PATH = settings.taxonomy_dir / "alternative_registry.json"


@dataclass
class AlternativeRegistryEntry:
    source_commodity_id: int
    source_canonical_name: str
    alternative_commodity_id: int
    alternative_canonical_name: str
    category: str
    reason_bn: str
    reason_en: str


class AlternativeRecommendationService:
    """Calculates and filters empirical smart cheaper substitute recommendations."""

    MIN_SAVINGS_BDT: float = 2.00
    MIN_SAVINGS_PCT: float = 5.00
    MAX_DATE_DIVERGENCE_DAYS: int = 1

    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or REGISTRY_PATH
        self._entries: list[AlternativeRegistryEntry] = []
        self._load_registry()

    def _load_registry(self) -> None:
        """Load and parse the alternative registry JSON."""
        if not self.registry_file.exists():
            logger.warning("Alternative registry not found at %s", self.registry_file)
            self._entries = []
            return

        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = [
                AlternativeRegistryEntry(
                    source_commodity_id=int(item["source_commodity_id"]),
                    source_canonical_name=str(item["source_canonical_name"]),
                    alternative_commodity_id=int(item["alternative_commodity_id"]),
                    alternative_canonical_name=str(item["alternative_canonical_name"]),
                    category=str(item["category"]),
                    reason_bn=str(item.get("reason_bn", "সাশ্রয়ী বিকল্প")),
                    reason_en=str(item.get("reason_en", "Economical alternative")),
                )
                for item in data.get("alternatives", [])
            ]
            logger.info("Loaded %d alternative rules from registry", len(self._entries))
        except Exception as exc:
            logger.error("Failed to load alternative registry: %s", exc)
            self._entries = []

    def get_candidate_entries(self, source_commodity_id: int) -> list[AlternativeRegistryEntry]:
        """Return all registered alternative candidates for a source commodity."""
        return [e for e in self._entries if e.source_commodity_id == source_commodity_id]

    def _fetch_latest_empirical_price(
        self,
        db: Session,
        commodity_id: int,
        target_date: date,
        channel: str = "retail",
    ) -> Optional[Tuple[float, str, date, Optional[object], str]]:
        """
        Fetch the most recent observed price for a commodity on the requested channel.
        Excludes modeled and synthetic benchmark sources.
        Returns: (normalized_price, normalized_unit, observation_date, scraped_at, provenance_status)
        """
        window_start = target_date - timedelta(days=14)

        stmt = (
            select(PriceObservation)
            .join(Source, PriceObservation.source_id == Source.id)
            .where(
                PriceObservation.commodity_id == commodity_id,
                PriceObservation.observation_date >= window_start,
                PriceObservation.observation_date <= target_date,
                PriceObservation.price_type.like(f"%{channel}%"),
                Source.code != "PANDAMART_MODELED",
                Source.source_type != "modeled_benchmark",
            )
            .order_by(
                desc(PriceObservation.observation_date),
                desc(PriceObservation.confidence_score),
                desc(PriceObservation.id),
            )
        )
        obs = db.scalars(stmt).first()
        if not obs or obs.normalized_price <= 0:
            return None

        source_code = obs.source.code if obs.source else "UNKNOWN"
        from app.services.source_health import source_health_service
        src_telemetry = source_health_service.get_source_status(source_code)
        if src_telemetry and not src_telemetry.get("is_fallback", True):
            provenance = "LIVE"
        else:
            provenance = "FALLBACK"

        return (
            float(obs.normalized_price),
            obs.normalized_unit or "kg",
            obs.observation_date,
            obs.scraped_at,
            provenance,
        )

    @staticmethod
    def _normalize_pair_units(
        price_src: float,
        unit_src: str,
        price_alt: float,
        unit_alt: str,
    ) -> Optional[Tuple[float, float, str]]:
        """
        Standardize both prices to an equivalent comparison unit.
        Returns (price_src_std, price_alt_std, standard_unit) or None if incompatible.
        """
        u_src = unit_src.strip().lower()
        u_alt = unit_alt.strip().lower()

        # Identical metric units
        if u_src == u_alt:
            return price_src, price_alt, unit_src

        # Egg normalization: hali (4 pcs) vs pc (1 pc)
        egg_hali = {"hali", "হালি"}
        egg_pc = {"pc", "pcs", "piece", "পিস", "টি", "টা"}

        if u_src in egg_hali and u_alt in egg_pc:
            # Source is in hali; convert alt (per piece) to per hali (× 4)
            return price_src, round(price_alt * 4.0, 2), "হালি"

        if u_src in egg_pc and u_alt in egg_hali:
            # Source is in pc; convert alt (per hali) to per piece (/ 4)
            return price_src, round(price_alt / 4.0, 2), "পিস"

        # General unit conversion via commodity_normalizer
        try:
            base_s, mult_s = commodity_normalizer.normalize_unit(unit_src)
            base_a, mult_a = commodity_normalizer.normalize_unit(unit_alt)
            if base_s == base_a and mult_s > 0 and mult_a > 0:
                p_s_norm = price_src / mult_s
                p_a_norm = price_alt / mult_a
                return round(p_s_norm, 2), round(p_a_norm, 2), base_s
        except ValueError:
            pass

        return None

    def evaluate_alternative(
        self,
        db: Session,
        entry: AlternativeRegistryEntry,
        target_date: Optional[date] = None,
        channel: str = "retail",
        basket_quantity: Optional[float] = None,
    ) -> Optional[PriceAlternativeOut]:
        """
        Evaluate a single candidate alternative rule against empirical market data.
        Returns PriceAlternativeOut if all criteria pass, else None.
        """
        eval_date = target_date or get_bangladesh_today()

        # 1. Verify existence of both commodities
        comm_src = db.get(Commodity, entry.source_commodity_id)
        comm_alt = db.get(Commodity, entry.alternative_commodity_id)
        if not comm_src or not comm_alt:
            return None

        # 2. Rule A: Strictly Intra-Category
        if comm_src.category != comm_alt.category:
            logger.debug(
                "Rejected cross-category alternative: %s (%s) vs %s (%s)",
                comm_src.canonical_name,
                comm_src.category,
                comm_alt.canonical_name,
                comm_alt.category,
            )
            return None

        # 3. Fetch empirical observed prices on the evaluated channel
        src_data = self._fetch_latest_empirical_price(
            db, comm_src.id, eval_date, channel=channel
        )
        alt_data = self._fetch_latest_empirical_price(
            db, comm_alt.id, eval_date, channel=channel
        )
        if not src_data or not alt_data:
            return None

        price_s_raw, unit_s_raw, date_s, scraped_s, prov_s = src_data
        price_a_raw, unit_a_raw, date_a, scraped_a, prov_a = alt_data

        # 4. Strict Temporal Alignment Rule:
        # Source and Alternative observations must not be more than 1 calendar day apart.
        # Comparisons with divergence > 1 day are strictly excluded.
        divergence_days = abs((date_s - date_a).days)
        if divergence_days > self.MAX_DATE_DIVERGENCE_DAYS:
            logger.debug(
                "Excluded alternative due to excessive temporal divergence (%d days): %s (%s) vs %s (%s)",
                divergence_days,
                comm_src.canonical_name,
                date_s,
                comm_alt.canonical_name,
                date_a,
            )
            return None

        # 5. Standardize comparison units
        norm_result = self._normalize_pair_units(
            price_src=price_s_raw,
            unit_src=unit_s_raw,
            price_alt=price_a_raw,
            unit_alt=unit_a_raw,
        )
        if not norm_result:
            return None

        price_s, price_a, std_unit = norm_result

        # 5. Qualification rules: Alternative MUST be cheaper by >= ৳2.00 AND >= 5.0%
        if price_a >= price_s:
            return None

        savings = round(price_s - price_a, 2)
        savings_pct = round((savings / price_s) * 100.0, 1)

        if savings < self.MIN_SAVINGS_BDT or savings_pct < self.MIN_SAVINGS_PCT:
            return None

        # 6. Dual-sided freshness evaluation (Phase 5B Hardened)
        freshness_meta_alt = evaluate_freshness(
            obs_date=date_a,
            scraped_at=scraped_a,
            ref_date=eval_date,
        )
        freshness_meta_src = evaluate_freshness(
            obs_date=date_s,
            scraped_at=scraped_s,
            ref_date=eval_date,
        )
        is_symmetric = (date_s == date_a)

        # 7. Projected basket line savings
        estimated_line_savings = None
        if basket_quantity is not None and basket_quantity > 0:
            estimated_line_savings = round(savings * basket_quantity, 2)

        return PriceAlternativeOut(
            source_commodity_id=comm_src.id,
            source_commodity_name=comm_src.canonical_name,
            source_bangla_name=comm_src.bangla_name,
            source_price=price_s,
            alternative_commodity_id=comm_alt.id,
            alternative_commodity_name=comm_alt.canonical_name,
            alternative_bangla_name=comm_alt.bangla_name,
            alternative_price=price_a,
            standard_unit=std_unit,
            savings_per_unit=savings,
            savings_percent=savings_pct,
            basket_quantity=basket_quantity,
            estimated_line_savings=estimated_line_savings,
            # Dual-sided freshness tracking
            source_observation_date=date_s.isoformat(),
            source_freshness_tier=freshness_meta_src.freshness_tier,
            alternative_observation_date=date_a.isoformat(),
            alternative_freshness_tier=freshness_meta_alt.freshness_tier,
            is_symmetric_freshness=is_symmetric,
            # Backward compatibility fields
            observation_date=date_a.isoformat(),
            freshness_tier=freshness_meta_alt.freshness_tier,
            provenance_status=prov_a,
            channel=channel,
            reason_bn=entry.reason_bn,
            reason_en=entry.reason_en,
        )

    def find_alternatives_for_commodity(
        self,
        db: Session,
        commodity_id: int,
        target_date: Optional[date] = None,
        channel: str = "retail",
        basket_quantity: Optional[float] = None,
    ) -> list[PriceAlternativeOut]:
        """Discover and rank all qualifying cheaper alternatives for a specific commodity."""
        candidates = self.get_candidate_entries(commodity_id)
        results: list[PriceAlternativeOut] = []

        for entry in candidates:
            alt = self.evaluate_alternative(
                db=db,
                entry=entry,
                target_date=target_date,
                channel=channel,
                basket_quantity=basket_quantity,
            )
            if alt:
                results.append(alt)

        # Rank: highest absolute savings first, then highest percentage savings
        results.sort(key=lambda x: (x.savings_per_unit, x.savings_percent), reverse=True)
        return results

    def find_alternatives_for_basket(
        self,
        db: Session,
        basket_items: list[tuple[int, float, str]],
        target_date: Optional[date] = None,
        channel: str = "retail",
    ) -> list[PriceAlternativeOut]:
        """
        Discover qualifying cheaper alternatives for all items in a user's basket.
        basket_items: list of (commodity_id, quantity_normalized, standard_unit)
        """
        all_alternatives: list[PriceAlternativeOut] = []
        seen_alt_keys = set()

        for comm_id, qty, _ in basket_items:
            alts = self.find_alternatives_for_commodity(
                db=db,
                commodity_id=comm_id,
                target_date=target_date,
                channel=channel,
                basket_quantity=qty,
            )
            for a in alts:
                key = (a.source_commodity_id, a.alternative_commodity_id)
                if key not in seen_alt_keys:
                    seen_alt_keys.add(key)
                    all_alternatives.append(a)

        # Sort overall by highest absolute savings
        all_alternatives.sort(
            key=lambda x: (x.estimated_line_savings or x.savings_per_unit, x.savings_percent),
            reverse=True,
        )
        return all_alternatives


# Module-level singleton
alternative_service = AlternativeRecommendationService()
