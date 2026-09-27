"""
Unit tests for statistical anomaly formulas, compound anomaly decision rules, and explanation formatting.
"""

from datetime import date, timedelta
import pytest
from app.services.anomaly_engine import AnomalyEngine
from app.schemas.anomaly import MetricBreakdown


@pytest.fixture
def engine():
    return AnomalyEngine()


class TestStatisticalFormulas:
    """Test core statistical calculations."""

    def test_sma_calculation(self, engine):
        values = [80.0, 82.0, 84.0, 86.0, 88.0]
        sma = engine.calculate_sma(values)
        assert sma == 84.0

    def test_std_dev_calculation(self, engine):
        values = [10.0, 12.0, 14.0, 16.0, 18.0]
        # Mean = 14, sample variance = ((16 + 4 + 0 + 4 + 16) / 4) = 10.0, std = sqrt(10) ≈ 3.1623
        std = engine.calculate_std_dev(values, sma=14.0)
        assert pytest.approx(std, 0.01) == 3.1623

    def test_z_score_calculation(self, engine):
        # Current = 120, baseline = 100, std = 10 -> Z = +2.0
        z = engine.calculate_z_score(current_price=120.0, baseline_sma=100.0, std_dev=10.0)
        assert z == 2.0

        # Current = 80, baseline = 100, std = 10 -> Z = -2.0
        z_neg = engine.calculate_z_score(current_price=80.0, baseline_sma=100.0, std_dev=10.0)
        assert z_neg == -2.0

    def test_cv_calculation(self, engine):
        # Baseline = 100, std = 5 -> CV = 5.0%
        cv = engine.calculate_cv(std_dev=5.0, baseline_sma=100.0)
        assert cv == 5.0


class TestCompoundAnomalyRules:
    """Test compound decision rules requiring both Z-score and percentage deviation."""

    def test_stable_series_produces_normal_status(self, engine):
        today = date.today()
        # 14 days of stable prices around 90 BDT
        series = [(today - timedelta(days=14 - i), 90.0 + (i % 2)) for i in range(15)]
        is_anomaly, severity, direction, metrics = engine.evaluate_series(series, target_date=today)

        assert not is_anomaly
        assert severity == "Normal"
        assert direction is None
        assert abs(metrics.z_score_14d) < 1.5

    def test_severe_spike_triggers_anomaly(self, engine):
        today = date.today()
        # 14 days around 90 BDT with a sudden jump to 125 BDT on target date
        series = [(today - timedelta(days=14 - i), 90.0 + (i % 2)) for i in range(14)]
        series.append((today, 125.0))  # +38% jump

        is_anomaly, severity, direction, metrics = engine.evaluate_series(series, target_date=today)

        assert is_anomaly
        assert severity in ["Severe", "Critical"]
        assert direction == "Spike"
        assert metrics.z_score_14d >= 2.0
        assert metrics.percentage_change_14d >= 20.0

    def test_explanation_generation_content(self, engine):
        metrics = MetricBreakdown(
            current_price=125.0,
            baseline_sma_14d=90.0,
            std_dev_14d=5.0,
            z_score_14d=7.0,
            percentage_change_14d=38.9,
            volatility_cv=5.5,
        )
        text = engine.generate_explanation(
            commodity_name="Onion (Local)",
            unit="kg",
            eval_date=date.today(),
            is_anomaly=True,
            severity="Critical",
            direction="Spike",
            metrics=metrics,
        )

        assert "Onion (Local)" in text
        assert "critical price spike" in text
        assert "125.00 BDT/kg" in text
        assert "+38.9%" in text
        assert "Z = +7.00" in text
