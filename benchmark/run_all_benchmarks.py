"""
Benchmark Suite Runner — PricePulse BD
=======================================
Runs all three benchmark modules sequentially and emits a combined
summary report for thesis Chapter 6 and viva defense reference.

Usage:
    python benchmark/run_all_benchmarks.py
    python -m benchmark.run_all_benchmarks

Outputs:
    benchmark/results/normalization_results.json
    benchmark/results/anomaly_results.json
    benchmark/results/latency_results.json
    benchmark/results/combined_summary.json
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

RESULTS_DIR = PROJECT_ROOT / "benchmark" / "results"


def section(title: str) -> None:
    bar = "=" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(f"{bar}")


def run_normalization() -> dict:
    section("PART 1 — Normalization & Entity Resolution Benchmark")
    from benchmark.benchmark_normalization import run_benchmark, print_report, save_results
    from app.services.normalizer import CommodityNormalizer

    normalizer = CommodityNormalizer()
    results = run_benchmark(normalizer)
    print_report(results)
    save_results(results, RESULTS_DIR / "normalization_results.json")
    return results


def run_anomaly() -> dict:
    section("PART 2 — Statistical Anomaly Detection Benchmark")
    from benchmark.benchmark_anomaly import run_benchmark, print_report, save_results

    results = run_benchmark()
    print_report(results)
    save_results(results, RESULTS_DIR / "anomaly_results.json")
    return results


def run_latency() -> dict:
    section("PART 3 — REST API Latency Profiling")
    from benchmark.benchmark_latency import run_benchmark, print_report, save_results

    results = run_benchmark()
    print_report(results)
    save_results(results, RESULTS_DIR / "latency_results.json")
    return results


def build_summary(norm: dict, anomaly: dict, latency: dict) -> dict:
    """Assemble the combined machine-readable summary for CI artifacts."""
    ov_norm = norm.get("Overall", {})
    an_res = anomaly.get("results", anomaly)
    lat_eps = latency.get("endpoints", latency.get("results", {}).get("endpoints", []))

    # Best latency: GET /commodities
    commodities_ep = next((e for e in lat_eps if "commodities" in e.get("endpoint", "") and "history" not in e.get("endpoint", "") and "compare" not in e.get("endpoint", "")), {})

    return {
        "normalization": {
            "sample_size": ov_norm.get("sample_size"),
            "precision_pct": ov_norm.get("precision"),
            "recall_pct": ov_norm.get("recall"),
            "f1_score": ov_norm.get("f1_score"),
            "avg_latency_ms": ov_norm.get("avg_latency_ms"),
        },
        "anomaly_detection": {
            "total_scenarios": an_res.get("total_scenarios", an_res.get("total", None)),
            "passed": an_res.get("passed"),
            "failed": an_res.get("failed"),
            "accuracy_pct": an_res.get("accuracy_pct"),
        },
        "latency": {
            "mode": latency.get("mode", "live"),
            "iterations_per_endpoint": latency.get("iterations_per_endpoint", 100),
            "commodities_p95_ms": commodities_ep.get("p95_ms"),
            "commodities_p99_ms": commodities_ep.get("p99_ms"),
        },
    }


def print_summary(summary: dict) -> None:
    section("COMBINED BENCHMARK SUMMARY — PricePulse BD Milestone 008")
    n = summary["normalization"]
    a = summary["anomaly_detection"]
    l = summary["latency"]

    print(f"\n  Normalization Engine:")
    print(f"    Precision : {n['precision_pct']}%")
    print(f"    Recall    : {n['recall_pct']}%")
    print(f"    F1-Score  : {n['f1_score']}")
    print(f"    Avg Latency: {n['avg_latency_ms']} ms")

    print(f"\n  Anomaly Detection Engine:")
    print(f"    Scenarios : {a['total_scenarios']}  Passed: {a['passed']}  Failed: {a['failed']}")
    print(f"    Accuracy  : {a['accuracy_pct']}%")

    print(f"\n  REST API (GET /commodities, {l['iterations_per_endpoint']} requests):")
    print(f"    P95 Latency: {l['commodities_p95_ms']} ms")
    print(f"    P99 Latency: {l['commodities_p99_ms']} ms")
    print(f"    Mode: {l['mode']}")
    print()


if __name__ == "__main__":
    overall_start = time.perf_counter()

    norm_results = run_normalization()
    anomaly_results = run_anomaly()
    latency_results = run_latency()

    summary = build_summary(norm_results, anomaly_results, latency_results)
    print_summary(summary)

    out_path = RESULTS_DIR / "combined_summary.json"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  Combined summary saved -> {out_path}")

    elapsed = time.perf_counter() - overall_start
    print(f"\n  Total benchmark time: {elapsed:.2f}s")
