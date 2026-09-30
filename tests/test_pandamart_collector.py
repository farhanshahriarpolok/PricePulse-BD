"""
Deterministic unit and integration tests for PandamartCollector.
Covers:
- Verification of transparent MODELED contract
- Preservation of is_fallback=True
- Disclosed technical access limitations (Cloudflare Bot Management 403)
- Ingestion and persistence via IngestionPipeline
- Telemetry recording in SourceHealthService
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.collectors.base import CollectionStatus
from app.collectors.pandamart_collector import PandamartCollector
from app.core.database import Base
from app.models.commodity import Commodity
from app.models.location import Division, District, Market
from app.models.observation import PriceObservation
from app.models.source import Source
from app.services.ingestion import IngestionPipeline
from app.services.normalizer import CommodityNormalizer
from app.services.source_health import source_health_service


class TestPandamartCollectorUnit:
    """Deterministic tests for Pandamart collector and modeled contract."""

    def test_pandamart_modeled_harvest(self):
        collector = PandamartCollector()
        observations = collector.collect()

        assert len(observations) > 0
        for obs in observations:
            assert obs.source_code == "PANDAMART_MODELED"
            assert obs.market_name == "Pandamart Darkstore Network"
            assert obs.raw_price > 0.0
            assert obs.is_fallback is True
            assert obs.collection_status == CollectionStatus.MODELED.value
            assert "Cloudflare" in (obs.error_message or "")
            assert obs.source_url == "https://foodpanda.com.bd/pandamart"

    def test_pandamart_telemetry_recording(self):
        collector = PandamartCollector()
        collector.collect()

        telemetry = source_health_service.get_source_status("PANDAMART_MODELED")
        assert telemetry is not None
        assert telemetry["status"] == "DEGRADED"
        assert telemetry["is_fallback"] is True
        assert "Cloudflare" in (telemetry["last_error"] or "")


class TestPandamartIngestionPersistence:
    """Integration test verifying Pandamart modeled persistence into SQLite."""

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
            ("Onion (Local)", "দেশি পেঁয়াজ", "Vegetables", "kg"),
            ("Potato (Diamond)", "আলু (ডায়মন্ড)", "Vegetables", "kg"),
            ("Farm Egg", "ফার্মের ডিম", "Eggs & Milk", "pc"),
            ("Rice (Miniket)", "মিনিকেট চাল", "Rice & Grains", "kg"),
            ("Soybean Oil (Bottled)", "সয়াবিন তেল (বোতল)", "Oil & Spices", "liter"),
            ("Green Chilli", "কাঁচা মরিচ", "Vegetables", "kg"),
        ]
        for cname, bname, cat, unit in commodities_to_seed:
            comm = Commodity(canonical_name=cname, bangla_name=bname, category=cat, default_unit=unit)
            db.add(comm)

        db.commit()
        yield db
        db.close()

    def test_pandamart_ingestion_pipeline_run(self, test_db: Session):
        normalizer = CommodityNormalizer()
        pipeline = IngestionPipeline(db=test_db, normalizer=normalizer)
        collector = PandamartCollector()

        report = pipeline.run_collector(collector)

        assert report.total_harvested > 0
        assert report.inserted > 0
        assert report.source_code == "PANDAMART_MODELED"

        source = test_db.scalars(select(Source).where(Source.code == "PANDAMART_MODELED")).first()
        assert source is not None
        assert source.name == "Pandamart Express Grocery"

        observations = list(test_db.scalars(select(PriceObservation).where(PriceObservation.source_id == source.id)).all())
        assert len(observations) > 0
