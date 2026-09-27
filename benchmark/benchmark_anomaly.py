"""
Anomaly Detection Benchmark — PricePulse BD
============================================
Validates the Compound Decision Rule (Z-score + Delta%) anomaly engine
against controlled synthetic time-series scenarios including normal baselines,
moderate volatility events, severe supply shocks, and negative (non-anomaly) controls.

Usage:
    python benchmark/benchmark_anomaly.py

Outputs:
    benchmark/results/anomaly_results.json
"""

import json
import math
import sys
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.services.anomaly_engine import AnomalyEngine


# ---------------------------------------------------------------------------
# Synthetic time-series fixtures
# ---------------------------------------------------------------------------

def _make_series(base: float, noise: float, length: int, seed: int = 42) -> List[Tuple[date, float]]:
    """Generate a stationary Brownian price walk with Gaussian noise."""
    import random
    rng = random.Random(seed)
    start = date(2025, 1, 1)
    series = []
    price = base
    for i in range(length):
        price = base + rng.gauss(0, noise)
        series.append((start + timedelta(days=i), round(price, 2)))
    return series


def _inject_shock(
    series: List[Tuple[date, float]],
    shock_day: int,
    shock_price: float,
) -> List[Tuple[date, float]]:
    """Inject a fixed shock price at shock_day, holding it through end."""
    result = []
    for i, (d, p) in enumerate(series):
        if i >= shock_day:
            p = shock_price
        result.append((d, p))
    return result


@dataclass
class AnomalyScenario:
    name: str
    series: List[Tuple[date, float]]
    target_date: Optional[date]
    expected_is_anomaly: bool
    expected_min_severity: str          # "Normal" | "Moderate" | "Severe" | "Critical"
    description: str


def build_scenarios() -> List[AnomalyScenario]:
    """Construct the full benchmark scenario set."""
    scenarios = []

    # --- Scenario S1: Stable onion baseline, no anomaly ---
    stable = _make_series(base=85.0, noise=1.5, length=30, seed=1)
    scenarios.append(AnomalyScenario(
        name="S1_Stable_Baseline",
        series=stable,
        target_date=date(2025, 1, 28),
        expected_is_anomaly=False,
        expected_min_severity="Normal",
        description="30-day stationary baseline with low noise. Should produce no alert.",
    ))

    # --- Scenario S2: Onion 50% supply shock (mimics Chapter 6 viva scenario) ---
    # 30 stable days, then 1 shock observation appended as target date.
    # The 14-day baseline (days 16-29) is entirely normal, giving a clean Z-score.
    shocked_50_base = _make_series(base=85.0, noise=0.9, length=30, seed=2)
    # Append shock day: 50% above the stable baseline of 85
    shock_date_s2 = shocked_50_base[-1][0] + timedelta(days=1)
    shocked_50 = shocked_50_base + [(shock_date_s2, 127.5)]
    scenarios.append(AnomalyScenario(
        name="S2_Onion_50pct_Shock",
        series=shocked_50,
        target_date=shock_date_s2,
        expected_is_anomaly=True,
        expected_min_severity="Critical",
        description="50% price surge in single day against clean baseline. Critical alert expected.",
    ))

    # --- Scenario S3: Moderate 12% deviation (cross Moderate threshold) ---
    # 30 stable days with very low noise (0.4 BDT), 1 shock day at +12% appended
    mod_shock_base = _make_series(base=70.0, noise=0.4, length=30, seed=3)
    shock_date_s3 = mod_shock_base[-1][0] + timedelta(days=1)
    mod_shock = mod_shock_base + [(shock_date_s3, 78.5)]  # +12.1%
    scenarios.append(AnomalyScenario(
        name="S3_Moderate_12pct_Shock",
        series=mod_shock,
        target_date=shock_date_s3,
        expected_is_anomaly=True,
        expected_min_severity="Moderate",
        description="12% single-day shock on very low-noise baseline. Moderate alert expected.",
    ))

    # --- Scenario S4: Severe 25% shock ---
    # 30 stable days (noise 0.4), shock day at +25% appended
    sev_shock_base = _make_series(base=60.0, noise=0.4, length=30, seed=4)
    shock_date_s4 = sev_shock_base[-1][0] + timedelta(days=1)
    sev_shock = sev_shock_base + [(shock_date_s4, 75.0)]  # +25%
    scenarios.append(AnomalyScenario(
        name="S4_Severe_25pct_Shock",
        series=sev_shock,
        target_date=shock_date_s4,
        expected_is_anomaly=True,
        expected_min_severity="Severe",
        description="25% single-day shock on tight baseline. Severe or Critical alert expected.",
    ))

    # --- Scenario S5: High-noise commodity (CV >5%), 8% shift should NOT trigger ---
    high_noise = _make_series(base=165.0, noise=9.0, length=30, seed=5)
    # 8% of 165 = 13.2 BDT — within noise envelope, compound rule suppresses
    high_noise[-1] = (high_noise[-1][0], 178.0)
    scenarios.append(AnomalyScenario(
        name="S5_HighNoise_SubThreshold",
        series=high_noise,
        target_date=high_noise[-1][0],
        expected_is_anomaly=False,
        expected_min_severity="Normal",
        description="High-volatility commodity with ~8% shift. Compound rule should suppress alert.",
    ))

    # --- Scenario S6: Price drop (negative shock / crash) ---
    crash_base = _make_series(base=120.0, noise=0.8, length=30, seed=6)
    shock_date_s6 = crash_base[-1][0] + timedelta(days=1)
    crash = crash_base + [(shock_date_s6, 78.0)]  # -35%
    scenarios.append(AnomalyScenario(
        name="S6_Price_Crash_35pct",
        series=crash,
        target_date=shock_date_s6,
        expected_is_anomaly=True,
        expected_min_severity="Critical",
        description="35% price crash in single day. Critical alert expected.",
    ))

    # --- Scenario S7: Sparse history (only 5 observations, no meaningful baseline) ---
    sparse = _make_series(base=50.0, noise=1.0, length=5, seed=7)
    scenarios.append(AnomalyScenario(
        name="S7_Sparse_History",
        series=sparse,
        target_date=sparse[-1][0],
        expected_is_anomaly=False,
        expected_min_severity="Normal",
        description="Only 5 historical points — insufficient baseline. No alert expected.",
    ))

    # --- Scenario S8: Potato stable with micro-noise — confirm no false positives ---
    potato_stable = _make_series(base=44.0, noise=0.8, length=30, seed=8)
    scenarios.append(AnomalyScenario(
        name="S8_Potato_Stable_NoAlert",
        series=potato_stable,
        target_date=potato_stable[-2][0],
        expected_is_anomaly=False,
        expected_min_severity="Normal",
        description="Potato stable baseline. Day 29 should show no anomaly.",
    ))

    # --- Scenario S9: Rice 30% shock --- Severe/Critical boundary ---
    rice_shock_base = _make_series(base=72.0, noise=0.4, length=30, seed=9)
    shock_date_s9 = rice_shock_base[-1][0] + timedelta(days=1)
    rice_shock = rice_shock_base + [(shock_date_s9, 93.6)]  # +30%
    scenarios.append(AnomalyScenario(
        name="S9_Rice_30pct_Shock",
        series=rice_shock,
        target_date=shock_date_s9,
        expected_is_anomaly=True,
        expected_min_severity="Severe",
        description="30% rice shock as single-day event. Severe or Critical expected.",
    ))

    # --- Scenario S10: Soybean oil tiny fluctuation (administered price regime) ---
    oil_stable = _make_series(base=162.0, noise=0.3, length=30, seed=10)
    scenarios.append(AnomalyScenario(
        name="S10_SoybeanOil_Administered",
        series=oil_stable,
        target_date=oil_stable[-1][0],
        expected_is_anomaly=False,
        expected_min_severity="Normal",
        description="Administered-price soybean oil. Noise is < 1 BDT/day. No alerts expected.",
    ))

    return scenarios


