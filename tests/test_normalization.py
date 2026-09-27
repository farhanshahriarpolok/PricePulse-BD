"""
Unit tests for commodity alias resolution, metric unit conversion, and confidence scoring.
"""

from datetime import date, timedelta
import pytest
from app.services.normalizer import CommodityNormalizer
from app.services.confidence import ConfidenceScorer


@pytest.fixture
def normalizer():
    return CommodityNormalizer()


@pytest.fixture
def scorer():
    return ConfidenceScorer()


class TestCommodityAliasResolution:
    """Test bilingual and phonetic commodity resolution against taxonomy."""

    def test_bengali_exact_aliases(self, normalizer):
        cases = [
            ("দেশি পেঁয়াজ", "Onion (Local)"),
            ("দেশি পেঁয়াজ", "Onion (Local)"),
            ("আমদানি পেঁয়াজ", "Onion (Imported)"),
            ("ডায়মন্ড আলু", "Potato (Diamond)"),
            ("মিনিকেট চাল", "Rice (Miniket)"),
            ("মোটা চাল", "Rice (Coarse)"),
            ("বোতলজাত সয়াবিন তেল", "Soybean Oil (Bottled)"),
        ]
        for raw, expected in cases:
            res = normalizer.resolve_commodity(raw)
            assert res is not None, f"Failed to resolve '{raw}'"
            assert res.canonical_name == expected, f"Expected {expected}, got {res.canonical_name}"
            assert res.match_weight >= 0.90

    def test_english_and_phonetic_aliases(self, normalizer):
        cases = [
            ("local onion", "Onion (Local)"),
            ("deshi peyaj", "Onion (Local)"),
            ("diamond potato", "Potato (Diamond)"),
            ("miniket rice", "Rice (Miniket)"),
            ("miniket chal", "Rice (Miniket)"),
            ("soybean oil", "Soybean Oil (Bottled)"),
        ]
        for raw, expected in cases:
            res = normalizer.resolve_commodity(raw)
            assert res is not None, f"Failed to resolve '{raw}'"
            assert res.canonical_name == expected

    def test_unmapped_commodity_returns_none(self, normalizer):
        res = normalizer.resolve_commodity("অপরিচিত পণ্য এক্সওয়াইজেড 123")
        assert res is None


class TestUnitAndPriceNormalization:
    """Test standard SI unit conversions."""

    def test_kg_standard_unit(self, normalizer):
        norm_price, norm_unit = normalizer.normalize_price(85.0, "কেজি")
        assert norm_unit == "kg"
        assert norm_price == 85.0

    def test_maund_to_kg_conversion(self, normalizer):
        # 1 Maund = 40.0 kg in Bangladesh commercial trade
        # 2800 BDT per maund -> 2800 / 40 = 70.0 BDT/kg
        norm_price, norm_unit = normalizer.normalize_price(2800.0, "মণ")
        assert norm_unit == "kg"
        assert norm_price == 70.0

    def test_seer_to_kg_conversion(self, normalizer):
        # 1 Seer = 0.933 kg
        # 93.3 BDT per seer -> 93.3 / 0.933 = 100.0 BDT/kg
        norm_price, norm_unit = normalizer.normalize_price(93.3, "সের")
        assert norm_unit == "kg"
        assert norm_price == 100.0

    def test_volume_and_count_conversions(self, normalizer):
        # Liters
        p1, u1 = normalizer.normalize_price(167.0, "লিটার")
        assert u1 == "liter"
        assert p1 == 167.0

        # Hali -> 4 pieces
        p2, u2 = normalizer.normalize_price(48.0, "হালি")
        assert u2 == "pc"
        assert p2 == 12.0

        # Dozen -> 12 pieces
        p3, u3 = normalizer.normalize_price(144.0, "ডজন")
        assert u3 == "pc"
        assert p3 == 12.0

    def test_invalid_unit_raises_error(self, normalizer):
        with pytest.raises(ValueError):
            normalizer.normalize_price(100.0, "nonexistent_unit")


class TestConfidenceScoring:
    """Test mathematical confidence score computation."""

    def test_confidence_range_and_weights(self, scorer):
        today = date.today()
        score = scorer.compute(
            source_reliability=0.95,
            alias_weight=1.0,
            observation_date=today,
            completeness_score=1.0,
            reference_date=today,
        )
        assert 0.0 <= score <= 1.0
        # 0.4*0.95 + 0.3*1.0 + 0.15*1.0 + 0.15*1.0 = 0.38 + 0.30 + 0.15 + 0.15 = 0.98
        assert pytest.approx(score, 0.01) == 0.98

    def test_freshness_decay(self, scorer):
        today = date.today()
        ten_days_ago = today - timedelta(days=10)

        fresh_score = scorer.compute(
            source_reliability=0.90,
            alias_weight=0.95,
            observation_date=today,
            reference_date=today,
        )
        stale_score = scorer.compute(
            source_reliability=0.90,
            alias_weight=0.95,
            observation_date=ten_days_ago,
            reference_date=today,
        )
        assert stale_score < fresh_score
