"""
Deterministic unit and integration tests for MeenaBazarCollector.
Covers:
- Successful harvest from mock / fixture
- Canonical commodity mapping accuracy
- Cultural unit normalization and package-size calculations
- Out-of-stock and zero-price filtering
- Duplicate product deduplication
- Network failure & graceful fallback to local fixture
- Database persistence via IngestionPipeline
- SourceHealth telemetry updates
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch
import pytest
import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.collectors.base import CollectionStatus
from app.collectors.meena_bazar_collector import MeenaBazarCollector
from app.core.database import Base
from app.models.commodity import Commodity
from app.models.location import Division, District, Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.services.ingestion import IngestionPipeline
from app.services.normalizer import CommodityNormalizer
from app.services.source_health import source_health_service


@pytest.fixture
def mock_meena_bazar_payload():
    return {
        "code": 201,
        "status": "success",
        "data": {
            "homeProductSection": [
                {
                    "ItemId": "mb-1",
                    "ItemDisplayName": "Beef Bone-In Premium",
                    "UnitSalesPrice": 412.5,
                    "DiscountSalesPrice": 412.5,
                    "Unit": "500g",
                    "StockQuantity": 100,
                },
                {
                    "ItemId": "mb-2",
                    "ItemDisplayName": "Najir Rice (Premium)",
                    "UnitSalesPrice": 82.0,
                    "DiscountSalesPrice": 82.0,
                    "Unit": "KG",
                    "StockQuantity": 39,
                },
                {
                    "ItemId": "mb-3",
                    "ItemDisplayName": "Minicate Rice (Premium)",
                    "UnitSalesPrice": 72.0,
                    "DiscountSalesPrice": 72.0,
                    "Unit": "KG",
                    "StockQuantity": 236,
                },
                {
                    "ItemId": "mb-4",
                    "ItemDisplayName": "Onion Local Bulk Regular",
                    "UnitSalesPrice": 27.0,
                    "DiscountSalesPrice": 27.0,
                    "Unit": "500g",
                    "StockQuantity": 704,
                },
                {
                    "ItemId": "mb-5",
                    "ItemDisplayName": "Farm Fresh Paragon Omega3+ Egg 12pcs",
                    "UnitSalesPrice": 265.0,
                    "DiscountSalesPrice": 265.0,
                    "Unit": "12 pcs",
                    "StockQuantity": 24,
                },
                {
                    "ItemId": "mb-6",
                    "ItemDisplayName": "Rupchanda Soyabean Oil Pet 5ltr",
                    "UnitSalesPrice": 1000.0,
                    "DiscountSalesPrice": 1000.0,
                    "Unit": "5 liter",
                    "StockQuantity": 50,
                },
                # Out of stock item -> must be ignored
                {
                    "ItemId": "mb-7",
                    "ItemDisplayName": "Potato Bulk White Regular",
                    "UnitSalesPrice": 15.0,
                    "DiscountSalesPrice": 15.0,
                    "Unit": "500g",
                    "StockQuantity": 0,
                },
                # Zero price item -> must be ignored
                {
                    "ItemId": "mb-8",
                    "ItemDisplayName": "Green Chili Local",
                    "UnitSalesPrice": 0.0,
                    "DiscountSalesPrice": 0.0,
                    "Unit": "100g",
                    "StockQuantity": 50,
                },
                # Unmapped item -> must never be guessed
                {
                    "ItemId": "mb-9",
                    "ItemDisplayName": "Paragon Chicken Mini Spring Roll -300gm",
                    "UnitSalesPrice": 235.0,
                    "DiscountSalesPrice": 235.0,
                    "Unit": "EACH",
                    "StockQuantity": 20,
                },
                # Duplicate item -> must be deduplicated
                {
                    "ItemId": "mb-10",
                    "ItemDisplayName": "Najir Rice (Premium)",
                    "UnitSalesPrice": 85.0,
                    "DiscountSalesPrice": 85.0,
                    "Unit": "KG",
                    "StockQuantity": 39,
                },
            ]
        }
    }


class TestMeenaBazarCollectorUnit:
    """Deterministic tests for Meena Bazar collector logic and mapping."""

    def test_fixture_harvest_success(self):
        collector = MeenaBazarCollector(enable_network=False)
        observations = collector.collect()

        assert len(observations) > 0
        for obs in observations:
            assert obs.source_code == "MEENA_BAZAR_RETAIL"
            assert obs.market_name == "Meena Bazar Hub"
            assert obs.raw_price > 0.0
            assert obs.is_fallback is True
            assert obs.collection_status == CollectionStatus.FALLBACK.value
            assert obs.source_url == "https://meenabazaronline.com"

    def test_canonical_mapping_accuracy(self, mock_meena_bazar_payload):
        collector = MeenaBazarCollector(enable_network=True)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_meena_bazar_payload
            mock_get.return_value = mock_resp

            observations = collector.collect()
            mapped_names = {obs.raw_commodity_name for obs in observations}

            assert "Beef (Local with Bone)" in mapped_names
            assert "Rice (Nazirshail)" in mapped_names
            assert "Rice (Miniket)" in mapped_names
            assert "Onion (Local)" in mapped_names
            assert "Farm Egg" in mapped_names
            assert "Soybean Oil (Bottled)" in mapped_names
            # Unmapped spring roll must never be mapped
            assert "Spring Roll" not in mapped_names
            # Out of stock potato and zero-price chilli must be excluded
            assert "Potato (Diamond)" not in mapped_names
            assert "Green Chilli" not in mapped_names

    def test_deduplication_in_harvest(self, mock_meena_bazar_payload):
        collector = MeenaBazarCollector(enable_network=True)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_meena_bazar_payload
            mock_get.return_value = mock_resp

            observations = collector.collect()
            rice_obs = [o for o in observations if o.raw_commodity_name == "Rice (Nazirshail)"]
            assert len(rice_obs) == 1

    def test_live_network_failure_falls_back_cleanly(self):
        collector = MeenaBazarCollector(enable_network=True, max_retries=1)

        with patch("httpx.Client.get", side_effect=httpx.ConnectTimeout("Connection timed out")):
            observations = collector.collect()

            assert len(observations) > 0
            for obs in observations:
                assert obs.is_fallback is True
                assert obs.collection_status == CollectionStatus.FALLBACK.value
                assert "ConnectTimeout" in (obs.error_message or "")

    def test_source_health_recording(self, mock_meena_bazar_payload):
        collector = MeenaBazarCollector(enable_network=True)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_meena_bazar_payload
            mock_get.return_value = mock_resp

            collector.collect()
            telemetry = source_health_service.get_source_status("MEENA_BAZAR_RETAIL")
            assert telemetry is not None
            assert telemetry["status"] == "HEALTHY"
            assert telemetry["is_fallback"] is False


class TestMeenaBazarIngestionPersistence:
    """Integration test verifying MeenaBazarCollector persistence into SQLite via IngestionPipeline."""

    @pytest.fixture
    def test_db(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        div = Division(id=1, name="Dhaka", bangla_name="ঢাকা")
        dist = District(id=1, division_id=1, name="Dhaka", bangla_name="ঢাকা")
        mkt = Market(id=1, district_id=1, name="Karwan Bazar", bangla_name="কাওরান বাজার", market_type="wholesale")
        db.add_all([div, dist, mkt])

        commodities_to_seed = [
            ("Beef (Local with Bone)", "গরুর মাংস (হাড়সহ)", "Meat", "kg"),
            ("Rice (Nazirshail)", "নাজিরশাইল চাল", "Rice & Grains", "kg"),
            ("Rice (Miniket)", "মিনিকেট চাল", "Rice & Grains", "kg"),
            ("Broiler Chicken", "ব্রয়লার মুরগি", "Meat", "kg"),
            ("Farm Egg", "ফার্মের ডিম", "Eggs & Milk", "pc"),
            ("Onion (Local)", "দেশি পেঁয়াজ", "Vegetables", "kg"),
            ("Potato (Diamond)", "আলু (ডায়মন্ড)", "Vegetables", "kg"),
            ("Green Chilli", "কাঁচা মরিচ", "Vegetables", "kg"),
            ("Cucumber", "শসা", "Vegetables", "kg"),
            ("Cauliflower", "ফুলকপি", "Vegetables", "pc"),
            ("Soybean Oil (Bottled)", "সয়াবিন তেল (বোতল)", "Oil & Spices", "liter"),
            ("Atta (Packaged)", "আটা (প্যাকেট)", "Rice & Grains", "kg"),
            ("Sugar (Refined White)", "সাদা চিনি", "Oil & Spices", "kg"),
            ("Lemon", "লেবু", "Vegetables", "hali"),
            ("Cabbage", "বাঁধাকপি", "Vegetables", "pc"),
            ("Khesari Dal", "খেসারি ডাল", "Rice & Grains", "kg"),
        ]
        for cname, bname, cat, unit in commodities_to_seed:
            comm = Commodity(canonical_name=cname, bangla_name=bname, category=cat, default_unit=unit)
            db.add(comm)

        db.commit()
        yield db
        db.close()

    def test_meena_bazar_ingestion_pipeline_run(self, test_db: Session):
        normalizer = CommodityNormalizer()
        pipeline = IngestionPipeline(db=test_db, normalizer=normalizer)
        collector = MeenaBazarCollector(enable_network=False)

        report = pipeline.run_collector(collector)

        assert report.total_harvested > 0
        assert report.inserted > 0
        assert report.source_code == "MEENA_BAZAR_RETAIL"

        # Verify Source entity
        source = test_db.scalars(select(Source).where(Source.code == "MEENA_BAZAR_RETAIL")).first()
        assert source is not None
        assert source.name == "Meena Bazar Online"

        # Verify PriceObservation entities
        observations = list(test_db.scalars(select(PriceObservation).where(PriceObservation.source_id == source.id)).all())
        assert len(observations) > 0

        # Verify normalized pricing for 500g Beef pack (412.5 BDT / 0.5kg = 825.0 BDT/kg)
        beef_comm = test_db.scalars(select(Commodity).where(Commodity.canonical_name == "Beef (Local with Bone)")).first()
        beef_obs = test_db.scalars(
            select(PriceObservation).where(
                PriceObservation.commodity_id == beef_comm.id,
                PriceObservation.source_id == source.id,
            )
        ).first()
        assert beef_obs is not None
        assert beef_obs.normalized_price == 825.0
        assert beef_obs.normalized_unit == "kg"