# ---------------------------------------------------------------------------
# Severity ordering helper
# ---------------------------------------------------------------------------

SEVERITY_RANK = {"Normal": 0, "Moderate": 1, "Severe": 2, "Critical": 3}


def severity_ok(actual: str, min_expected: str) -> bool:
    return SEVERITY_RANK.get(actual, 0) >= SEVERITY_RANK.get(min_expected, 0)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark() -> dict:
    engine = AnomalyEngine()
    scenarios = build_scenarios()

    pass_count = 0
    fail_count = 0
    rows = []

    for sc in scenarios:
        start = time.perf_counter()
        is_anomaly, severity, direction, metrics = engine.evaluate_series(
            sc.series, target_date=sc.target_date
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        anomaly_ok = (is_anomaly == sc.expected_is_anomaly)
        sev_ok = severity_ok(severity, sc.expected_min_severity)
        passed = anomaly_ok and sev_ok

        if passed:
            pass_count += 1
        else:
            fail_count += 1

        rows.append({
            "scenario": sc.name,
            "description": sc.description,
            "expected_is_anomaly": sc.expected_is_anomaly,
            "actual_is_anomaly": is_anomaly,
            "expected_min_severity": sc.expected_min_severity,
            "actual_severity": severity,
            "direction": direction,
            "z_score": getattr(metrics, "z_score_14d", None),
            "delta_pct": getattr(metrics, "percentage_change_14d", None),
            "sma_14d": getattr(metrics, "baseline_sma_14d", None),
            "cv_pct": getattr(metrics, "volatility_cv", None),
            "elapsed_ms": round(elapsed_ms, 3),
            "passed": passed,
        })

    total = pass_count + fail_count
    accuracy = round((pass_count / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_scenarios": total,
        "passed": pass_count,
        "failed": fail_count,
        "accuracy_pct": accuracy,
        "scenarios": rows,
    }


def print_report(results: dict) -> None:
    print()
    print("=" * 76)
    print("  PricePulse BD — Anomaly Detection Benchmark Report")
    print("=" * 76)
    print(f"  {'Scenario':<32} {'Pass':>5} {'Sev':<10} {'Z':>6} {'Delta%':>7} {'ms':>6}")
    print("  " + "-" * 72)
    for row in results["scenarios"]:
        mark = "[OK]" if row["passed"] else "[FAIL]"
        z = f"{row['z_score']:.2f}" if row["z_score"] is not None else "  N/A"
        dp = f"{row['delta_pct']:.1f}" if row["delta_pct"] is not None else "  N/A"
        print(
            f"  {row['scenario']:<32} {mark:>5}  {row['actual_severity']:<10} "
            f"{z:>6} {dp:>7} {row['elapsed_ms']:>6.2f}"
        )
    print("=" * 76)
    print(
        f"  RESULT: {results['passed']}/{results['total_scenarios']} passed "
        f"({results['accuracy_pct']}% accuracy)"
    )
    print("=" * 76)
    print()


def save_results(results: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark": "anomaly_detection", "results": results}, f, indent=2)
    print(f"  Results saved -> {out_path}")


if __name__ == "__main__":
    print("Running anomaly detection benchmark (10 scenarios)...")
    results = run_benchmark()
    print_report(results)
    out_path = PROJECT_ROOT / "benchmark" / "results" / "anomaly_results.json"
    save_results(results, out_path)
