"""
Database schema initialization and canonical taxonomy seeding script.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path to allow execution from any directory
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
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models.commodity import Commodity, CommodityAlias
from app.models.location import Division, District, Market
from app.models.source import Source
from app.models.observation import PriceObservation


def init_schema():
    """Create all relational tables with foreign keys and indexes."""
    print("-> Creating database tables if not existing...")
    Base.metadata.create_all(bind=engine)
    print("   Database schema created successfully.")


def seed_locations(session):
    """Seed divisions, districts, and markets from data/taxonomy/locations.json."""
    loc_file = settings.taxonomy_dir / "locations.json"
    if not loc_file.exists():
        print(f"   [WARN] Locations seed file not found at {loc_file}")
        return

    with open(loc_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    div_count = 0
    dist_count = 0
    mkt_count = 0

    for div_data in data.get("divisions", []):
        div_stmt = select(Division).where(Division.name == div_data["name"])
        division = session.scalars(div_stmt).first()
        if not division:
            division = Division(name=div_data["name"], bangla_name=div_data.get("bangla_name"))
            session.add(division)
            session.flush()
            div_count += 1

        for dist_data in div_data.get("districts", []):
            dist_stmt = select(District).where(
                District.name == dist_data["name"], District.division_id == division.id
            )
            district = session.scalars(dist_stmt).first()
            if not district:
                district = District(
                    name=dist_data["name"],
                    bangla_name=dist_data.get("bangla_name"),
                    division_id=division.id,
                )
                session.add(district)
                session.flush()
                dist_count += 1

            for mkt_data in dist_data.get("markets", []):
                mkt_stmt = select(Market).where(
                    Market.name == mkt_data["name"], Market.district_id == district.id
                )
                market = session.scalars(mkt_stmt).first()
                if not market:
                    market = Market(
                        name=mkt_data["name"],
                        bangla_name=mkt_data.get("bangla_name"),
                        market_type=mkt_data.get("market_type", "retail"),
                        latitude=mkt_data.get("latitude"),
                        longitude=mkt_data.get("longitude"),
                        district_id=district.id,
                    )
                    session.add(market)
                    mkt_count += 1

    session.commit()
    print(f"   Seeded locations: {div_count} divisions, {dist_count} districts, {mkt_count} markets.")


def seed_commodities(session):
    """Seed canonical commodities and aliases from data/taxonomy/commodities.json."""
    comm_file = settings.taxonomy_dir / "commodities.json"
    if not comm_file.exists():
        print(f"   [WARN] Commodities seed file not found at {comm_file}")
        return

    with open(comm_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    comm_count = 0
    alias_count = 0

    for item in data:
        canonical_name = item["canonical_name"]
        stmt = select(Commodity).where(Commodity.canonical_name == canonical_name)
        commodity = session.scalars(stmt).first()
        if not commodity:
            commodity = Commodity(
                canonical_name=canonical_name,
                bangla_name=item["bangla_name"],
                category=item.get("category", "General"),
                default_unit=item.get("default_unit", "kg"),
            )
            session.add(commodity)
            session.flush()
            comm_count += 1

        for alias_data in item.get("aliases", []):
            alias_str = alias_data["alias"].strip()
            alias_stmt = select(CommodityAlias).where(
                CommodityAlias.alias == alias_str, CommodityAlias.commodity_id == commodity.id
            )
            existing_alias = session.scalars(alias_stmt).first()
            if not existing_alias:
                alias_obj = CommodityAlias(
                    commodity_id=commodity.id,
                    alias=alias_str,
                    language=alias_data.get("language", "bn"),
                    confidence_weight=float(alias_data.get("weight", 1.0)),
                )
                session.add(alias_obj)
                alias_count += 1

    session.commit()
    print(f"   Seeded commodities: {comm_count} commodities, {alias_count} aliases.")


def seed_sources(session):
    """Seed default publisher sources and field reporter source."""
    default_sources = [
        {"code": "DAM_DAILY", "name": "Department of Agricultural Marketing Live", "source_type": "government", "reliability_score": 0.95},
        {"code": "TCB_DAILY", "name": "Trading Corporation of Bangladesh Live", "source_type": "statutory_body", "reliability_score": 0.90},
        {"code": "CHALDAL_RETAIL", "name": "Chaldal Live Catalog", "source_type": "retail_ecommerce", "reliability_score": 0.88},
        {"code": "field_report", "name": "Field Spot Report (Manual)", "source_type": "field_report", "reliability_score": 0.60},
        {"code": "PRESS_REPORT", "name": "National Daily Press Spot Roundups", "source_type": "press", "reliability_score": 0.70},
    ]
    src_count = 0
    for s_data in default_sources:
        stmt = select(Source).where(Source.code == s_data["code"])
        src = session.scalars(stmt).first()
        if not src:
            src = Source(
                code=s_data["code"],
                name=s_data["name"],
                source_type=s_data["source_type"],
                reliability_score=s_data["reliability_score"],
            )
            session.add(src)
            src_count += 1
    session.commit()
    if src_count > 0:
        print(f"   Seeded sources: {src_count} data sources.")


def main():
    print("=== PricePulse BD: Database Initialization ===")
    init_schema()

    with SessionLocal() as session:
        print("-> Seeding administrative locations and market nodes...")
        seed_locations(session)
        print("-> Seeding canonical commodity taxonomy & aliases...")
        seed_commodities(session)
        print("-> Seeding data publishers and sources...")
        seed_sources(session)

    print("=== Database initialization completed successfully ===")



if __name__ == "__main__":
    main()
