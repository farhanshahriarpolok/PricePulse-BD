"""
Unit and integration tests for expanded commodity taxonomy, bilingual alias mapping, and unit normalization.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.normalizer import commodity_normalizer


@pytest.fixture(scope="module", autouse=True)
def reload_taxonomy():
    commodity_normalizer.reload()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestCountUnitConversions:
    """Test customary Bangladeshi count units and fractional conversions."""

    def test_hali_single_unit(self):
        base_unit, multiplier = commodity_normalizer.normalize_unit("হালি")
        assert base_unit == "pc"
        assert multiplier == 4.0

    def test_hali_english_alias(self):
        base_unit, multiplier = commodity_normalizer.normalize_unit("hali")
        assert base_unit == "pc"
        assert multiplier == 4.0

    def test_dozen_unit(self):
        base_unit, multiplier = commodity_normalizer.normalize_unit("ডজন")
        assert base_unit == "pc"
        assert multiplier == 12.0

    def test_dozen_english_alias(self):
        base_unit, multiplier = commodity_normalizer.normalize_unit("dozen")
        assert base_unit == "pc"
        assert multiplier == 12.0

    def test_half_dozen_fraction(self):
        base_unit, multiplier = commodity_normalizer.normalize_unit("1/2 dozen")
        assert base_unit == "pc"
        assert multiplier == 6.0

    def test_half_dozen_bengali(self):
        base_unit, multiplier = commodity_normalizer.normalize_unit("হাফ ডজন")
        assert base_unit == "pc"
        assert multiplier == 6.0

    def test_bengali_numerals_prefix(self):
        # ১ হালি = 4 pcs, ২ হালি = 8 pcs
        base_unit1, mult1 = commodity_normalizer.normalize_unit("১ হালি")
        assert base_unit1 == "pc"
        assert mult1 == 4.0

        base_unit2, mult2 = commodity_normalizer.normalize_unit("২ হালি")
        assert base_unit2 == "pc"
        assert mult2 == 8.0

    def test_egg_price_normalization_math(self):
        # 56 BDT per hali -> 14 BDT/pc
        norm_price, unit = commodity_normalizer.normalize_price(56.0, "হালি")
        assert norm_price == 14.0
        assert unit == "pc"

        # 168 BDT per dozen -> 14 BDT/pc
        norm_price_doz, unit_doz = commodity_normalizer.normalize_price(168.0, "ডজন")
        assert norm_price_doz == 14.0
        assert unit_doz == "pc"


class TestExpandedCommodityResolution:
    """Test bilingual alias resolution for newly added essential commodities."""

    def test_broiler_chicken_resolution(self):
        test_queries = [
            "ব্রয়লার মুরগি",
            "ব্রয়লার মুরগি",
            "broiler chicken",
            "chicken broiler",
            "broiler murgi",
        ]
        for q in test_queries:
            resolved = commodity_normalizer.resolve_commodity(q)
            assert resolved is not None, f"Failed to resolve '{q}'"
            assert resolved.canonical_name == "Broiler Chicken"
            assert resolved.default_unit == "kg"
            assert resolved.category == "Meat & Poultry"

    def test_farm_egg_resolution(self):
        test_queries = [
            "ফার্মের ডিম",
            "ফার্মের মুরগির ডিম",
            "farm egg",
            "chicken egg",
            "farm er dim",
        ]
        for q in test_queries:
            resolved = commodity_normalizer.resolve_commodity(q)
            assert resolved is not None, f"Failed to resolve '{q}'"
            assert resolved.canonical_name == "Farm Egg"
            assert resolved.default_unit == "pc"
            assert resolved.category == "Eggs & Dairy"

    def test_masur_dal_resolution(self):
        test_queries = [
            "মসুর ডাল (মাঝারি)",
            "মসুর ডাল",
            "মশুর ডাল",
            "masur dal",
            "masoor dal",
        ]
        for q in test_queries:
            resolved = commodity_normalizer.resolve_commodity(q)
            assert resolved is not None, f"Failed to resolve '{q}'"
            assert resolved.canonical_name == "Masur Dal (Medium)"
            assert resolved.default_unit == "kg"
            assert resolved.category == "Pulses"

    def test_garlic_resolution(self):
        test_queries = [
            "দেশি রসুন",
            "দেশী রসুন",
            "local garlic",
            "garlic (local)",
            "deshi roshun",
        ]
        for q in test_queries:
            resolved = commodity_normalizer.resolve_commodity(q)
            assert resolved is not None, f"Failed to resolve '{q}'"
            assert resolved.canonical_name == "Garlic (Local)"
            assert resolved.default_unit == "kg"
            assert resolved.category == "Spices"


class TestCompareCommoditiesEndpoint:
    """Test GET /api/v1/commodities/compare endpoint."""

    def test_compare_endpoint_success(self, client):
        res = client.get("/api/v1/commodities/compare?ids=1,2")
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert "commodity_id" in item
            assert "canonical_name" in item
            assert "unit" in item
            assert "is_anomaly" in item

    def test_compare_endpoint_invalid_ids(self, client):
        res = client.get("/api/v1/commodities/compare?ids=abc,xyz")
        assert res.status_code == 400
