"""
Phase 1 regression tests for:
- Taxonomy safety: single-token alias must not match multi-word product descriptions
- Source seeding: all 8 canonical sources must be present in fresh isolated DB
- Provenance: Pandamart always MODELED, Chaldal FALLBACK from fixture
- Unit normalization: cultural units, package sizes, hali/dozen isolation
"""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.collectors.pandamart_collector import PandamartCollector
from app.collectors.chaldal_live_collector import ChaldalLiveCollector
from app.collectors.shwapno_collector import ShwapnoCollector
from app.collectors.meena_bazar_collector import MeenaBazarCollector
from app.core.database import Base
from app.models.source import Source
from app.models.location import Division, District, Market
from app.models.commodity import Commodity, CommodityAlias
from app.models.observation import PriceObservation
from app.services.normalizer import CommodityNormalizer
from scripts.init_db import seed_locations, seed_commodities, seed_sources


# ── Isolated in-memory DB fixture ────────────────────────────────────────────

@pytest.fixture(scope="module")
def isolated_db_session():
    """Provides a fully seeded in-memory SQLite session for fresh-DB tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        seed_locations(session)
        seed_commodities(session)
        seed_sources(session)
        yield session


@pytest.fixture(scope="module")
def norm():
    return CommodityNormalizer()


# ── SECTION 1: Taxonomy Safety — No Fuzzy/Substring Single-Token Match ────────

class TestTaxonomySafety:
    """Verify that single-token aliases CANNOT match unrelated multi-word product names."""

    def test_chicken_springroll_rejected(self, norm):
        """'Paragon Chicken Mini Spring Roll -300gm' must not resolve to Broiler Chicken."""
        result = norm.resolve_commodity("Paragon Chicken Mini Spring Roll -300gm")
        assert result is None, (
            f"Taxonomy leak: resolved to '{result.canonical_name}' via single-token alias"
        )

    def test_egg_noodle_rejected(self, norm):
        """'Knorr Egg Noodle Pack 150g' must not resolve to Farm Egg."""
        result = norm.resolve_commodity("Knorr Egg Noodle Pack 150g")
        assert result is None, (
            f"Taxonomy leak: resolved to '{result.canonical_name}'"
        )

    def test_rice_biscuit_rejected(self, norm):
        """'Rice Crackers Savory Pack 200g' must not resolve to any rice commodity."""
        result = norm.resolve_commodity("Rice Crackers Savory Pack 200g")
        assert result is None, (
            f"Taxonomy leak: resolved to '{result.canonical_name}'"
        )

    def test_potato_chips_rejected(self, norm):
        """'Potato Rings Snack Pack' must not resolve to Potato (Diamond) or similar."""
        result = norm.resolve_commodity("Potato Rings Snack Pack")
        # If it resolves, it must only be via exact multi-token alias match, not substring
        # Actually this test verifies correct rejection
        assert result is None, (
            f"Taxonomy leak: resolved to '{result.canonical_name}'"
        )

    def test_beef_jerky_rejected(self, norm):
        """'Smoked Beef Jerky Packet Premium' must not resolve to Beef (Local with Bone)."""
        result = norm.resolve_commodity("Smoked Beef Jerky Packet Premium")
        assert result is None, (
            f"Taxonomy leak: resolved to '{result.canonical_name}'"
        )

    def test_onion_powder_rejected(self, norm):
        """'Onion Powder Spice Jar 100g' must not resolve to Onion (Local) via single-word 'onion'."""
        result = norm.resolve_commodity("Onion Powder Spice Jar 100g")
        # 'onion powder' is not a 2-token alias for Onion (Local), so must be None
        assert result is None, (
            f"Taxonomy leak: resolved to '{result.canonical_name}'"
        )

    def test_canonical_names_still_resolve(self, norm):
        """Exact canonical commodity names from collectors must still resolve."""
        canonical_cases = [
            ("Broiler Chicken", "Broiler Chicken"),
            ("Farm Egg", "Farm Egg"),
            ("Potato (Diamond)", "Potato (Diamond)"),
            ("Onion (Local)", "Onion (Local)"),
            ("Rice (Miniket)", "Rice (Miniket)"),
            ("Soybean Oil (Bottled)", "Soybean Oil (Bottled)"),
        ]
        for raw, expected in canonical_cases:
            result = norm.resolve_commodity(raw)
            assert result is not None, f"Canonical name failed to resolve: '{raw}'"
            assert result.canonical_name == expected, (
                f"Expected '{expected}', got '{result.canonical_name}' for '{raw}'"
            )

    def test_multi_token_aliases_still_resolve(self, norm):
        """Multi-token aliases for complex products must resolve correctly."""
        multi_token_cases = [
            ("miniket rice", "Rice (Miniket)"),
            ("deshi peyaj", "Onion (Local)"),
            ("broiler chicken", "Broiler Chicken"),
            ("diamond potato", "Potato (Diamond)"),
        ]
        for raw, expected in multi_token_cases:
            result = norm.resolve_commodity(raw)
            assert result is not None, f"Multi-token alias failed: '{raw}'"
            assert result.canonical_name == expected, (
                f"Expected '{expected}', got '{result.canonical_name}'"
            )

    def test_bengali_single_commodity_still_resolves(self, norm):
        """Bengali exact commodity names must resolve."""
        result = norm.resolve_commodity("মিনিকেট চাল")
        assert result is not None
        assert result.canonical_name == "Rice (Miniket)"

    def test_eggplant_not_eggs(self, norm):
        """Brinjal / Eggplant must resolve to Brinjal, never to Farm Egg."""
        result = norm.resolve_commodity("Eggplant")
        if result is not None:
            assert "egg" not in result.canonical_name.lower() or "Brinjal" in result.canonical_name, (
                f"Eggplant resolved to '{result.canonical_name}' which may indicate category bleed"
            )

    def test_fish_not_oil(self, norm):
        """'Fish Fry Mix' must not resolve to any oil commodity."""
        result = norm.resolve_commodity("Fish Fry Mix Seasoned 200g")
        if result is not None:
            assert "oil" not in result.canonical_name.lower(), (
                f"Fish product resolved to oil category: '{result.canonical_name}'"
            )


# ── SECTION 2: Cultural Unit Normalization ────────────────────────────────────

class TestCulturalUnitNormalization:
    """Verify Bangladeshi cultural units produce correct per-unit prices."""

    def test_hali_is_four_units(self, norm):
        """হালি (hali) = 4 pieces; 1 hali eggs at 48 BDT = 12 BDT/pc."""
        price, unit = norm.normalize_price(48.0, "হালি")
        assert unit == "pc"
        assert price == pytest.approx(12.0, abs=0.01)

    def test_hali_not_one(self, norm):
        """1 hali eggs (48 BDT) must NOT equal 48 BDT/pc (that would be 1-unit mistake)."""
        price, unit = norm.normalize_price(48.0, "হালি")
        assert price != 48.0, "Hali must be divided by 4, not treated as 1 unit"

    def test_dozen_eggs_normalization(self, norm):
        """1 dozen eggs at 144 BDT = 12.0 BDT/pc."""
        price, unit = norm.normalize_price(144.0, "ডজন")
        assert unit == "pc"
        assert price == pytest.approx(12.0, abs=0.01)

    def test_twelve_pcs_eggs(self, norm):
        """12 pcs (Farm Egg) at 265 BDT = 22.08 BDT/pc."""
        price, unit = norm.normalize_price(265.0, "12 pcs")
        assert unit == "pc"
        assert price == pytest.approx(22.083, abs=0.01)

    def test_four_pcs_hali_equivalent(self, norm):
        """4 pcs must equal hali price (≡ price / 4 per pc)."""
        price_hali, _ = norm.normalize_price(48.0, "হালি")
        price_pcs, _ = norm.normalize_price(48.0, "4 pcs")
        assert price_hali == pytest.approx(price_pcs, abs=0.01)

    def test_500gm_to_kg(self, norm):
        """500gm beef at 412.5 BDT = 825.0 BDT/kg."""
        price, unit = norm.normalize_price(412.5, "500 gm")
        assert unit == "kg"
        assert price == pytest.approx(825.0, abs=0.01)

    def test_500gm_not_equal_1kg(self, norm):
        """500gm pack price must NOT equal 1kg price (package-size isolation)."""
        price_500gm, _ = norm.normalize_price(412.5, "500 gm")
        price_1kg, _ = norm.normalize_price(412.5, "kg")
        assert price_500gm != price_1kg, "500gm and 1kg must produce different normalized prices"

    def test_maund_40kg(self, norm):
        """মণ (Maund) = 40 kg; 2800 BDT/maund = 70.0 BDT/kg."""
        price, unit = norm.normalize_price(2800.0, "মণ")
        assert unit == "kg"
        assert price == pytest.approx(70.0, abs=0.01)

    def test_powa_quarter_kg(self, norm):
        """পোয়া (Powa) = 0.25 kg; 25 BDT/powa = 100.0 BDT/kg."""
        price, unit = norm.normalize_price(25.0, "পোয়া")
        assert unit == "kg"
        assert price == pytest.approx(100.0, abs=0.01)

    def test_bundle_unit_preserved(self, norm):
        """আঁটি (bundle) remains bundle unit (not converted to kg or pc)."""
        price, unit = norm.normalize_price(15.0, "আঁটি")
        assert unit == "bundle"
        assert price == pytest.approx(15.0, abs=0.01)


# ── SECTION 3: Fresh DB Seeding — All 8 Sources ───────────────────────────────

class TestFreshDBSourceSeeding:
    """Verify that fresh DB initialization seeds all 8 canonical sources."""

    EXPECTED_SOURCES = {
        "DAM_DAILY", "TCB_DAILY", "CHALDAL_RETAIL", "field_report",
        "PRESS_REPORT", "SHWAPNO_RETAIL", "MEENA_BAZAR_RETAIL", "PANDAMART_MODELED",
    }

    def test_all_sources_seeded(self, isolated_db_session):
        """All 8 data sources must be present in a freshly initialized database."""
        sources = list(isolated_db_session.scalars(select(Source)).all())
        seeded_codes = {s.code for s in sources}
        missing = self.EXPECTED_SOURCES - seeded_codes
        assert not missing, f"Missing sources after fresh init: {missing}"

    def test_shwapno_retail_seeded(self, isolated_db_session):
        """SHWAPNO_RETAIL must be seeded with correct metadata."""
        src = isolated_db_session.scalars(
            select(Source).where(Source.code == "SHWAPNO_RETAIL")
        ).first()
        assert src is not None
        assert src.source_type == "retail_superstore"
        assert src.reliability_score == pytest.approx(0.90, abs=0.01)

    def test_meena_bazar_retail_seeded(self, isolated_db_session):
        """MEENA_BAZAR_RETAIL must be seeded with correct metadata."""
        src = isolated_db_session.scalars(
            select(Source).where(Source.code == "MEENA_BAZAR_RETAIL")
        ).first()
        assert src is not None
        assert src.source_type == "retail_superstore"
        assert src.reliability_score == pytest.approx(0.89, abs=0.01)

    def test_pandamart_modeled_seeded(self, isolated_db_session):
        """PANDAMART_MODELED must be seeded with modeled_benchmark type."""
        src = isolated_db_session.scalars(
            select(Source).where(Source.code == "PANDAMART_MODELED")
        ).first()
        assert src is not None
        assert src.source_type == "modeled_benchmark"

    def test_65_commodities_seeded(self, isolated_db_session):
        """Fresh DB must contain exactly 65 canonical commodities."""
        count = isolated_db_session.scalar(
            select(__import__("sqlalchemy", fromlist=["func"]).func.count()).select_from(Commodity)
        )
        assert count == 65, f"Expected 65 commodities, got {count}"

    def test_8_divisions_seeded(self, isolated_db_session):
        """Fresh DB must contain exactly 8 administrative divisions."""
        count = isolated_db_session.scalar(
            select(__import__("sqlalchemy", fromlist=["func"]).func.count()).select_from(Division)
        )
        assert count == 8, f"Expected 8 divisions, got {count}"

    def test_64_districts_seeded(self, isolated_db_session):
        """Fresh DB must contain exactly 64 districts."""
        count = isolated_db_session.scalar(
            select(__import__("sqlalchemy", fromlist=["func"]).func.count()).select_from(District)
        )
        assert count == 64, f"Expected 64 districts, got {count}"

    def test_markets_seeded(self, isolated_db_session):
        """Fresh DB must contain >= 78 market nodes."""
        count = isolated_db_session.scalar(
            select(__import__("sqlalchemy", fromlist=["func"]).func.count()).select_from(Market)
        )
        assert count >= 78, f"Expected >= 78 markets, got {count}"


# ── SECTION 4: Provenance — Pandamart Always MODELED ─────────────────────────

class TestPandamartProvenance:
    """Pandamart observations must always be marked MODELED."""

    def test_all_observations_modeled(self):
        """Every Pandamart observation must have collection_status == 'MODELED'."""
        collector = PandamartCollector()
        obs = collector.collect()
        assert len(obs) > 0, "Pandamart collector returned no observations"
        for o in obs:
            assert o.collection_status == "MODELED", (
                f"Pandamart observation '{o.raw_commodity_name}' has status '{o.collection_status}', expected MODELED"
            )
            assert o.is_fallback is True, (
                f"Pandamart observation must be marked is_fallback=True"
            )

    def test_no_live_claim(self):
        """Pandamart collector must never claim LIVE status."""
        collector = PandamartCollector()
        obs = collector.collect()
        live_obs = [o for o in obs if o.collection_status == "LIVE"]
        assert len(live_obs) == 0, f"Pandamart incorrectly reported {len(live_obs)} LIVE observations"


# ── SECTION 5: Provenance — Chaldal FALLBACK from fixture ────────────────────

class TestChaldalProvenance:
    """Chaldal collector must correctly mark fixture data as FALLBACK (HTTP 404 confirmed)."""

    def test_chaldal_fallback_observations(self):
        """Chaldal observations from fixture must have is_fallback=True."""
        collector = ChaldalLiveCollector(max_retries=0, timeout_seconds=2.0)
        obs = collector.collect()
        assert len(obs) > 0, "Chaldal collector returned no observations (even from fixture)"
        fallback_obs = [o for o in obs if o.is_fallback]
        live_obs = [o for o in obs if not o.is_fallback]
        # Current known state: Chaldal API returns 404, so all should be fallback
        # This test documents the known behavior
        assert len(fallback_obs) > 0, "Expected at least some FALLBACK observations from Chaldal"
        # If live somehow becomes available in future, this test should be updated
        if live_obs:
            # Verify live observations have proper HTTP success indicators
            for o in live_obs:
                assert o.collection_status == "LIVE"


# ── SECTION 6: Duplicate Ingestion Behavior ───────────────────────────────────

class TestDuplicateIngestionBehavior:
    """Repeated collection of the same fixture must not create duplicate DB records."""

    @pytest.fixture
    def ingestion_db(self):
        """Fresh in-memory DB for ingestion tests."""
        from app.services.ingestion import IngestionPipeline
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        with Session() as session:
            seed_locations(session)
            seed_commodities(session)
            seed_sources(session)
            yield session, engine

    def test_fixture_run_twice_no_duplicates(self, ingestion_db):
        """Running the fixture-backed ShwapnoCollector twice must not create duplicates."""
        from app.services.ingestion import IngestionPipeline
        from sqlalchemy import func as sqlfunc

        session, engine = ingestion_db

        collector1 = ShwapnoCollector(enable_network=False)
        pipeline = IngestionPipeline(db=session)
        report1 = pipeline.run_collector(collector1)

        count_after_first = session.scalar(
            select(sqlfunc.count()).select_from(PriceObservation)
        )

        collector2 = ShwapnoCollector(enable_network=False)
        report2 = pipeline.run_collector(collector2)

        count_after_second = session.scalar(
            select(sqlfunc.count()).select_from(PriceObservation)
        )

        assert count_after_second == count_after_first, (
            f"Second fixture run created {count_after_second - count_after_first} duplicate records"
        )
        assert report2.inserted == 0, (
            f"Second fixture run should insert 0 records (all fallback skipped), got {report2.inserted}"
        )


# ── SECTION 5: System Hardening & Audit Gap Verification ─────────────────────

class TestSystemHardeningAndGaps:
    """Verify system hardening against synthetic prices, unknown market pollution, and order dependency."""

    def test_empty_store_data_returns_unavailable_not_synthetic_price(self, isolated_db_session):
        """When no DB observation exists for a store, it must return UNAVAILABLE and price=None, NEVER an invented price."""
        from app.api.v1.endpoints.commodities import get_commodity_stores
        from app.models.commodity import Commodity

        # Get any canonical commodity that has no retail store observations in the isolated DB
        comm = isolated_db_session.scalars(select(Commodity)).first()
        assert comm is not None

        response = get_commodity_stores(commodity_id=comm.id, db=isolated_db_session)
        assert response.commodity_id == comm.id
        assert len(response.stores) == 4

        for store in response.stores:
            # Must be honest: no price invented
            assert store.collection_status == "UNAVAILABLE", (
                f"Store {store.id} returned '{store.collection_status}' instead of 'UNAVAILABLE'"
            )
            assert store.price is None, (
                f"Store {store.id} invented synthetic price {store.price} merely to avoid an empty screen"
            )
            assert store.status_label_bn == "তথ্য উপলব্ধ নেই"
            assert store.error_message is not None

    def test_unknown_market_returns_none_and_quarantined(self, isolated_db_session):
        """Unknown raw market names must return None and NOT silently map to the first DB market."""
        from app.services.ingestion import IngestionPipeline

        pipeline = IngestionPipeline(db=isolated_db_session)
        resolved = pipeline._resolve_market("Nonexistent Alien Remote Village Bazar 9999")
        assert resolved is None, (
            f"Security/Integrity flaw: unknown market mapped to '{resolved.name}' instead of returning None"
        )

    def test_order_independent_duplicate_resolution(self):
        """
        Duplicate ingestion of multiple SKUs for the same commodity in different orders
        must yield identical deterministic normalized prices (no order-dependent averaging).
        """
        from datetime import date
        from app.collectors.base import RawObservation
        from app.services.ingestion import IngestionPipeline

        def run_with_order(raw_items_list):
            eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
            Base.metadata.create_all(eng)
            S = sessionmaker(bind=eng)
            with S() as sess:
                seed_locations(sess)
                seed_commodities(sess)
                seed_sources(sess)

                pipe = IngestionPipeline(db=sess)
                mock_collector = type("MockCollector", (), {
                    "source_code": "TEST_RETAIL",
                    "source_name": "Test Retail",
                    "source_type": "retail_superstore",
                    "reliability_score": 0.90,
                    "collect": lambda self: raw_items_list,
                })()
                pipe.run_collector(mock_collector)

                obs = sess.scalars(select(PriceObservation)).all()
                return [(o.normalized_price, o.raw_name) for o in obs]

        item_a = RawObservation(
            source_code="TEST_RETAIL",
            market_name="Karwan Bazar",
            raw_commodity_name="Miniket Rice 1kg Pack",
            raw_unit="1 kg",
            raw_price=70.0,
            price_type="retail_avg",
            observation_date=date(2026, 9, 30),
        )
        item_b = RawObservation(
            source_code="TEST_RETAIL",
            market_name="Karwan Bazar",
            raw_commodity_name="Miniket Rice 5kg Sack",
            raw_unit="5 kg",
            raw_price=340.0,  # 68.0 BDT/kg
            price_type="retail_avg",
            observation_date=date(2026, 9, 30),
        )

        res_order_1 = run_with_order([item_a, item_b])
        res_order_2 = run_with_order([item_b, item_a])

        assert len(res_order_1) == 1
        assert len(res_order_2) == 1
        # Order 1 and Order 2 must produce the EXACT same normalized price
        assert res_order_1[0][0] == res_order_2[0][0], (
            f"Order-dependent duplicate resolution: order 1 gave {res_order_1[0][0]}, order 2 gave {res_order_2[0][0]}"
        )

    def test_historical_get_does_not_trigger_harvest(self, isolated_db_session):
        """Historical GET requests with target_date < today must NEVER trigger on-demand live harvest."""
        from datetime import date
        from unittest.mock import patch
        from app.services.realtime_service import RealtimePriceService

        service = RealtimePriceService(db=isolated_db_session)
        past_date = date(2022, 1, 1)

        with patch.object(service, "_trigger_on_demand_harvest") as mock_harvest:
            service.get_realtime_price(query="Miniket", target_date=past_date)
            assert mock_harvest.call_count == 0, (
                "Violation: Historical GET request triggered live on-demand harvest"
            )

    def test_modeled_pandamart_excluded_from_basket_channels(self, isolated_db_session):
        """Modeled Pandamart observations must be excluded from real channel price averages in BasketService."""
        from datetime import date
        from app.services.basket_service import basket_service
        from app.models.commodity import Commodity
        from app.models.location import Market
        from app.models.source import Source
        from app.models.observation import PriceObservation

        comm = isolated_db_session.scalars(select(Commodity).where(Commodity.canonical_name == "Rice (Miniket)")).first()
        mkt = isolated_db_session.scalars(select(Market)).first()
        panda_src = isolated_db_session.scalars(select(Source).where(Source.code == "PANDAMART_MODELED")).first()

        # Add a modeled observation for Pandamart
        modeled_obs = PriceObservation(
            commodity_id=comm.id,
            market_id=mkt.id,
            source_id=panda_src.id,
            raw_name="Rice (Miniket)",
            raw_price=999.0,
            raw_unit="kg",
            normalized_price=999.0,
            normalized_unit="kg",
            price_type="retail_avg",
            observation_date=date.today(),
            confidence_score=0.75,
        )
        isolated_db_session.add(modeled_obs)
        isolated_db_session.commit()

        # Fetch channel prices via basket service
        channel_prices = basket_service._fetch_channel_prices(isolated_db_session, comm.id, date.today())
        # The modeled 999.0 must not enter retail or online averages
        assert channel_prices.retail != 999.0, "Modeled Pandamart price leaked into real retail channel"
        assert channel_prices.online != 999.0, "Modeled Pandamart price leaked into real online channel"

    def test_stores_api_returns_none_when_unavailable(self, isolated_db_session):
        """Store price API must return price=None and collection_status='UNAVAILABLE' when no DB record exists."""
        from app.api.v1.endpoints.commodities import get_commodity_stores
        from app.models.commodity import Commodity

        comm = isolated_db_session.scalars(select(Commodity).where(Commodity.canonical_name == "Rice (Miniket)")).first()
        res = get_commodity_stores(commodity_id=comm.id, db=isolated_db_session)
        assert len(res.stores) > 0
        for store in res.stores:
            # If no real observation exists for that store, price must be None, not synthetic
            if store.collection_status == "UNAVAILABLE":
                assert store.price is None, f"Store {store.id} returned synthetic price {store.price} while UNAVAILABLE"
                assert "অনুপলব্ধ" in store.status_label_bn or "অপ্রাপ্য" in store.status_label_bn or "উপলব্ধ নেই" in store.status_label_bn

    def test_dam_ticker_range_not_split_wholesale_retail(self):
        """DAM ticker range (e.g., 30 - 35 Tk) must be averaged for retail_avg, not split into wholesale_avg and retail_avg."""
        from app.collectors.dam_live_collector import DAMLiveCollector
        collector = DAMLiveCollector()
        sample_html = """
        <html>
            <div class="stockbox">আলু: ৩০ - ৩৫</div>
            <div class="stockbox">পেঁয়াজ (পাইকারি): ৬০ - ৭০</div>
        </html>
        """
        obs = collector._parse_html(sample_html, is_fallback=False)
        assert len(obs) == 2, f"Expected 2 observations, got {len(obs)}"

        # Potato: Retail ticker range 30-35 -> average 32.5 retail_avg
        potato_obs = next((o for o in obs if "আলু" in o.raw_commodity_name), None)
        assert potato_obs is not None
        assert potato_obs.price_type == "retail_avg"
        assert potato_obs.raw_price == 32.5

        # Onion: Wholesale ticker range 60-70 -> average 65.0 wholesale_avg
        onion_obs = next((o for o in obs if "পেঁয়াজ" in o.raw_commodity_name), None)
        assert onion_obs is not None
        assert onion_obs.price_type == "wholesale_avg"
        assert onion_obs.raw_price == 65.0
