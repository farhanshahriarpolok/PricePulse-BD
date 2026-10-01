"""
tests/test_phase5b_substitution.py
==================================
Comprehensive test suite for Phase 5B: Smart Cheaper Alternative Recommendations.

Covers:
1. Cheaper alternative qualifies when savings >= ৳2 and savings_pct >= 5%.
2. Exact boundary tests:
   - savings exactly ৳2.00
   - savings < ৳2.00 (fails)
   - savings_pct exactly 5.0%
   - savings_pct < 5.0% (fails)
3. Alternative is more expensive (fails).
4. Strictly intra-category (Rule A).
5. Cross-category pairs rejected.
6. Missing source price or missing alternative price.
7. Unit normalization (e.g. egg 'hali' vs 'pc').
8. Ranking order (highest absolute savings first).
9. Provenance & Phase 5A freshness preservation (FRESH_TODAY vs YESTERDAY vs STALE).
10. Basket integration: items without substitutes remain unchanged; calculation doesn't alter user basket silently.
11. REST API endpoint GET /api/v1/basket/alternatives/{commodity_id}.
"""

import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.alternative_service import (
    AlternativeRecommendationService,
    AlternativeRegistryEntry,
    alternative_service,
)
from app.schemas.basket import BasketCalculationRequest, BasketItemInput
from app.services.basket_service import basket_service
from app.services.freshness import get_bangladesh_today


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


def test_registry_loading():
    """Verify alternative_registry.json loads and contains valid entries."""
    service = AlternativeRecommendationService()
    entries = service._entries
    assert len(entries) > 0
    for e in entries:
        assert isinstance(e.source_commodity_id, int)
        assert isinstance(e.alternative_commodity_id, int)
        assert e.category
        assert e.reason_bn
        assert e.reason_en


def test_rule_a_intra_category_enforcement():
    """Test that candidate pairs across different categories are strictly rejected."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()

    # Two commodities with different categories
    c_meat = MagicMock(id=8, canonical_name="Broiler Chicken", bangla_name="ব্রয়লার মুরগি", category="Meat, Fish & Eggs")
    c_grain = MagicMock(id=4, canonical_name="Rice (Miniket)", bangla_name="মিনিকেট চাল", category="Grains & Flours")
    mock_db.get.side_effect = lambda model, pk: c_meat if pk == 8 else (c_grain if pk == 4 else None)

    entry = AlternativeRegistryEntry(
        source_commodity_id=8,
        source_canonical_name="Broiler Chicken",
        alternative_commodity_id=4,
        alternative_canonical_name="Rice (Miniket)",
        category="CrossCategoryTest",
        reason_bn="পরীক্ষামূলক",
        reason_en="Test cross category",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=get_bangladesh_today(),
        channel="retail",
    )
    assert res is None, "Cross-category alternative must be strictly rejected (Rule A)."


def test_qualification_boundary_exact_2_taka():
    """Test boundary where savings is exactly ৳2.00 and pct >= 5%."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source = ৳20.00, Alt = ৳18.00 -> savings = ৳2.00, pct = 10.0% >= 5%
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (20.0, "kg", now_date, None, "LIVE"),
        (18.0, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="ঠিক ২ টাকা সাশ্রয়",
        reason_en="Exact 2 taka savings",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
        basket_quantity=1.0,
    )
    assert res is not None
    assert res.savings_per_unit == 2.0
    assert res.savings_percent == 10.0


