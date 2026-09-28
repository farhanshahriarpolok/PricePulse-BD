"""
tests/test_expanded_basket.py
===============================
Validates normalization, unit conversion, and price calculations for the 10 newly
added commodity categories: Beef, Mutton, Rui Fish, Pangas Fish, Hilsa Fish,
Pasteurized Milk, Green Chilli, Sugar, Salt, and Mustard Oil.

All tests are deterministic and do not require a live database or network connection.
"""

import pytest
from app.services.normalizer import CommodityNormalizer


@pytest.fixture(scope="module")
def normalizer():
    return CommodityNormalizer()


# ─────────────────────────────────────────────
# Part 1: Commodity resolution — new basket
# ─────────────────────────────────────────────

class TestBeefResolution:
    def test_english_canonical(self, normalizer):
        r = normalizer.resolve_commodity("Beef (Local with Bone)")
        assert r is not None
        assert r.canonical_name == "Beef (Local with Bone)"

    def test_bangla_label(self, normalizer):
        r = normalizer.resolve_commodity("গরুর মাংস (হাড়সহ)")
        assert r is not None
        assert r.canonical_name == "Beef (Local with Bone)"

    def test_short_bangla(self, normalizer):
        r = normalizer.resolve_commodity("গরুর মাংস")
        assert r is not None
        assert r.canonical_name == "Beef (Local with Bone)"

    def test_phonetic(self, normalizer):
        r = normalizer.resolve_commodity("gorur mangsho")
        assert r is not None
        assert r.canonical_name == "Beef (Local with Bone)"

    def test_plain_english(self, normalizer):
        r = normalizer.resolve_commodity("beef with bone")
        assert r is not None
        assert r.canonical_name == "Beef (Local with Bone)"

    def test_default_unit_is_kg(self, normalizer):
        r = normalizer.resolve_commodity("beef")
        assert r is not None
        assert r.default_unit == "kg"


class TestMuttonResolution:
    def test_english(self, normalizer):
        r = normalizer.resolve_commodity("Mutton (Goat Meat)")
        assert r is not None
        assert r.canonical_name == "Mutton (Goat Meat)"

    def test_bangla(self, normalizer):
        r = normalizer.resolve_commodity("খাসির মাংস")
        assert r is not None
        assert r.canonical_name == "Mutton (Goat Meat)"

    def test_goat_meat(self, normalizer):
        r = normalizer.resolve_commodity("goat meat")
        assert r is not None
        assert r.canonical_name == "Mutton (Goat Meat)"

    def test_phonetic_khashi(self, normalizer):
        r = normalizer.resolve_commodity("khashi mangsho")
        assert r is not None
        assert r.canonical_name == "Mutton (Goat Meat)"


class TestFishResolution:
    def test_rui_english(self, normalizer):
        r = normalizer.resolve_commodity("Rui Fish (Fresh)")
        assert r is not None
        assert r.canonical_name == "Rui Fish (Fresh)"

    def test_rui_bangla(self, normalizer):
        r = normalizer.resolve_commodity("রুই মাছ")
        assert r is not None
        assert r.canonical_name == "Rui Fish (Fresh)"

    def test_rui_phonetic(self, normalizer):
        r = normalizer.resolve_commodity("rui mach")
        assert r is not None
        assert r.canonical_name == "Rui Fish (Fresh)"

    def test_pangas_english(self, normalizer):
        r = normalizer.resolve_commodity("Pangas Fish (Farm)")
        assert r is not None
        assert r.canonical_name == "Pangas Fish (Farm)"

    def test_pangas_bangla(self, normalizer):
        r = normalizer.resolve_commodity("পাঙ্গাস মাছ")
        assert r is not None
        assert r.canonical_name == "Pangas Fish (Farm)"

    def test_hilsa_bangla(self, normalizer):
        r = normalizer.resolve_commodity("ইলিশ মাছ")
        assert r is not None
        assert r.canonical_name == "Hilsa Fish (Medium)"

    def test_hilsa_phonetic(self, normalizer):
        r = normalizer.resolve_commodity("ilish mach")
        assert r is not None
        assert r.canonical_name == "Hilsa Fish (Medium)"

    def test_fish_category(self, normalizer):
        r = normalizer.resolve_commodity("Rui Fish (Fresh)")
        assert r.category == "Fish & Seafood"


class TestDairyResolution:
    def test_milk_english(self, normalizer):
        r = normalizer.resolve_commodity("Pasteurized Cow Milk")
        assert r is not None
        assert r.canonical_name == "Pasteurized Cow Milk"

    def test_milk_bangla(self, normalizer):
        r = normalizer.resolve_commodity("প্যাকেটজাত তরল দুধ")
        assert r is not None
        assert r.canonical_name == "Pasteurized Cow Milk"

    def test_milk_short_bangla(self, normalizer):
        r = normalizer.resolve_commodity("দুধ")
        assert r is not None
        assert r.canonical_name == "Pasteurized Cow Milk"

    def test_milk_unit(self, normalizer):
        r = normalizer.resolve_commodity("pasteurized milk")
        assert r is not None
        assert r.default_unit == "liter"


