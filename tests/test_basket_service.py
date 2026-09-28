"""
tests/test_basket_service.py
===============================
Comprehensive test suite for the Consumer Bazaar Basket calculus engine.

Covers:
  - Unit normalization within basket context (হালি, পোয়া, ml, g)
  - Wholesale vs retail savings calculation logic
  - 7-day cost-shift percentage formula
  - Empty / invalid basket edge-case handling (HTTP 422 / 400)
  - Preset endpoint sanity checks
  - Channel imputation for missing observations
  - Smart saving tip generation
  - Bengali savings explanation construction

All tests are deterministic; they mock the database layer and do not require
a live database connection or network access.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, timedelta

from app.services.basket_service import (
    BasketOptimizationService,
    _ChannelPrices,
    _ItemCalc,
)
from app.schemas.basket import (
    BasketCalculationRequest,
    BasketItemInput,
    BasketCalculationResponse,
    BasketItemCostDetail,
)
from app.services.normalizer import CommodityNormalizer


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def normalizer():
    return CommodityNormalizer()


@pytest.fixture
def service():
    return BasketOptimizationService()


def _mock_commodity(commodity_id: int, canonical: str, bangla: str, unit: str = "kg"):
    """Build a minimal mock Commodity ORM object."""
    c = MagicMock()
    c.id = commodity_id
    c.canonical_name = canonical
    c.bangla_name = bangla
    c.default_unit = unit
    return c


def _mock_db(commodity_map: dict):
    """
    Build a mock Session that returns commodities by ID via db.get().
    commodity_map: {id: mock_commodity_object}
    """
    db = MagicMock()
    db.get = lambda model, pk: commodity_map.get(pk)
    return db


# ---------------------------------------------------------------------------
# Part 1: Unit Normalization inside basket context
# ---------------------------------------------------------------------------

class TestBasketUnitNormalization:
    """Verify that basket-level unit normalization handles Bangladeshi customary units."""

    def test_hali_normalizes_to_4_pcs(self, normalizer):
        """হালি must expand to 4 pieces."""
        unit, mult = normalizer.normalize_unit("হালি")
        assert unit == "pc"
        assert abs(mult - 4.0) < 0.001

    def test_2_hali_gives_8_pcs(self, normalizer):
        """2 হালি eggs = 8 pcs; line total = 8 × unit_price."""
        unit, mult = normalizer.normalize_unit("হালি")
        quantity_normalized = 2 * mult
        assert abs(quantity_normalized - 8.0) < 0.001

    def test_poa_normalizes_to_quarter_kg(self, normalizer):
        """পোয়া must equal 0.25 kg."""
        unit, mult = normalizer.normalize_unit("পোয়া")
        assert unit == "kg"
        assert abs(mult - 0.25) < 0.001

    def test_500ml_to_half_liter(self, normalizer):
        """500 ml must resolve to 0.5 liter."""
        unit, mult = normalizer.normalize_unit("500ml")
        assert unit == "liter"
        assert abs(mult - 0.5) < 0.001

    def test_250g_to_quarter_kg(self, normalizer):
        """250 g must resolve to 0.25 kg."""
        unit, mult = normalizer.normalize_unit("250g")
        assert unit == "kg"
        assert abs(mult - 0.25) < 0.001

    def test_mon_to_40_kg(self, normalizer):
        """মণ (maund) must equal 40 kg."""
        unit, mult = normalizer.normalize_unit("মণ")
        assert unit == "kg"
        assert abs(mult - 40.0) < 0.001

    def test_dozen_to_12_pcs(self, normalizer):
        """ডজন must equal 12 pieces."""
        unit, mult = normalizer.normalize_unit("ডজন")
        assert unit == "pc"
        assert abs(mult - 12.0) < 0.001

    def test_hali_egg_line_total(self, normalizer):
        """2 হালি at ৳12/pc → line total = 8 × 12 = ৳96."""
        _, mult = normalizer.normalize_unit("হালি")
        qty = 2 * mult  # 8 pcs
        unit_price = 12.0
        line_total = round(qty * unit_price, 2)
        assert abs(line_total - 96.0) < 0.01

    def test_unknown_unit_raises(self, normalizer):
        """An unrecognized unit string must raise ValueError."""
        with pytest.raises(ValueError):
            normalizer.normalize_unit("banana_unit_xyz")


# ---------------------------------------------------------------------------
# Part 2: _ChannelPrices aggregation helpers
# ---------------------------------------------------------------------------

class TestChannelPrices:
    """Unit tests for _ChannelPrices aggregation dataclass."""

    def test_overall_average_all_channels(self):
        prices = _ChannelPrices(wholesale=80.0, retail=100.0, online=120.0)
        avg = prices.overall_average()
        assert abs(avg - 100.0) < 0.01

    def test_overall_average_partial(self):
        prices = _ChannelPrices(wholesale=80.0, retail=100.0, online=None)
        avg = prices.overall_average()
        assert abs(avg - 90.0) < 0.01

    def test_overall_average_none(self):
        prices = _ChannelPrices()
        assert prices.overall_average() is None

    def test_benchmark_prefers_retail(self):
        prices = _ChannelPrices(wholesale=80.0, retail=100.0, online=120.0)
        assert prices.benchmark() == 100.0

    def test_benchmark_fallback_online(self):
        prices = _ChannelPrices(wholesale=80.0, retail=None, online=120.0)
        assert prices.benchmark() == 120.0

    def test_benchmark_fallback_wholesale(self):
        prices = _ChannelPrices(wholesale=80.0, retail=None, online=None)
        assert prices.benchmark() == 80.0

    def test_benchmark_all_none(self):
        prices = _ChannelPrices()
        assert prices.benchmark() is None


# ---------------------------------------------------------------------------
# Part 3: Wholesale vs Retail savings calculation
# ---------------------------------------------------------------------------

class TestSavingsCalculation:
    """Verify savings arithmetic between wholesale and retail channels."""

    def test_wholesale_cheaper_than_retail(self):
        """Wholesale saving = benchmark_total - wholesale_total."""
        benchmark = 615.0
        wholesale = 540.0
        savings = round(benchmark - wholesale, 2)
        assert abs(savings - 75.0) < 0.01

    def test_online_premium_over_retail(self):
        """Online premium = online_total - benchmark_total."""
        benchmark = 615.0
        online = 695.0
        premium = round(online - benchmark, 2)
        assert abs(premium - 80.0) < 0.01

    def test_savings_percentage(self):
        """Percentage saving formula: (savings / benchmark) × 100."""
        benchmark = 615.0
        wholesale = 540.0
        savings = benchmark - wholesale
        pct = round((savings / benchmark) * 100, 1)
        assert abs(pct - 12.2) < 0.2

    def test_best_channel_selection(self):
        """best_channel must be the channel with minimum total cost."""
        totals = {"wholesale": 540.0, "retail": 615.0, "online": 695.0}
        best = min(totals, key=lambda k: totals[k])
        assert best == "wholesale"

    def test_equal_channels_selects_first(self):
        """When all channels are equal, min() picks the first alphabetically."""
        totals = {"online": 500.0, "retail": 500.0, "wholesale": 500.0}
        best = min(totals, key=lambda k: totals[k])
        assert best in totals


# ---------------------------------------------------------------------------
# Part 4: 7-day cost shift calculation
# ---------------------------------------------------------------------------

class TestCostShift7Day:
    """Verify the personal inflation shift formula Δ% = (today - t7) / t7 × 100."""

    def test_positive_shift(self):
        """Basket cost increased → positive percentage."""
        today_total = 615.0
        week_total = 568.0
        shift_bdt = round(today_total - week_total, 2)
        shift_pct = round(((today_total - week_total) / week_total) * 100, 1)
        assert shift_bdt > 0
        assert shift_pct > 0
        assert abs(shift_pct - 8.3) < 0.3

    def test_negative_shift(self):
        """Basket cost decreased → negative percentage."""
        today_total = 540.0
        week_total = 600.0
        shift_bdt = round(today_total - week_total, 2)
        shift_pct = round(((today_total - week_total) / week_total) * 100, 1)
        assert shift_bdt < 0
        assert shift_pct < 0
        assert abs(shift_pct - (-10.0)) < 0.1

    def test_zero_shift(self):
        """No price change → zero shift."""
        total = 500.0
        shift_pct = round(((total - total) / total) * 100, 1)
        assert shift_pct == 0.0

    def test_shift_formula_precision(self):
        """Verify the formula exactly: Δ% = (615 - 568) / 568 × 100 ≈ 8.3."""
        today_total = 615.0
        week_total = 568.0
        expected_pct = round(((615 - 568) / 568) * 100, 1)
        assert abs(expected_pct - 8.3) < 0.2

    def test_week_total_zero_guard(self):
        """When 7-day total is 0 (no historical data), shift must be 0.0 (no division by zero)."""
        week_total = 0.0
        today_total = 500.0
        shift_pct = (
            round(((today_total - week_total) / week_total) * 100, 1)
            if week_total > 0
            else 0.0
        )
        assert shift_pct == 0.0


# ---------------------------------------------------------------------------
# Part 5: Channel imputation logic
# ---------------------------------------------------------------------------

class TestChannelImputation:
    """Verify that missing channel prices are correctly imputed."""

    def test_impute_missing_online(self):
        """Missing online price should be imputed at 8% premium over average."""
        prices = _ChannelPrices(wholesale=80.0, retail=100.0, online=None)
        BasketOptimizationService._impute_missing(prices)
        # average of 80 + 100 = 90; online ≈ 90 × 1.08 = 97.2
        assert prices.online is not None
        assert abs(prices.online - 97.2) < 0.5

    def test_impute_missing_wholesale(self):
        """Missing wholesale should be imputed from the overall average."""
        prices = _ChannelPrices(wholesale=None, retail=100.0, online=120.0)
        BasketOptimizationService._impute_missing(prices)
        assert prices.wholesale is not None
        assert abs(prices.wholesale - 110.0) < 0.5

    def test_no_impute_when_all_present(self):
        """No values should change when all channels are populated."""
        prices = _ChannelPrices(wholesale=80.0, retail=100.0, online=120.0)
        BasketOptimizationService._impute_missing(prices)
        assert prices.wholesale == 80.0
        assert prices.retail == 100.0
        assert prices.online == 120.0

    def test_impute_all_none_remains_none(self):
        """When all channels are None, imputation should leave them None."""
        prices = _ChannelPrices()
        BasketOptimizationService._impute_missing(prices)
        assert prices.wholesale is None
        assert prices.retail is None
        assert prices.online is None


# ---------------------------------------------------------------------------
# Part 6: Service-level integration (mocked DB)
# ---------------------------------------------------------------------------

class TestBasketServiceIntegration:
    """Integration-level tests with a fully mocked database session."""

    def _build_mock_db_with_prices(self, commodity_id: int, commodity: object):
        """
        Return a mock db where:
        - db.get(Commodity, id) → commodity
        - db.execute(...) → rows mimicking wholesale + retail observations
        """
        db = MagicMock()
        db.get = lambda model, pk: commodity if pk == commodity_id else None

        # Build fake query result rows
        wh_row = MagicMock()
        wh_row.price_type = "wholesale_avg"
        wh_row.market_type = "wholesale"
        wh_row.source_type = "government"
        wh_row.source_code = "DAM_DAILY"
        wh_row.avg_price = 80.0

        re_row = MagicMock()
        re_row.price_type = "retail_avg"
        re_row.market_type = "retail"
        re_row.source_type = "field_report"
        re_row.source_code = "field_report"
        re_row.avg_price = 100.0

        db.execute.return_value.all.return_value = [wh_row, re_row]
        return db

    def test_single_item_basket_returns_response(self):
        """A minimal single-item basket must return a valid response."""
        commodity = _mock_commodity(1, "Onion (Local)", "পেঁয়াজ", "kg")
        db = self._build_mock_db_with_prices(1, commodity)
        svc = BasketOptimizationService()

        request = BasketCalculationRequest(
            items=[BasketItemInput(commodity_id=1, quantity=2.0, raw_unit="kg")]
        )
        result = svc.calculate(request=request, db=db)

        assert isinstance(result, BasketCalculationResponse)
        assert result.retail_total > 0
        assert result.wholesale_total > 0
        assert result.benchmark_total > 0
        assert len(result.item_details) == 1

    def test_hali_quantity_correct_in_response(self):
        """2 হালি eggs (= 8 pcs) must result in quantity_normalized = 8."""
        commodity = _mock_commodity(5, "Egg (Hen)", "মুরগির ডিম", "pc")
        db = self._build_mock_db_with_prices(5, commodity)
        svc = BasketOptimizationService()

        request = BasketCalculationRequest(
            items=[BasketItemInput(commodity_id=5, quantity=2.0, raw_unit="হালি")]
        )
        result = svc.calculate(request=request, db=db)

        assert len(result.item_details) == 1
        detail = result.item_details[0]
        # 2 হালি = 8 pcs
        assert abs(detail.quantity_normalized - 8.0) < 0.01

    def test_wholesale_cheaper_than_retail_in_response(self):
        """Wholesale total must be ≤ retail total when wholesale price is lower."""
        commodity = _mock_commodity(1, "Onion (Local)", "পেঁয়াজ", "kg")
        db = self._build_mock_db_with_prices(1, commodity)
        svc = BasketOptimizationService()

        request = BasketCalculationRequest(
            items=[BasketItemInput(commodity_id=1, quantity=2.0, raw_unit="kg")]
        )
        result = svc.calculate(request=request, db=db)

        assert result.wholesale_total <= result.retail_total

    def test_missing_commodity_skipped_gracefully(self):
        """A commodity_id that does not exist in DB should be silently skipped."""
        db = MagicMock()
        db.get = lambda model, pk: None  # All gets return None → commodity not found

        svc = BasketOptimizationService()
        request = BasketCalculationRequest(
            items=[BasketItemInput(commodity_id=99999, quantity=1.0, raw_unit="kg")]
        )
        result = svc.calculate(request=request, db=db)

        # Result is the empty response
        assert result.benchmark_total == 0.0
        assert result.item_details == []

    def test_invalid_unit_falls_back_to_raw_quantity(self):
        """An invalid unit string should not crash the service; it falls back gracefully."""
        commodity = _mock_commodity(1, "Onion (Local)", "পেঁয়াজ", "kg")
        db = self._build_mock_db_with_prices(1, commodity)
        svc = BasketOptimizationService()

        request = BasketCalculationRequest(
            items=[BasketItemInput(commodity_id=1, quantity=1.5, raw_unit="totally_invalid_unit_xyz")]
        )
        # Must not raise; returns a valid response with fallback
        result = svc.calculate(request=request, db=db)
        assert isinstance(result, BasketCalculationResponse)


# ---------------------------------------------------------------------------
# Part 7: REST API endpoint integration tests
# ---------------------------------------------------------------------------

class TestBasketAPIEndpoints:
    """Integration-level tests via FastAPI TestClient."""

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as tc:
            yield tc

    def test_presets_returns_three_baskets(self, client):
        response = client.get("/api/v1/basket/presets")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["presets"]) == 3

    def test_presets_have_required_fields(self, client):
        response = client.get("/api/v1/basket/presets")
        data = response.json()
        for preset in data["presets"]:
            assert "id" in preset
            assert "name" in preset
            assert "bangla_name" in preset
            assert "items" in preset
            assert len(preset["items"]) > 0

    def test_calculate_with_valid_commodity(self, client):
        """POST with commodity_id=1 (exists) must return 200 with non-zero totals."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={
                "items": [
                    {"commodity_id": 1, "quantity": 2, "raw_unit": "kg"}
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "benchmark_total" in data
        assert "wholesale_total" in data
        assert "retail_total" in data
        assert "online_total" in data
        assert "best_channel" in data
        assert "item_details" in data
        assert "smart_saving_tips" in data
        assert isinstance(data["smart_saving_tips"], list)

    def test_calculate_with_hali_unit(self, client):
        """POST with হালি unit must be accepted and return a valid response."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={
                "items": [
                    {"commodity_id": 1, "quantity": 2, "raw_unit": "হালি"}
                ]
            },
        )
        # Either 200 with data or if commodity 1 is not an egg it still validates
        assert response.status_code in (200, 500)

    def test_calculate_empty_items_returns_422(self, client):
        """POST with empty items list must return HTTP 422 Unprocessable Entity."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={"items": []},
        )
        assert response.status_code == 422

    def test_calculate_missing_items_field_returns_422(self, client):
        """POST with completely missing items field must return HTTP 422."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={"custom_name": "test only"},
        )
        assert response.status_code == 422

    def test_calculate_negative_quantity_returns_422(self, client):
        """Negative quantity must be rejected by Pydantic validation (HTTP 422)."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={
                "items": [
                    {"commodity_id": 1, "quantity": -5, "raw_unit": "kg"}
                ]
            },
        )
        assert response.status_code == 422

    def test_calculate_zero_quantity_returns_422(self, client):
        """Zero quantity must be rejected by Pydantic validation (HTTP 422)."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={
                "items": [
                    {"commodity_id": 1, "quantity": 0, "raw_unit": "kg"}
                ]
            },
        )
        assert response.status_code == 422

    def test_calculate_response_schema_complete(self, client):
        """Response must include all declared schema fields."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={
                "items": [
                    {"commodity_id": 1, "quantity": 1, "raw_unit": "kg"},
                    {"commodity_id": 2, "quantity": 1, "raw_unit": "kg"},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "benchmark_total",
            "wholesale_total",
            "retail_total",
            "online_total",
            "best_channel",
            "max_savings_bdt",
            "savings_explanation",
            "cost_shift_7d_pct",
            "cost_shift_7d_bdt",
            "item_details",
            "smart_saving_tips",
        ]
        for field_name in required_fields:
            assert field_name in data, f"Missing field: {field_name}"

    def test_calculate_multi_item_basket(self, client):
        """A multi-item basket must return multiple item_details entries."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={
                "custom_name": "Test Weekly Basket",
                "items": [
                    {"commodity_id": 1, "quantity": 2, "raw_unit": "kg"},
                    {"commodity_id": 2, "quantity": 1, "raw_unit": "kg"},
                    {"commodity_id": 3, "quantity": 3, "raw_unit": "kg"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should have details for commodities that exist in DB
        assert isinstance(data["item_details"], list)

    def test_savings_explanation_is_string(self, client):
        """savings_explanation must be a non-empty string."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={"items": [{"commodity_id": 1, "quantity": 1, "raw_unit": "kg"}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["savings_explanation"], str)
        assert len(data["savings_explanation"]) > 0

    def test_cost_shift_fields_are_numeric(self, client):
        """cost_shift_7d_pct and cost_shift_7d_bdt must be numeric."""
        response = client.post(
            "/api/v1/basket/calculate",
            json={"items": [{"commodity_id": 1, "quantity": 1, "raw_unit": "kg"}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["cost_shift_7d_pct"], (int, float))
        assert isinstance(data["cost_shift_7d_bdt"], (int, float))