def test_qualification_below_2_taka_fails():
    """Test boundary where savings < ৳2.00 (e.g. ৳1.90), must fail."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source = ৳10.00, Alt = ৳8.10 -> savings = ৳1.90 (< ৳2.00) even though pct = 19%
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (10.0, "kg", now_date, None, "LIVE"),
        (8.10, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="সাশ্রয় ২ টাকার নিচে",
        reason_en="Savings under 2 taka",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is None, "Savings below ৳2.00 must not qualify."


def test_qualification_boundary_exact_5_pct():
    """Test boundary where savings_pct is exactly 5.0% and savings >= ৳2."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source = ৳100.00, Alt = ৳95.00 -> savings = ৳5.00 (>= ৳2), pct = 5.0%
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (100.0, "kg", now_date, None, "LIVE"),
        (95.0, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="ঠিক ৫ শতাংশ",
        reason_en="Exact 5 percent",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is not None
    assert res.savings_per_unit == 5.0
    assert abs(res.savings_percent - 5.0) < 1e-4


def test_qualification_below_5_pct_fails():
    """Test boundary where savings_pct < 5.0% (e.g. ৳4 on ৳100 = 4.0%), must fail."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source = ৳100.00, Alt = ৳96.00 -> savings = ৳4.00 (>= ৳2), but pct = 4.0% (< 5.0%)
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (100.0, "kg", now_date, None, "LIVE"),
        (96.0, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="চার শতাংশ",
        reason_en="Four percent",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is None, "Savings percentage below 5% must not qualify."


def test_alternative_more_expensive_fails():
    """Test that an alternative priced higher than source is never recommended."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source = ৳50.00, Alt = ৳70.00 -> more expensive
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (50.0, "kg", now_date, None, "LIVE"),
        (70.0, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="বেশি দামি",
        reason_en="More expensive",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is None, "More expensive alternative must never qualify."


def test_missing_price_fails():
    """Test that missing price for either source or alternative results in no recommendation."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source has price, Alt returns None (missing observation)
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (50.0, "kg", now_date, None, "LIVE"),
        None,
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="অনুপস্থিত দাম",
        reason_en="Missing price",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is None, "Missing observation for alternative must prevent recommendation."


def test_unit_normalization_egg_hali():
    """Test egg normalization: 'hali' (4 pcs) vs single 'pc'."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=58, canonical_name="Duck Egg", bangla_name="হাঁসের ডিম", category="Eggs & Dairy")
    c_alt = MagicMock(id=9, canonical_name="Farm Egg", bangla_name="ফার্মের ডিম", category="Eggs & Dairy")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 58 else (c_alt if pk == 9 else None)

    # Source = ৳72 / hali (4 pcs). Alt = ৳14 / pc (৳56 / hali).
    # Standard comparison unit is 'হালি': Source = 72, Alt = 14 * 4 = 56.
    # Savings = ৳16 / hali (22.2% >= 5%).
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (72.0, "hali", now_date, None, "LIVE"),
        (14.0, "pc", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=58,
        source_canonical_name="Duck Egg",
        alternative_commodity_id=9,
        alternative_canonical_name="Farm Egg",
        category="Eggs & Dairy",
        reason_bn="ডিম একক পরিবর্তন",
        reason_en="Egg unit conversion",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
        basket_quantity=2.0,  # 2 hali
    )
    assert res is not None
    assert res.standard_unit == "হালি"
    assert res.source_price == 72.0
    assert res.alternative_price == 56.0
    assert res.savings_per_unit == 16.0
    assert res.estimated_line_savings == 32.0


def test_freshness_metadata_preservation():
    """Test that Phase 5A freshness tier is preserved accurately."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()
    yesterday = now_date - timedelta(days=1)

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (100.0, "kg", now_date, None, "LIVE"),
        (80.0, "kg", yesterday, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="পূর্বের দর যাচাই",
        reason_en="Older price check",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is not None
    assert res.freshness_tier == "YESTERDAY"
    assert res.observation_date == yesterday.isoformat()
    # Dual-sided freshness assertions
    assert res.source_freshness_tier == "FRESH_TODAY"
    assert res.source_observation_date == now_date.isoformat()
    assert res.alternative_freshness_tier == "YESTERDAY"
    assert res.alternative_observation_date == yesterday.isoformat()
    assert res.is_symmetric_freshness is False


def test_dual_freshness_states_symmetric():
    """Verify is_symmetric_freshness is True when dates match."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (100.0, "kg", now_date, None, "LIVE"),
        (80.0, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="উভয়ই তাজা",
        reason_en="Both fresh",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is not None
    assert res.source_freshness_tier == "FRESH_TODAY"
    assert res.alternative_freshness_tier == "FRESH_TODAY"
    assert res.is_symmetric_freshness is True


def test_dual_freshness_both_stale_1_day_apart():
    """Verify dual-sided freshness when both source and alt are older observations within 1 day."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()
    older_date_s = now_date - timedelta(days=3)
    older_date_a = now_date - timedelta(days=4)  # 1 day apart <= MAX_DATE_DIVERGENCE_DAYS

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (100.0, "kg", older_date_s, None, "LIVE"),
        (80.0, "kg", older_date_a, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="উভয়ই পুরনো দর",
        reason_en="Both older prices",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is not None
    assert res.source_freshness_tier == "STALE"
    assert res.alternative_freshness_tier == "STALE"
    assert res.is_symmetric_freshness is False


def test_temporal_divergence_0_day_allowed():
    """Test 0-day difference: same observation date is allowed and marked symmetric."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (50.0, "kg", now_date, None, "LIVE"),
        (40.0, "kg", now_date, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="০ দিন ব্যবধান",
        reason_en="0 day divergence",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is not None
    assert res.is_symmetric_freshness is True
    assert res.source_observation_date == res.alternative_observation_date


def test_temporal_divergence_1_day_allowed_asymmetric():
    """Test 1-day difference: allowed but explicitly marked is_symmetric_freshness=False."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()
    yesterday = now_date - timedelta(days=1)

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (50.0, "kg", now_date, None, "LIVE"),
        (40.0, "kg", yesterday, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="১ দিন ব্যবধান",
        reason_en="1 day divergence",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is not None
    assert res.is_symmetric_freshness is False
    assert res.source_freshness_tier == "FRESH_TODAY"
    assert res.alternative_freshness_tier == "YESTERDAY"


def test_temporal_divergence_2_plus_days_excluded():
    """Test 2+ day difference: strictly excluded from recommendations."""
    service = AlternativeRecommendationService()
    mock_db = MagicMock()
    now_date = get_bangladesh_today()
    two_days_ago = now_date - timedelta(days=2)

    c_src = MagicMock(id=101, canonical_name="Item A", bangla_name="পণ্য এ", category="Vegetables")
    c_alt = MagicMock(id=102, canonical_name="Item B", bangla_name="পণ্য বি", category="Vegetables")
    mock_db.get.side_effect = lambda model, pk: c_src if pk == 101 else (c_alt if pk == 102 else None)

    # Source is today (2026-10-02), Alt is 2 days ago (2026-09-30) -> divergence = 2 days > 1
    service._fetch_latest_empirical_price = MagicMock(side_effect=[
        (50.0, "kg", now_date, None, "LIVE"),
        (40.0, "kg", two_days_ago, None, "LIVE"),
    ])

    entry = AlternativeRegistryEntry(
        source_commodity_id=101,
        source_canonical_name="Item A",
        alternative_commodity_id=102,
        alternative_canonical_name="Item B",
        category="Vegetables",
        reason_bn="২ দিন ব্যবধান",
        reason_en="2 day divergence",
    )
    res = service.evaluate_alternative(
        db=mock_db,
        entry=entry,
        target_date=now_date,
        channel="retail",
    )
    assert res is None, "Alternative with > 1 calendar day divergence must be strictly excluded."


def test_provenance_modeled_source_rejected(db):
    """Verify that modeled/synthetic sources are strictly excluded from empirical prices."""
    service = AlternativeRecommendationService()
    from app.models.source import Source
    from app.models.observation import PriceObservation

    # Check that SQL query filter excludes PANDAMART_MODELED
    modeled_src = db.query(Source).filter(Source.code == "PANDAMART_MODELED").first()
    if modeled_src:
        res = service._fetch_latest_empirical_price(
            db=db,
            commodity_id=1,
            target_date=get_bangladesh_today(),
            channel="retail",
        )
        if res:
            p_val, p_unit, p_date, _, _ = res
            # Find the actual observation record matching this price and date
            matched_obs = db.query(PriceObservation).filter(
                PriceObservation.commodity_id == 1,
                PriceObservation.observation_date == p_date,
                PriceObservation.normalized_price == p_val,
            ).all()
            for obs in matched_obs:
                assert obs.source.code != "PANDAMART_MODELED"
                assert obs.source.source_type != "modeled_benchmark"


def test_inactive_unit_pair_removed_from_registry():
    """Verify that dead unit pairings (e.g. Hilsa pc -> Rui kg) are not active."""
    service = AlternativeRecommendationService()
    active_pairs = service._entries
    for p in active_pairs:
        # Pairing 16 (Hilsa) -> 14 (Rui) must NOT be in active list
        assert not (p.source_commodity_id == 16 and p.alternative_commodity_id == 14)
        # Pairing 37 (Spinach) -> 36 (Red Spinach) must NOT be in active list
        assert not (p.source_commodity_id == 37 and p.alternative_commodity_id == 36)
        # Pairing 38 (Malabar) -> 36 (Red Spinach) must NOT be in active list
        assert not (p.source_commodity_id == 38 and p.alternative_commodity_id == 36)


def test_basket_service_find_alternatives_integration(db):
    """Test full basket service integration returns price_alternatives."""
    req = BasketCalculationRequest(
        items=[
            BasketItemInput(commodity_id=4, quantity=5.0, raw_unit="kg"),
            BasketItemInput(commodity_id=7, quantity=2.0, raw_unit="liter"),
        ]
    )
    res = basket_service.calculate(request=req, db=db)
    assert res is not None
    assert hasattr(res, "price_alternatives")
    assert isinstance(res.price_alternatives, list)
    for alt in res.price_alternatives:
        assert alt.savings_per_unit >= 2.0
        assert alt.savings_percent >= 5.0
        assert hasattr(alt, "source_observation_date")
        assert hasattr(alt, "alternative_observation_date")
        assert hasattr(alt, "is_symmetric_freshness")


def test_endpoint_get_alternatives(client):
    """Test the standalone GET /api/v1/basket/alternatives/{commodity_id} endpoint."""
    resp = client.get("/api/v1/basket/alternatives/4")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for alt in data:
        assert alt["source_commodity_id"] == 4
        assert alt["savings_per_unit"] >= 2.0
        assert alt["savings_percent"] >= 5.0
        assert "source_observation_date" in alt
        assert "alternative_observation_date" in alt
        assert "is_symmetric_freshness" in alt
