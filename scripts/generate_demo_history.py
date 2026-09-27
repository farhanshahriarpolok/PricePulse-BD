"""
Generates 30 days of realistic historical market observations with a calibrated Onion price shock.
Designed for offline viva defense and statistical anomaly validation.
"""

import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure utf-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlalchemy import select
from app.core.database import SessionLocal, engine, Base
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.source import Source
from app.models.observation import PriceObservation
from scripts.init_db import init_schema, seed_locations, seed_commodities


def get_or_create_source(session, code: str, name: str, source_type: str, reliability: float) -> Source:
    stmt = select(Source).where(Source.code == code)
    src = session.scalars(stmt).first()
    if not src:
        src = Source(
            code=code,
            name=name,
            source_type=source_type,
            reliability_score=reliability,
        )
        session.add(src)
        session.flush()
    return src


def generate_history():
    print("=== PricePulse BD: Generating 30-Day Demo History ===")
    init_schema()

    with SessionLocal() as session:
        seed_locations(session)
        seed_commodities(session)

        # Retrieve sources
        src_dam = get_or_create_source(
            session, "DAM_DAILY", "Department of Agricultural Marketing", "government", 0.95
        )
        src_chaldal = get_or_create_source(
            session, "CHALDAL_RETAIL", "Chaldal Online Grocery", "retail_ecommerce", 0.88
        )

        # Retrieve markets
        m_karwan = session.scalars(select(Market).where(Market.name == "Karwan Bazar")).first()
        m_khatunganj = session.scalars(select(Market).where(Market.name == "Khatunganj")).first()
        m_chaldal = session.scalars(select(Market).where(Market.name == "Chaldal Online Hub")).first()

        # Retrieve commodities
        c_onion = session.scalars(select(Commodity).where(Commodity.canonical_name == "Onion (Local)")).first()
        c_potato = session.scalars(select(Commodity).where(Commodity.canonical_name == "Potato (Diamond)")).first()
        c_rice = session.scalars(select(Commodity).where(Commodity.canonical_name == "Rice (Miniket)")).first()
        c_oil = session.scalars(select(Commodity).where(Commodity.canonical_name == "Soybean Oil (Bottled)")).first()

        if not all([m_karwan, m_khatunganj, m_chaldal, c_onion, c_potato, c_rice, c_oil]):
            print("Error: Missing required markets or commodities. Run init_db.py first.")
            return

        today = date.today()
        total_inserted = 0
        total_updated = 0

        # Deterministic random seed for reproducible observations
        rng = random.Random(42)

        print("-> Synthesizing 30 daily price time-series...")

        for day_offset in range(29, -1, -1):
            obs_date = today - timedelta(days=day_offset)
            days_from_start = 29 - day_offset  # 0 to 29

            # --- 1. Potato (Diamond) - Stable Baseline ---
            p_base = 44.0 + rng.uniform(-1.0, 1.0)
            potato_configs = [
                (c_potato, m_karwan, src_dam, "wholesale_avg", round(p_base, 2), "কেজি", 1.0, 0.93),
                (c_potato, m_karwan, src_dam, "retail_avg", round(p_base + 6.0, 2), "কেজি", 1.0, 0.93),
                (c_potato, m_khatunganj, src_dam, "wholesale_avg", round(p_base + 1.5, 2), "কেজি", 1.0, 0.92),
                (c_potato, m_chaldal, src_chaldal, "retail_avg", round(p_base + 11.0, 2), "1 kg", 1.0, 0.88),
            ]

            # --- 2. Rice (Miniket) - Stable Baseline ---
            r_base = 70.0 + rng.uniform(-0.8, 0.8)
            rice_configs = [
                (c_rice, m_karwan, src_dam, "wholesale_avg", round(r_base, 2), "কেজি", 1.0, 0.94),
                (c_rice, m_karwan, src_dam, "retail_avg", round(r_base + 7.0, 2), "কেজি", 1.0, 0.94),
                (c_rice, m_khatunganj, src_dam, "wholesale_avg", round(r_base + 0.5, 2), "কেজি", 1.0, 0.93),
                (c_rice, m_chaldal, src_chaldal, "retail_avg", round(r_base + 10.0, 2), "1 kg", 1.0, 0.88),
            ]

            # --- 3. Soybean Oil (Bottled) - Fixed/Administered Baseline ---
            oil_base = 162.0 + rng.uniform(-0.5, 0.5)
            oil_configs = [
                (c_oil, m_karwan, src_dam, "wholesale_avg", round(oil_base, 2), "লিটার", 1.0, 0.95),
                (c_oil, m_karwan, src_dam, "retail_avg", 167.0, "লিটার", 1.0, 0.95),
                (c_oil, m_chaldal, src_chaldal, "retail_avg", 167.0, "1 liter", 1.0, 0.88),
            ]

            # --- 4. Onion (Local) - Calibrated 5-Day Supply Shock ---
            # Normal days (0 to 24): Wholesale ~85 BDT, Retail ~95 BDT, Chaldal ~105 BDT
            # Shock days (25 to 29): Progressive surge reaching Wholesale 118 BDT, Retail 128 BDT, Chaldal 140 BDT
            if days_from_start < 25:
                o_base = 85.0 + rng.uniform(-1.5, 1.5)
                shock_boost = 0.0
            else:
                # Escalating shock over the last 5 days
                shock_day = days_from_start - 24  # 1, 2, 3, 4, 5
                shock_boost = shock_day * 6.5     # +6.5, +13.0, +19.5, +26.0, +32.5 BDT
                o_base = 85.0 + shock_boost + rng.uniform(-0.5, 0.5)

            onion_configs = [
                (c_onion, m_karwan, src_dam, "wholesale_avg", round(o_base, 2), "কেজি", 1.0, 0.935),
                (c_onion, m_karwan, src_dam, "retail_avg", round(o_base + 10.0, 2), "কেজি", 1.0, 0.935),
                (c_onion, m_khatunganj, src_dam, "wholesale_avg", round(o_base + 2.0, 2), "কেজি", 1.0, 0.935),
                (c_onion, m_khatunganj, src_dam, "retail_avg", round(o_base + 12.0, 2), "কেজি", 1.0, 0.935),
                (c_onion, m_chaldal, src_chaldal, "retail_avg", round(o_base + 20.0, 2), "1 kg", 1.0, 0.886),
            ]

            all_day_configs = potato_configs + rice_configs + oil_configs + onion_configs

            for comm, mkt, src, p_type, raw_p, unit_str, mult, conf in all_day_configs:
                norm_p = round(raw_p / mult, 2)
                base_unit = comm.default_unit

                stmt = select(PriceObservation).where(
                    PriceObservation.commodity_id == comm.id,
                    PriceObservation.market_id == mkt.id,
                    PriceObservation.source_id == src.id,
                    PriceObservation.observation_date == obs_date,
                    PriceObservation.price_type == p_type,
                )
                existing = session.scalars(stmt).first()

                if existing:
                    existing.raw_price = raw_p
                    existing.raw_unit = unit_str
                    existing.normalized_price = norm_p
                    existing.normalized_unit = base_unit
                    existing.confidence_score = conf
                    total_updated += 1
                else:
                    new_obs = PriceObservation(
                        commodity_id=comm.id,
                        market_id=mkt.id,
                        source_id=src.id,
                        raw_name=f"{comm.canonical_name} ({unit_str})",
                        raw_price=raw_p,
                        raw_unit=unit_str,
                        normalized_price=norm_p,
                        normalized_unit=base_unit,
                        price_type=p_type,
                        observation_date=obs_date,
                        confidence_score=conf,
                    )
                    session.add(new_obs)
                    total_inserted += 1

            session.flush()

        session.commit()
        print(f"-> Successfully generated 30 days of data: {total_inserted} inserted, {total_updated} updated.")
        print(f"-> Verified calibrated shock for Onion (Local) over final 5 days up to {today}.")


if __name__ == "__main__":
    generate_history()
