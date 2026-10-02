"""
Supply Chain Price Gap Deconstruction Service (Phase 5C).

Deconstructs the price difference between wholesale and retail channels
into transparent cost layers, strictly distinguishing directly observed prices
from modeled intermediary economic assumptions.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.commodity import Commodity
from app.models.location import District, Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.schemas.supply_chain import (
    ProvenanceType,
    SpreadStatus,
    SupplyChainComponent,
    SupplyChainDeconstructionResponse,
)
from app.services.freshness import evaluate_freshness
from app.services.normalizer import commodity_normalizer
from app.services.spatial_service import spatial_service

logger = logging.getLogger(__name__)


class SupplyChainService:
    """Calculates explainable supply chain cost breakdowns and residual spreads."""

    def __init__(self, benchmarks_path: Optional[str] = None):
        self.benchmarks_path = benchmarks_path or (
            settings.data_dir / "taxonomy" / "supply_chain_benchmarks.json"
        )
        self._benchmarks: dict = self._load_benchmarks()

    def _load_benchmarks(self) -> dict:
        """Load the calibrated benchmark registry from JSON."""
        try:
            with open(self.benchmarks_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load supply chain benchmarks from {self.benchmarks_path}: {e}")
            return {}

    def _get_perishability_tier(self, category: str) -> Tuple[str, float, str, str]:
        """
        Determine the perishability shrinkage rate and source for a given category.
        Returns: (tier_name, rate_pct, source_reference, methodology_note)
        """
        tiers_cfg = (
            self._benchmarks.get("parameters", {})
            .get("transit_wastage_allowance", {})
            .get("tiers", {})
        )

        cat_lower = (category or "").lower()
        for tier_key, tier_data in tiers_cfg.items():
            tier_cats = [c.lower() for c in tier_data.get("categories", [])]
            if any(c in cat_lower or cat_lower in c for c in tier_cats):
                return (
                    tier_key,
                    float(tier_data.get("rate_pct", 3.0)),
                    tier_data.get("source_reference", "Secondary Agricultural Literature"),
                    tier_data.get("methodology_note", "Modeled post-harvest shrinkage allowance"),
                )

        # Default fallback to moderate perishability
        mod_tier = tiers_cfg.get("MODERATE_PERISHABILITY", {})
        return (
            "MODERATE_PERISHABILITY",
            float(mod_tier.get("rate_pct", 3.0)),
            mod_tier.get("source_reference", "Secondary Agricultural Literature"),
            mod_tier.get("methodology_note", "Modeled post-harvest shrinkage allowance"),
        )

    def deconstruct_price_gap(
        self,
        db: Session,
        commodity_identifier: str,
        district_id: Optional[int] = None,
        destination_district_id: Optional[int] = None,
        target_date: Optional[date] = None,
    ) -> Optional[SupplyChainDeconstructionResponse]:
        """
        Deconstruct the spread between wholesale and retail observations.
        Does NOT clamp residual to zero. Gracefully surfaces margin compression when negative.
        """
        # 1. Resolve Commodity
        commodity = spatial_service.resolve_commodity(db, commodity_identifier)
        if not commodity:
            return None

        unit = commodity.default_unit or "kg"

        # 2. Build Query for Wholesale and Retail Observations
        # Exclude synthetic/modeled records (e.g. PANDAMART_MODELED, modeled_benchmark)
        base_stmt = (
            select(PriceObservation)
            .join(Source, PriceObservation.source_id == Source.id)
            .where(
                PriceObservation.commodity_id == commodity.id,
                Source.code != "PANDAMART_MODELED",
                PriceObservation.price_type != "modeled_benchmark",
            )
        )

        if target_date:
            base_stmt = base_stmt.where(PriceObservation.observation_date <= target_date)

        # Fetch Wholesale Observation
        w_stmt = base_stmt.where(PriceObservation.price_type.like("%wholesale%"))
        if district_id:
            w_stmt = w_stmt.join(Market, PriceObservation.market_id == Market.id).where(
                Market.district_id == district_id
            )
        w_obs = db.scalars(
            w_stmt.order_by(PriceObservation.observation_date.desc(), PriceObservation.id.desc())
        ).first()

        # Fetch Retail Observation
        r_stmt = base_stmt.where(PriceObservation.price_type.like("%retail%"))
        target_retail_dist = destination_district_id or district_id
        if target_retail_dist:
            r_stmt = r_stmt.join(Market, PriceObservation.market_id == Market.id).where(
                Market.district_id == target_retail_dist
            )
        r_obs = db.scalars(
            r_stmt.order_by(PriceObservation.observation_date.desc(), PriceObservation.id.desc())
        ).first()

        w_price = round(w_obs.normalized_price, 2) if w_obs else None
        r_price = round(r_obs.normalized_price, 2) if r_obs else None

        # Freshness evaluation using canonical BST boundary
        w_freshness = (
            evaluate_freshness(w_obs.observation_date, w_obs.scraped_at)
            if w_obs
            else None
        )
        r_freshness = (
            evaluate_freshness(r_obs.observation_date, r_obs.scraped_at)
            if r_obs
            else None
        )

        w_date = w_obs.observation_date if w_obs else None
        r_date = r_obs.observation_date if r_obs else None

        temporal_gap = abs((r_date - w_date).days) if (r_date and w_date) else 0
        is_symmetric = (temporal_gap == 0)

        # Market names and districts
        w_market = db.get(Market, w_obs.market_id) if w_obs else None
        r_market = db.get(Market, r_obs.market_id) if r_obs else None

        src_dist_obj = db.get(District, w_market.district_id) if (w_market and w_market.district_id) else None
        dest_dist_obj = db.get(District, r_market.district_id) if (r_market and r_market.district_id) else None

        src_dist_name = src_dist_obj.name if src_dist_obj else None
        dest_dist_name = dest_dist_obj.name if dest_dist_obj else None

        # 3. Calculate Transport Logistics Freight
        freight_cfg = self._benchmarks.get("parameters", {}).get("freight_logistics", {})
        is_inter_district = (
            src_dist_obj and dest_dist_obj and src_dist_obj.id != dest_dist_obj.id
        )

        corridor_name = None
        corridor_distance = None
        freight_bdt = 0.0
        freight_provenance = ProvenanceType.MODELED_ASSUMPTION
        freight_source_name = "PricePulse BD Highway Logistics Engine"
        freight_source_ref = "Calibrated national highway transport cost model"
        freight_method_note = "Local intra-district wholesale-to-retail transit flat rate (1.50 BDT/unit)"

        if is_inter_district:
            s_lat = (w_market.latitude if (w_market and w_market.latitude) else None) or 24.8465
            s_lon = (w_market.longitude if (w_market and w_market.longitude) else None) or 89.3770
            d_lat = (r_market.latitude if (r_market and r_market.latitude) else None) or 23.8103
            d_lon = (r_market.longitude if (r_market and r_market.longitude) else None) or 90.4125

            corridor_distance = spatial_service.haversine_distance(s_lat, s_lon, d_lat, d_lon)
            var_rate = float(freight_cfg.get("variable_rate_bdt_per_kg_km", 0.018))
            dist_cost = round(corridor_distance * var_rate, 2)

            toll_buffer = 0.35
            # Resolve specific bridge toll if available
            toll_cfg = freight_cfg.get("toll_buffers", {})
            pair_key = (src_dist_name, dest_dist_name)
            if pair_key in [("Bogura", "Dhaka"), ("Rangpur", "Dhaka"), ("Dinajpur", "Dhaka"), ("Rajshahi", "Dhaka")]:
                toll_buffer = float(toll_cfg.get("jamuna_bridge", {}).get("toll_bdt_per_kg", 0.50))
                corridor_name = f"{src_dist_name} ➔ {dest_dist_name} (বঙ্গবন্ধু যমুনা সেতু করিডোর)"
            elif pair_key in [("Jashore", "Dhaka"), ("Khulna", "Dhaka"), ("Barishal", "Dhaka")]:
                toll_buffer = float(toll_cfg.get("padma_bridge", {}).get("toll_bdt_per_kg", 0.60))
                corridor_name = f"{src_dist_name} ➔ {dest_dist_name} (পদ্মা বহুমুখী সেতু করিডোর)"
            else:
                toll_buffer = float(toll_cfg.get("general_inter_district", {}).get("toll_bdt_per_kg", 0.35))
                corridor_name = f"{src_dist_name} ➔ {dest_dist_name} জাতীয় মহাসড়ক করিডোর"

            freight_bdt = round(dist_cost + toll_buffer, 2)
            freight_method_note = (
                f"Inter-district highway freight ({corridor_distance:.1f} km road @ 0.018 BDT/km + "
                f"৳{toll_buffer:.2f} bridge/toll buffer)"
            )
        else:
            freight_bdt = float(freight_cfg.get("local_intra_district_flat_bdt", 1.50))

        # 4. Modeled Intermediary Components (Arath Commission, Handling, Spoilage)
        components: List[SupplyChainComponent] = []
        observed_or_supported_costs = round(freight_bdt, 2)
        modeled_costs = 0.0

        # Component: Freight
        components.append(
            SupplyChainComponent(
                name="Transport Freight & Logistics",
                bangla_name="পরিবহন ও হাইওয়ে ফ্রেইট খরচ",
                value_bdt=freight_bdt,
                unit=unit,
                provenance_type=freight_provenance,
                source_name=freight_source_name,
                source_reference=freight_source_ref,
                methodology_note=freight_method_note,
            )
        )

        # Modeled: Arath Commission
        arath_cfg = self._benchmarks.get("parameters", {}).get("arath_commission", {})
        arath_pct = float(arath_cfg.get("value", 3.0))
        arath_bdt = round((w_price or 0.0) * (arath_pct / 100.0), 2) if w_price else 0.0
        modeled_costs += arath_bdt

        components.append(
            SupplyChainComponent(
                name="Wholesale Arathdar Commission Assumption",
                bangla_name="আড়তদারি কমিশন প্রাক্কলন",
                value_bdt=arath_bdt,
                unit=unit,
                provenance_type=ProvenanceType.MODELED_ASSUMPTION,
                source_name=arath_cfg.get("source_name", "Agricultural Market Research"),
                source_reference=arath_cfg.get("source_reference", "World Bank / Minten et al. surveys (2.5%-4.0%)"),
                methodology_note=arath_cfg.get(
                    "methodology_note", "Modeled assumption: 3.0% of empirical wholesale price"
                ),
            )
        )

        # Modeled: Terminal Handling & Porterage
        handling_cfg = self._benchmarks.get("parameters", {}).get("terminal_handling_porterage", {})
        handling_rates = handling_cfg.get("value_per_unit", {})
        handling_rate = float(handling_rates.get(unit, handling_rates.get("kg", 1.25)))
        handling_bdt = round(handling_rate, 2)
        modeled_costs += handling_bdt

        components.append(
            SupplyChainComponent(
                name="Terminal Handling & Porterage Assumption",
                bangla_name="কুলি, আনলোডিং ও বাজার টোল প্রাক্কলন",
                value_bdt=handling_bdt,
                unit=unit,
                provenance_type=ProvenanceType.MODELED_ASSUMPTION,
                source_name=handling_cfg.get("source_name", "Urban Terminal Porterage Baselines"),
                source_reference=handling_cfg.get("source_reference", "Secondary municipal market survey rates"),
                methodology_note=handling_cfg.get(
                    "methodology_note", f"Modeled flat loading & stall entry allowance: {handling_bdt:.2f} BDT/{unit}"
                ),
            )
        )

        # Modeled: Perishability Spoilage & Shrinkage
        tier_name, wastage_pct, wastage_ref, wastage_note = self._get_perishability_tier(
            commodity.category
        )
        wastage_bdt = round((w_price or 0.0) * (wastage_pct / 100.0), 2) if w_price else 0.0
        modeled_costs += wastage_bdt

        components.append(
            SupplyChainComponent(
                name="Transit Spoilage & Shrinkage Allowance Assumption",
                bangla_name="পচনশীলতা অপচয় ও আর্দ্রতা ঘাটতি প্রাক্কলন",
                value_bdt=wastage_bdt,
                unit=unit,
                provenance_type=ProvenanceType.MODELED_ASSUMPTION,
                source_name="BARC & Agricultural Research Baselines",
                source_reference=wastage_ref,
                methodology_note=f"{wastage_note} ({wastage_pct:.1f}% of wholesale benchmark for {commodity.category})",
            )
        )

        modeled_costs = round(modeled_costs, 2)

        # 5. Gross Spread and Residual Spread Calculation
        gross_spread = None
        gross_spread_pct = None
        residual_spread = None
        margin_compression = None
        spread_status = SpreadStatus.NORMAL_SPREAD

        if w_price is not None and r_price is not None:
            gross_spread = round(r_price - w_price, 2)
            gross_spread_pct = (
                round((gross_spread / w_price) * 100.0, 1) if w_price > 0 else 0.0
            )

            # Mathematical derivation of residual spread
            # residual = gross_spread - observed_or_supported_costs - modeled_costs
            residual_spread = round(gross_spread - observed_or_supported_costs - modeled_costs, 2)

            if residual_spread < 0:
                spread_status = SpreadStatus.COMPRESSED_MARGIN
                margin_compression = round(abs(residual_spread), 2)
            elif residual_spread > (r_price * 0.25):
                spread_status = SpreadStatus.EXPANDED_SPREAD
            else:
                spread_status = SpreadStatus.NORMAL_SPREAD

            # Calculate component percentages against spread and retail
            for comp in components:
                if gross_spread > 0:
                    comp.percentage_of_spread = round((comp.value_bdt / gross_spread) * 100.0, 1)
                if r_price > 0:
                    comp.percentage_of_retail = round((comp.value_bdt / r_price) * 100.0, 1)

            # Component: Residual Spread
            components.append(
                SupplyChainComponent(
                    name="Residual Spread — Unobserved/Unallocated Portion",
                    bangla_name="অবশিষ্ট স্প্রেড — অনিরীক্ষিত/অনাবন্টিত অংশ",
                    value_bdt=residual_spread,
                    percentage_of_spread=(
                        round((residual_spread / gross_spread) * 100.0, 1) if gross_spread > 0 else None
                    ),
                    percentage_of_retail=(
                        round((residual_spread / r_price) * 100.0, 1) if r_price > 0 else None
                    ),
                    unit=unit,
                    provenance_type=ProvenanceType.MODELED_ASSUMPTION,
                    source_name="Mathematical Model Residual",
                    source_reference="Gross spread minus intermediate freight and modeled cost components",
                    methodology_note=(
                        "Mathematical remainder after subtracting supported freight and modeled intermediary "
                        "components from gross spread. It is NOT directly observed and not claimed as actual retailer profit or observed operating cost."
                        if residual_spread >= 0
                        else f"Negative residual (-৳{margin_compression:.2f}) indicates intermediate modeled costs exceed observed price spread."
                    ),
                )
            )

        return SupplyChainDeconstructionResponse(
            commodity_id=commodity.id,
            canonical_name=commodity.canonical_name,
            bangla_name=commodity.bangla_name,
            category=commodity.category,
            calculation_unit=unit,
            wholesale_price=w_price,
            retail_price=r_price,
            gross_spread_bdt=gross_spread,
            gross_spread_pct=gross_spread_pct,
            wholesale_market_name=w_market.name if w_market else "Wholesale Benchmark",
            retail_market_name=r_market.name if r_market else "Retail Kitchen Market",
            source_district=src_dist_name,
            destination_district=dest_dist_name,
            corridor_name=corridor_name,
            corridor_distance_km=corridor_distance,
            wholesale_observation_date=w_date,
            retail_observation_date=r_date,
            wholesale_freshness_tier=w_freshness.freshness_tier if w_freshness else None,
            retail_freshness_tier=r_freshness.freshness_tier if r_freshness else None,
            is_symmetric_freshness=is_symmetric,
            temporal_divergence_days=temporal_gap,
            observed_or_supported_costs_bdt=observed_or_supported_costs,
            modeled_costs_bdt=modeled_costs,
            residual_spread_bdt=residual_spread,
            spread_status=spread_status,
            margin_compression_bdt=margin_compression,
            components=components,
        )


supply_chain_service = SupplyChainService()
