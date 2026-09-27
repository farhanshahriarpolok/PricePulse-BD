"""
Execution script to initialize schema, seed taxonomy, and run the first ingestion slice.
"""

import sys
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

from sqlalchemy import select, func
from app.core.database import SessionLocal
from scripts.init_db import init_schema, seed_locations, seed_commodities
from app.collectors.dam_fixture_collector import DAMFixtureCollector
from app.services.ingestion import IngestionPipeline
from app.models.commodity import Commodity
from app.models.location import Market
from app.models.observation import PriceObservation


def run_pipeline():
    print("=== PricePulse BD: Seed and Ingest Execution ===")
    
    # 1. Initialize schema and taxonomy
    init_schema()
    
    with SessionLocal() as session:
        print("-> Ensuring taxonomy and market seeds...")
        seed_locations(session)
        seed_commodities(session)

        # 2. Execute DAM Fixture Ingestion Slice
        print("-> Running DAM bulletin fixture collector...")
        collector = DAMFixtureCollector()
        pipeline = IngestionPipeline(db=session)
        report = pipeline.run_collector(collector)

        print("\n--- Ingestion Summary Report ---")
        print(f"Source Code     : {report.source_code}")
        print(f"Total Harvested : {report.total_harvested}")
        print(f"New Inserted    : {report.inserted}")
        print(f"Updated         : {report.updated}")
        print(f"Skipped         : {report.skipped}")

        # 3. Query distinct observations across staple items
        print("\n--- Sample Ingested Observations ---")
        query = (
            select(
                Commodity.canonical_name,
                Market.name.label("market_name"),
                PriceObservation.raw_name,
                PriceObservation.raw_price,
                PriceObservation.raw_unit,
                PriceObservation.normalized_price,
                PriceObservation.normalized_unit,
                PriceObservation.price_type,
                PriceObservation.confidence_score,
                PriceObservation.observation_date,
            )
            .join(Commodity, PriceObservation.commodity_id == Commodity.id)
            .join(Market, PriceObservation.market_id == Market.id)
            .order_by(Commodity.canonical_name, Market.name, PriceObservation.price_type)
        )
        results = session.execute(query).all()

        for row in results:
            print(
                f"[{row.canonical_name:<20}] @ {row.market_name:<14} | "
                f"{row.price_type:<14} | Raw: {row.raw_price:>7.2f} {row.raw_unit:<4} -> "
                f"Norm: BDT {row.normalized_price:>6.2f}/{row.normalized_unit:<2} | "
                f"Conf: {row.confidence_score:.3f} | Date: {row.observation_date}"
            )

        # Total counts
        total_obs = session.scalar(select(func.count(PriceObservation.id)))
        print(f"\nTotal Price Observations in Database: {total_obs}")


if __name__ == "__main__":
    run_pipeline()