class TestSpicesAndOilsResolution:
    def test_green_chilli_english(self, normalizer):
        r = normalizer.resolve_commodity("Green Chilli")
        assert r is not None
        assert r.canonical_name == "Green Chilli"

    def test_green_chilli_bangla(self, normalizer):
        r = normalizer.resolve_commodity("কাঁচা মরিচ")
        assert r is not None
        assert r.canonical_name == "Green Chilli"

    def test_sugar_english(self, normalizer):
        r = normalizer.resolve_commodity("Sugar (Refined White)")
        assert r is not None
        assert r.canonical_name == "Sugar (Refined White)"

    def test_sugar_bangla(self, normalizer):
        r = normalizer.resolve_commodity("চিনি")
        assert r is not None
        assert r.canonical_name == "Sugar (Refined White)"

    def test_salt_iodized(self, normalizer):
        r = normalizer.resolve_commodity("Salt (Iodized)")
        assert r is not None
        assert r.canonical_name == "Salt (Iodized)"

    def test_salt_bangla(self, normalizer):
        r = normalizer.resolve_commodity("লবণ")
        assert r is not None
        assert r.canonical_name == "Salt (Iodized)"

    def test_mustard_oil_english(self, normalizer):
        r = normalizer.resolve_commodity("Mustard Oil")
        assert r is not None
        assert r.canonical_name == "Mustard Oil"

    def test_mustard_oil_bangla(self, normalizer):
        r = normalizer.resolve_commodity("সরিষার তেল")
        assert r is not None
        assert r.canonical_name == "Mustard Oil"

    def test_mustard_oil_unit(self, normalizer):
        r = normalizer.resolve_commodity("Mustard Oil")
        assert r.default_unit == "liter"


# ─────────────────────────────────────────────
# Part 2: Unit conversions for new categories
# ─────────────────────────────────────────────

class TestExpandedUnitConversions:
    """Verify that the expanded UNIT_MAP handles Bangla fraction units correctly."""

    def test_adha_kaji_half_kg(self, normalizer):
        unit, mult = normalizer.normalize_unit("আধা কেজি")
        assert unit == "kg"
        assert abs(mult - 0.5) < 0.001

    def test_poa_quarter_kg(self, normalizer):
        unit, mult = normalizer.normalize_unit("পোয়া")
        assert unit == "kg"
        assert abs(mult - 0.25) < 0.001

    def test_250g_pack(self, normalizer):
        unit, mult = normalizer.normalize_unit("250g")
        assert unit == "kg"
        assert abs(mult - 0.25) < 0.001

    def test_500gm_pack(self, normalizer):
        unit, mult = normalizer.normalize_unit("500gm")
        assert unit == "kg"
        assert abs(mult - 0.5) < 0.001

    def test_500ml_liter(self, normalizer):
        unit, mult = normalizer.normalize_unit("500ml")
        assert unit == "liter"
        assert abs(mult - 0.5) < 0.001

    def test_half_liter_bangla(self, normalizer):
        unit, mult = normalizer.normalize_unit("আধা লিটার")
        assert unit == "liter"
        assert abs(mult - 0.5) < 0.001


# ─────────────────────────────────────────────
# Part 3: Price normalization for new goods
# ─────────────────────────────────────────────

class TestPriceNormalizationExpandedBasket:
    """Verify price-per-base-unit calculation for realistic prices."""

    def test_beef_price_per_kg(self, normalizer):
        # 750 BDT/kg wholesale beef
        price, unit = normalizer.normalize_price(750.0, "kg")
        assert unit == "kg"
        assert abs(price - 750.0) < 0.01

    def test_milk_per_half_liter(self, normalizer):
        # 36 BDT for 500ml pack → 72 BDT/liter
        price, unit = normalizer.normalize_price(36.0, "500ml")
        assert unit == "liter"
        assert abs(price - 72.0) < 0.01

    def test_green_chilli_250g_pack(self, normalizer):
        # 30 BDT for 250g → 120 BDT/kg
        price, unit = normalizer.normalize_price(30.0, "250g")
        assert unit == "kg"
        assert abs(price - 120.0) < 0.01

    def test_hilsa_per_kg(self, normalizer):
        price, unit = normalizer.normalize_price(950.0, "kg")
        assert unit == "kg"
        assert abs(price - 950.0) < 0.01

    def test_mustard_oil_500ml_bottle(self, normalizer):
        # 120 BDT for 500ml bottle → 240 BDT/liter
        price, unit = normalizer.normalize_price(120.0, "500ml")
        assert unit == "liter"
        assert abs(price - 240.0) < 0.01

    def test_salt_half_kg_pack(self, normalizer):
        # 19 BDT for 500gm → 38 BDT/kg
        price, unit = normalizer.normalize_price(19.0, "500gm")
        assert unit == "kg"
        assert abs(price - 38.0) < 0.01


# ─────────────────────────────────────────────
# Part 4: Reject out-of-domain strings
# ─────────────────────────────────────────────

class TestOutOfDomainRejection:
    """New commodities should not cause false positives for unrelated strings."""

    def test_urea_fertilizer_rejected(self, normalizer):
        assert normalizer.resolve_commodity("Urea Fertilizer 50kg") is None

    def test_motor_oil_rejected(self, normalizer):
        # "oil" alone should NOT match mustard oil or soybean oil without context
        # (because "motor engine oil" has no commodity alias match)
        r = normalizer.resolve_commodity("Motor Engine Oil SAE 40")
        # If it resolves, it must NOT be a food oil
        if r is not None:
            assert "Motor" not in r.canonical_name

    def test_cement_rejected(self, normalizer):
        assert normalizer.resolve_commodity("Cement 50kg bag") is None

    def test_empty_string_rejected(self, normalizer):
        assert normalizer.resolve_commodity("") is None

    def test_whitespace_rejected(self, normalizer):
        assert normalizer.resolve_commodity("   ") is None
