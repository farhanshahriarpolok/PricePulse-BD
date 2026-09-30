"""
Deterministic unit and integration tests for ShwapnoCollector.
Covers:
- Successful harvest from mock / fixture
- Canonical commodity mapping accuracy
- Cultural unit normalization and package-size calculations
- Out-of-stock and missing/malformed price filtering
- Duplicate product deduplication
- Network failure & graceful fallback to local fixture
- Database persistence via IngestionPipeline
- SourceHealth telemetry updates
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.collectors.base import CollectionStatus
from app.collectors.shwapno_collector import ShwapnoCollector, EXPLICIT_COMMODITY_MAPPINGS
from app.core.database import Base
from app.models.commodity import Commodity, CommodityAlias
from app.models.location import Division, District, Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.services.ingestion import IngestionPipeline
from app.services.normalizer import CommodityNormalizer
from app.services.source_health import source_health_service


@pytest.fixture
def mock_shwapno_payload():
    return {
        "products": [
            {
                "name": "Fulcopy (Cauliflower)",
                "sku": "2902791",
                "price": {"priceValue": 75.0, "unitPriceValue": 75.0},
                "unit": "Piece",
                "stock": "InStock",
            },
            {
                "name": "Kacha Morich (Chilli Green)",
                "sku": "2900281",
                "price": {"priceValue": 160.0, "unitPriceValue": 160.0},
                "unit": "1 kg",
                "stock": "InStock",
            },
            {
                "name": "Egg Loose",
                "sku": "2900285",
                "price": {"priceValue": 12.75, "unitPriceValue": 12.75},
                "unit": "Piece",
                "stock": "InStock",
            },
            {
                "name": "ACI Pure Fortified Miniket Rice 5kg",
                "sku": "2900286",
                "price": {"priceValue": 340.0, "unitPriceValue": 68.0},
                "unit": "5 kg",
                "stock": "InStock",
            },
            {
                "name": "Rupchanda Fortified Soyabean Oil 5Ltr",
                "sku": "2900287",
                "price": {"priceValue": 950.0, "unitPriceValue": 190.0},
                "unit": "5 liter",
                "stock": "InStock",
            },
            # Out of stock item -> should be ignored
            {
                "name": "Tomato Local",
                "sku": "2900290",
                "price": {"priceValue": 80.0},
                "unit": "1 kg",
                "stock": "OutOfStock",
            },
            # Malformed item (zero price) -> should be ignored
            {
                "name": "Badhakopi (Cabbage)",
                "sku": "2900291",
                "price": {"priceValue": 0.0},
                "unit": "Piece",
                "stock": "InStock",
            },
            # Unmapped item -> should be ignored (no guessing!)
            {
                "name": "Imported Gourmet French Cheese 200g",
                "sku": "9999999",
                "price": {"priceValue": 850.0},
                "unit": "Piece",
                "stock": "InStock",
            },
            # Duplicate item -> should be deduplicated
            {
                "name": "Egg Loose",
                "sku": "2900285-dup",
                "price": {"priceValue": 13.0},
                "unit": "Piece",
                "stock": "InStock",
            },
        ]
    }


class TestShwapnoCollectorUnit:
    """Deterministic tests for Shwapno collector logic and mapping."""

    def test_fixture_harvest_success(self):
        collector = ShwapnoCollector(enable_network=False)
        observations = collector.collect()

        assert len(observations) > 0
        for obs in observations:
            assert obs.source_code == "SHWAPNO_RETAIL"
            assert obs.market_name == "Shwapno Retail Hub"
            assert obs.raw_price > 0.0
            assert obs.is_fallback is True
            assert obs.collection_status == CollectionStatus.FALLBACK.value
            assert obs.source_url == "https://www.shwapno.com"

    def test_canonical_mapping_accuracy(self, mock_shwapno_payload):
        collector = ShwapnoCollector(enable_network=True)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_shwapno_payload
            mock_get.return_value = mock_resp

            observations = collector.collect()
            mapped_names = {obs.raw_commodity_name for obs in observations}

            assert "Cauliflower" in mapped_names
            assert "Green Chilli" in mapped_names
            assert "Farm Egg" in mapped_names
            assert "Rice (Miniket)" in mapped_names
            assert "Soybean Oil (Bottled)" in mapped_names
            # Unmapped French cheese must NEVER be mapped
            assert "French Cheese" not in mapped_names
            # Out of stock and zero-price items must be excluded
            assert "Tomato" not in mapped_names
            assert "Cabbage" not in mapped_names

    def test_deduplication_in_harvest(self, mock_shwapno_payload):
        collector = ShwapnoCollector(enable_network=True)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_shwapno_payload
            mock_get.return_value = mock_resp

            observations = collector.collect()
            egg_obs = [o for o in observations if o.raw_commodity_name == "Farm Egg"]
            assert len(egg_obs) == 1

    def test_live_network_failure_falls_back_cleanly(self):
        collector = ShwapnoCollector(enable_network=True, max_retries=1)

        with patch("httpx.Client.get", side_effect=httpx.ConnectTimeout("Connection timed out")):
            observations = collector.collect()

            assert len(observations) > 0
            for obs in observations:
                assert obs.is_fallback is True
                assert obs.collection_status == CollectionStatus.FALLBACK.value
                assert "ConnectTimeout" in (obs.error_message or "")

    def test_http_500_error_falls_back_cleanly(self):
        collector = ShwapnoCollector(enable_network=True, max_retries=1)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_get.return_value = mock_resp

            observations = collector.collect()
            assert len(observations) > 0
            for obs in observations:
                assert obs.is_fallback is True
                assert obs.collection_status == CollectionStatus.FALLBACK.value

    def test_source_health_recording(self, mock_shwapno_payload):
        collector = ShwapnoCollector(enable_network=True)

        with patch("httpx.Client.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_shwapno_payload
            mock_get.return_value = mock_resp

            collector.collect()
            telemetry = source_health_service.get_source_status("SHWAPNO_RETAIL")
            assert telemetry is not None
            assert telemetry["status"] == "HEALTHY"
            assert telemetry["is_fallback"] is False



class TestShwapnoIngestionPersistence:
    """Integration test verifying ShwapnoCollector persistence into SQLite via IngestionPipeline."""

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
            ("Cauliflower", "ফুলকপি", "Vegetables", "pc"),
            ("Green Chilli", "কাঁচা মরিচ", "Vegetables", "kg"),
            ("Farm Egg", "ফার্মের ডিম", "Eggs & Milk", "pc"),
            ("Rice (Miniket)", "মিনিকেট চাল", "Rice & Grains", "kg"),
            ("Soybean Oil (Bottled)", "সয়াবিন তেল (বোতল)", "Oil & Spices", "liter"),
            ("Salt (Iodized)", "আয়োডিনযুক্ত লবণ", "Oil & Spices", "kg"),
            ("Sugar (Refined White)", "সাদা চিনি", "Oil & Spices", "kg"),
            ("Cucumber", "শসা", "Vegetables", "kg"),
            ("Papaya (Green)", "কাঁচা পেঁপে", "Vegetables", "kg"),
            ("Cabbage", "বাঁধাকপি", "Vegetables", "pc"),
        ]
        for cname, bname, cat, unit in commodities_to_seed:
            comm = Commodity(canonical_name=cname, bangla_name=bname, category=cat, default_unit=unit)
            db.add(comm)

        db.commit()
        yield db
        db.close()

    def test_shwapno_ingestion_pipeline_run(self, test_db: Session):
        normalizer = CommodityNormalizer()
        pipeline = IngestionPipeline(db=test_db, normalizer=normalizer)
        collector = ShwapnoCollector(enable_network=False)

        report = pipeline.run_collector(collector)

        assert report.total_harvested > 0
        assert report.inserted > 0
        assert report.source_code == "SHWAPNO_RETAIL"

        # Verify Source entity
        source = test_db.scalars(select(Source).where(Source.code == "SHWAPNO_RETAIL")).first()
        assert source is not None
        assert source.name == "Shwapno Superstore"

        # Verify PriceObservation entities
        observations = list(test_db.scalars(select(PriceObservation).where(PriceObservation.source_id == source.id)).all())
        assert len(observations) > 0

        # Verify normalized pricing for 5kg Rice pack (460 BDT / 5kg = 92.0 BDT/kg)
        rice_comm = test_db.scalars(select(Commodity).where(Commodity.canonical_name == "Rice (Miniket)")).first()
        rice_obs = test_db.scalars(
            select(PriceObservation).where(
                PriceObservation.commodity_id == rice_comm.id,
                PriceObservation.source_id == source.id,
            )
        ).first()
        assert rice_obs is not None
        assert rice_obs.normalized_price == 92.0
        assert rice_obs.normalized_unit == "kg"

