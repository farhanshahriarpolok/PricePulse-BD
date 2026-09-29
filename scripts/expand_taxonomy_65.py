"""
Script to expand PricePulse BD taxonomy to 65 essential Bangladeshi staples
and seed realistic daily and 30-day baseline observations into pricepulse.db.
"""

import sys
import json
from pathlib import Path
from datetime import date, timedelta
import random

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.commodity import Commodity, CommodityAlias
from app.models.location import Market
from app.models.source import Source
from app.models.observation import PriceObservation
from scripts.init_db import seed_locations, seed_sources

NEW_COMMODITIES = [
    # --- Vegetables & Greens (11 items) ---
    {
        "canonical_name": "Red Spinach",
        "bangla_name": "লাল শাক",
        "category": "Vegetables",
        "default_unit": "bundle",
        "base_price": 20.0,
        "aliases": [
            {"alias": "লাল শাক", "language": "bn", "weight": 1.0},
            {"alias": "red spinach", "language": "en", "weight": 0.95},
            {"alias": "lal shak", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Spinach",
        "bangla_name": "পালং শাক",
        "category": "Vegetables",
        "default_unit": "bundle",
        "base_price": 25.0,
        "aliases": [
            {"alias": "পালং শাক", "language": "bn", "weight": 1.0},
            {"alias": "spinach", "language": "en", "weight": 0.95},
            {"alias": "palong shak", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Malabar Spinach",
        "bangla_name": "পুঁই শাক",
        "category": "Vegetables",
        "default_unit": "bundle",
        "base_price": 30.0,
        "aliases": [
            {"alias": "পুঁই শাক", "language": "bn", "weight": 1.0},
            {"alias": "malabar spinach", "language": "en", "weight": 0.95},
            {"alias": "pui shak", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Cauliflower",
        "bangla_name": "ফুলকপি",
        "category": "Vegetables",
        "default_unit": "pc",
        "base_price": 35.0,
        "aliases": [
            {"alias": "ফুলকপি", "language": "bn", "weight": 1.0},
            {"alias": "cauliflower", "language": "en", "weight": 0.95},
            {"alias": "fulkopi", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Cabbage",
        "bangla_name": "বাঁধাকপি",
        "category": "Vegetables",
        "default_unit": "pc",
        "base_price": 30.0,
        "aliases": [
            {"alias": "বাঁধাকপি", "language": "bn", "weight": 1.0},
            {"alias": "cabbage", "language": "en", "weight": 0.95},
            {"alias": "badhakopi", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Country Beans",
        "bangla_name": "শিম",
        "category": "Vegetables",
        "default_unit": "kg",
        "base_price": 60.0,
        "aliases": [
            {"alias": "শিম", "language": "bn", "weight": 1.0},
            {"alias": "country beans", "language": "en", "weight": 0.95},
            {"alias": "shim", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Okra",
        "bangla_name": "ঢ্যাঁড়শ",
        "category": "Vegetables",
        "default_unit": "kg",
        "base_price": 55.0,
        "aliases": [
            {"alias": "ঢ্যাঁড়শ", "language": "bn", "weight": 1.0},
            {"alias": "ভেন্ডি", "language": "bn", "weight": 0.95},
            {"alias": "okra", "language": "en", "weight": 0.95},
            {"alias": "dherosh", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Bottle Gourd",
        "bangla_name": "লাউ",
        "category": "Vegetables",
        "default_unit": "pc",
        "base_price": 50.0,
        "aliases": [
            {"alias": "লাউ", "language": "bn", "weight": 1.0},
            {"alias": "কদু", "language": "bn", "weight": 0.90},
            {"alias": "bottle gourd", "language": "en", "weight": 0.95},
            {"alias": "lau", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Green Banana",
        "bangla_name": "কাঁচকলা",
        "category": "Vegetables",
        "default_unit": "hali",
        "base_price": 32.0,
        "aliases": [
            {"alias": "কাঁচকলা", "language": "bn", "weight": 1.0},
            {"alias": "green banana", "language": "en", "weight": 0.95},
            {"alias": "kachkola", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Lemon",
        "bangla_name": "লেবু",
        "category": "Vegetables",
        "default_unit": "hali",
        "base_price": 28.0,
        "aliases": [
            {"alias": "লেবু", "language": "bn", "weight": 1.0},
            {"alias": "কাগজি লেবু", "language": "bn", "weight": 0.95},
            {"alias": "lemon", "language": "en", "weight": 0.95},
            {"alias": "lebu", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Pointed Gourd",
        "bangla_name": "পটল",
        "category": "Vegetables",
        "default_unit": "kg",
        "base_price": 45.0,
        "aliases": [
            {"alias": "পটল", "language": "bn", "weight": 1.0},
            {"alias": "pointed gourd", "language": "en", "weight": 0.95},
            {"alias": "potol", "language": "phonetic", "weight": 0.95},
        ]
    },

    # --- Grains & Pulses (4 items) ---
    {
        "canonical_name": "Chinigura Rice",
        "bangla_name": "চিনিগুঁড়া পোলাও চাল",
        "category": "Grains",
        "default_unit": "kg",
        "base_price": 140.0,
        "aliases": [
            {"alias": "চিনিগুঁড়া পোলাও চাল", "language": "bn", "weight": 1.0},
            {"alias": "পোলাও চাল", "language": "bn", "weight": 0.95},
            {"alias": "chinigura rice", "language": "en", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Paijam Rice",
        "bangla_name": "পাইজাম চাল",
        "category": "Grains",
        "default_unit": "kg",
        "base_price": 58.0,
        "aliases": [
            {"alias": "পাইজাম চাল", "language": "bn", "weight": 1.0},
            {"alias": "paijam rice", "language": "en", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Khesari Dal",
        "bangla_name": "খেসারি ডাল",
        "category": "Pulses",
        "default_unit": "kg",
        "base_price": 85.0,
        "aliases": [
            {"alias": "খেসারি ডাল", "language": "bn", "weight": 1.0},
            {"alias": "khesari dal", "language": "en", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Moong Dal",
        "bangla_name": "মুগ ডাল",
        "category": "Pulses",
        "default_unit": "kg",
        "base_price": 150.0,
        "aliases": [
            {"alias": "মুগ ডাল", "language": "bn", "weight": 1.0},
            {"alias": "moong dal", "language": "en", "weight": 0.95},
            {"alias": "mug dal", "language": "phonetic", "weight": 0.95},
        ]
    },

    # --- Fish & Meat (7 items) ---
    {
        "canonical_name": "Pabda Fish",
        "bangla_name": "পাবদা মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 380.0,
        "aliases": [
            {"alias": "পাবদা মাছ", "language": "bn", "weight": 1.0},
            {"alias": "pabda fish", "language": "en", "weight": 0.95},
            {"alias": "pabda", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Tengra Fish",
        "bangla_name": "টেংরা মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 450.0,
        "aliases": [
            {"alias": "টেংরা মাছ", "language": "bn", "weight": 1.0},
            {"alias": "tengra fish", "language": "en", "weight": 0.95},
            {"alias": "tengra", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Shrimp (Prawn)",
        "bangla_name": "চিংড়ি মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 650.0,
        "aliases": [
            {"alias": "চিংড়ি মাছ", "language": "bn", "weight": 1.0},
            {"alias": "চিংড়ি", "language": "bn", "weight": 0.98},
            {"alias": "shrimp", "language": "en", "weight": 0.95},
            {"alias": "prawn", "language": "en", "weight": 0.95},
            {"alias": "chingri", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Pomfret (Rupchanda)",
        "bangla_name": "রূপচাঁদা মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 750.0,
        "aliases": [
            {"alias": "রূপচাঁদা মাছ", "language": "bn", "weight": 1.0},
            {"alias": "রূপচাঁদা", "language": "bn", "weight": 0.98},
            {"alias": "pomfret", "language": "en", "weight": 0.95},
            {"alias": "rupchanda", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Shing Fish",
        "bangla_name": "শিং মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 520.0,
        "aliases": [
            {"alias": "শিং মাছ", "language": "bn", "weight": 1.0},
            {"alias": "shing fish", "language": "en", "weight": 0.95},
            {"alias": "shing", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Catla Fish",
        "bangla_name": "কাতলা মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 280.0,
        "aliases": [
            {"alias": "কাতলা মাছ", "language": "bn", "weight": 1.0},
            {"alias": "catla fish", "language": "en", "weight": 0.95},
            {"alias": "katla", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Koi Fish",
        "bangla_name": "কই মাছ",
        "category": "Fish & Seafood",
        "default_unit": "kg",
        "base_price": 220.0,
        "aliases": [
            {"alias": "কই মাছ", "language": "bn", "weight": 1.0},
            {"alias": "koi fish", "language": "en", "weight": 0.95},
            {"alias": "koi", "language": "phonetic", "weight": 0.95},
        ]
    },

    # --- Eggs & Dairy (1 item) ---
    {
        "canonical_name": "Duck Egg",
        "bangla_name": "হাঁসের ডিম",
        "category": "Eggs & Dairy",
        "default_unit": "hali",
        "base_price": 72.0,  # per hali
        "aliases": [
            {"alias": "হাঁসের ডিম", "language": "bn", "weight": 1.0},
            {"alias": "duck egg", "language": "en", "weight": 0.95},
            {"alias": "haser dim", "language": "phonetic", "weight": 0.95},
        ]
    },

    # --- Oils & Spices (7 items) ---
    {
        "canonical_name": "Cinnamon",
        "bangla_name": "দারুচিনি",
        "category": "Spices",
        "default_unit": "kg",
        "base_price": 480.0,
        "aliases": [
            {"alias": "দারুচিনি", "language": "bn", "weight": 1.0},
            {"alias": "cinnamon", "language": "en", "weight": 0.95},
            {"alias": "daruchini", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Cardamom",
        "bangla_name": "ছোট এলাচ",
        "category": "Spices",
        "default_unit": "kg",
        "base_price": 2800.0,
        "aliases": [
            {"alias": "ছোট এলাচ", "language": "bn", "weight": 1.0},
            {"alias": "এলাচ", "language": "bn", "weight": 0.95},
            {"alias": "cardamom", "language": "en", "weight": 0.95},
            {"alias": "elachi", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Cloves",
        "bangla_name": "লবঙ্গ",
        "category": "Spices",
        "default_unit": "kg",
        "base_price": 1450.0,
        "aliases": [
            {"alias": "লবঙ্গ", "language": "bn", "weight": 1.0},
            {"alias": "cloves", "language": "en", "weight": 0.95},
            {"alias": "lobongo", "language": "phonetic", "weight": 0.95},
            {"alias": "long", "language": "phonetic", "weight": 0.92},
        ]
    },
    {
        "canonical_name": "Bay Leaves",
        "bangla_name": "তেজপাতা",
        "category": "Spices",
        "default_unit": "kg",
        "base_price": 160.0,
        "aliases": [
            {"alias": "তেজপাতা", "language": "bn", "weight": 1.0},
            {"alias": "bay leaves", "language": "en", "weight": 0.95},
            {"alias": "tej pata", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Cumin Seeds",
        "bangla_name": "জিরা",
        "category": "Spices",
        "default_unit": "kg",
        "base_price": 750.0,
        "aliases": [
            {"alias": "জিরা", "language": "bn", "weight": 1.0},
            {"alias": "cumin seeds", "language": "en", "weight": 0.95},
            {"alias": "jira", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Coriander Powder",
        "bangla_name": "ধনিয়া গুঁড়া",
        "category": "Spices",
        "default_unit": "kg",
        "base_price": 240.0,
        "aliases": [
            {"alias": "ধনিয়া গুঁড়া", "language": "bn", "weight": 1.0},
            {"alias": "coriander powder", "language": "en", "weight": 0.95},
            {"alias": "dhonia gura", "language": "phonetic", "weight": 0.95},
        ]
    },
    {
        "canonical_name": "Sunflower Oil",
        "bangla_name": "সূর্যমুখী তেল",
        "category": "Edible Oils",
        "default_unit": "liter",
        "base_price": 260.0,
        "aliases": [
            {"alias": "সূর্যমুখী তেল", "language": "bn", "weight": 1.0},
            {"alias": "sunflower oil", "language": "en", "weight": 0.95},
        ]
    }
]

def expand_taxonomy():
    tax_path = PROJECT_ROOT / "data" / "taxonomy" / "commodities.json"
    with open(tax_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    
    existing_canonicals = {item["canonical_name"] for item in existing}
    added_count = 0
    for new_item in NEW_COMMODITIES:
        if new_item["canonical_name"] not in existing_canonicals:
            # Clean copy without 'base_price'
            clean_item = {
                "canonical_name": new_item["canonical_name"],
                "bangla_name": new_item["bangla_name"],
                "category": new_item["category"],
                "default_unit": new_item["default_unit"],
                "aliases": new_item["aliases"],
            }
            existing.append(clean_item)
            existing_canonicals.add(new_item["canonical_name"])
            added_count += 1
            
    with open(tax_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"-> Updated commodities.json: total {len(existing)} commodities (+{added_count} added).")
    return existing

def seed_database_and_observations():
    with SessionLocal() as session:
        seed_locations(session)
        seed_sources(session)
        
        # 1. Seed all commodities from file
        tax_path = PROJECT_ROOT / "data" / "taxonomy" / "commodities.json"
        with open(tax_path, "r", encoding="utf-8") as f:
            all_tax = json.load(f)
            
        for item in all_tax:
            stmt = select(Commodity).where(Commodity.canonical_name == item["canonical_name"])
            c = session.scalars(stmt).first()
            if not c:
                c = Commodity(
                    canonical_name=item["canonical_name"],
                    bangla_name=item["bangla_name"],
                    category=item.get("category", "General"),
                    default_unit=item.get("default_unit", "kg"),
                )
                session.add(c)
                session.flush()
                
            for alias_data in item.get("aliases", []):
                alias_str = alias_data["alias"].strip()
                alias_stmt = select(CommodityAlias).where(
                    CommodityAlias.alias == alias_str,
                    CommodityAlias.commodity_id == c.id
                )
                if not session.scalars(alias_stmt).first():
                    session.add(CommodityAlias(
                        commodity_id=c.id,
                        alias=alias_str,
                        language=alias_data.get("language", "bn"),
                        confidence_weight=float(alias_data.get("weight", 1.0))
                    ))
        session.commit()
        
        # 2. Get required nodes
        src_dam = session.scalars(select(Source).where(Source.code == "DAM_DAILY")).first()
        if not src_dam:
            src_dam = session.scalars(select(Source).where(Source.code == "dam_bulletin")).first()
            
        src_chaldal = session.scalars(select(Source).where(Source.code == "CHALDAL_RETAIL")).first()
        if not src_chaldal:
            src_chaldal = session.scalars(select(Source).where(Source.code == "chaldal_retail")).first()
            
        m_karwan = session.scalars(select(Market).where(Market.name == "Karwan Bazar")).first()
        m_khatunganj = session.scalars(select(Market).where(Market.name == "Khatunganj")).first()
        m_chaldal = session.scalars(select(Market).where(Market.name == "Chaldal Online Hub")).first()
        
        today = date.today()
        rng = random.Random(1337)
        
        # Build base price dict for new items
        base_map = {item["canonical_name"]: item.get("base_price", 50.0) for item in NEW_COMMODITIES}
        
        # Seed 30-day observations for each new commodity
        inserted = 0
        for item in NEW_COMMODITIES:
            c = session.scalars(select(Commodity).where(Commodity.canonical_name == item["canonical_name"])).first()
            if not c:
                continue
            base = base_map.get(c.canonical_name, 50.0)
            unit = c.default_unit
            
            for day_offset in range(29, -1, -1):
                obs_date = today - timedelta(days=day_offset)
                noise = rng.uniform(-0.03, 0.03) * base
                
                # Karwan Bazar Wholesale
                ws_price = round(base * 0.88 + noise, 1)
                session.add(PriceObservation(
                    commodity_id=c.id,
                    market_id=m_karwan.id,
                    source_id=src_dam.id,
                    raw_name=f"{c.canonical_name} ({unit})",
                    raw_price=ws_price,
                    raw_unit=unit,
                    normalized_price=ws_price,
                    normalized_unit=unit,
                    price_type="wholesale",
                    observation_date=obs_date,
                    confidence_score=0.95,
                ))
                
                # Karwan Bazar Retail
                ret_price = round(base + noise, 1)
                session.add(PriceObservation(
                    commodity_id=c.id,
                    market_id=m_karwan.id,
                    source_id=src_dam.id,
                    raw_name=f"{c.canonical_name} ({unit})",
                    raw_price=ret_price,
                    raw_unit=unit,
                    normalized_price=ret_price,
                    normalized_unit=unit,
                    price_type="retail",
                    observation_date=obs_date,
                    confidence_score=0.92,
                ))
                
                # Chaldal Online Retail
                on_price = round(base * 1.08 + noise, 1)
                session.add(PriceObservation(
                    commodity_id=c.id,
                    market_id=m_chaldal.id,
                    source_id=src_chaldal.id,
                    raw_name=f"{c.canonical_name} ({unit})",
                    raw_price=on_price,
                    raw_unit=unit,
                    normalized_price=on_price,
                    normalized_unit=unit,
                    price_type="retail",
                    observation_date=obs_date,
                    confidence_score=0.88,
                ))
                inserted += 3
                
        session.commit()
        print(f"-> Seeded {inserted} price observations for new commodities across 30 days.")

if __name__ == "__main__":
    expand_taxonomy()
    seed_database_and_observations()
