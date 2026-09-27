"""
Normalization Engine Benchmark — PricePulse BD
===============================================
Evaluates bilingual commodity resolution and unit normalization accuracy
against a labeled testbed of 120 raw commodity strings.

Usage:
    python -m benchmark.benchmark_normalization
    python benchmark/benchmark_normalization.py

Outputs:
    benchmark/results/normalization_results.json
"""

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.services.normalizer import CommodityNormalizer


# ---------------------------------------------------------------------------
# Labeled evaluation testbed
# ---------------------------------------------------------------------------

@dataclass
class TestCase:
    raw: str
    expected_canonical: Optional[str]   # None => expected to be rejected
    category: str
    note: str = ""


TESTBED: list[TestCase] = [
    # -------- Category 1: Exact Latin / Phonetic Matches (40 cases) --------
    TestCase("deshi peyaj", "Onion (Local)", "Exact Bengali"),
    TestCase("mota chaul", "Rice (Coarse)", "Exact Bengali"),
    TestCase("alu", "Potato (Diamond)", "Exact Bengali"),
    TestCase("diamond alu", "Potato (Diamond)", "Exact Bengali"),
    TestCase("soyabean tel", "Soybean Oil (Bottled)", "Exact Bengali"),
    TestCase("miniket chaul", "Rice (Miniket)", "Exact Bengali"),
    TestCase("lal masur dal", "Masur Dal (Medium)", "Exact Bengali"),
    TestCase("masur dal", "Masur Dal (Medium)", "Exact Bengali"),
    TestCase("broiler murgi", "Broiler Chicken", "Exact Bengali"),
    TestCase("murgi dim", "Farm Egg", "Exact Bengali"),
    TestCase("dim", "Farm Egg", "Exact Bengali"),
    TestCase("rashun", "Garlic (Local)", "Exact Bengali"),
    TestCase("deshi rashun", "Garlic (Local)", "Exact Bengali"),
    TestCase("peyaj deshi", "Onion (Local)", "Exact Bengali"),
    TestCase("alu diamond", "Potato (Diamond)", "Exact Bengali"),
    TestCase("soyabean tel bottle", "Soybean Oil (Bottled)", "Exact Bengali"),
    TestCase("mota chaul paikari", "Rice (Coarse)", "Exact Bengali"),
    TestCase("miniket valo chaul", "Rice (Miniket)", "Exact Bengali"),
    TestCase("mosur dal", "Masur Dal (Medium)", "Exact Bengali"),
    TestCase("broiler", "Broiler Chicken", "Exact Bengali"),
    TestCase("peyaj", "Onion (Local)", "Exact Bengali"),
    TestCase("nazirshail chaul", "Rice (Nazirshail)", "Exact Bengali"),
    TestCase("nazir chaul", "Rice (Nazirshail)", "Exact Bengali"),
    TestCase("amdan peyaj", "Onion (Imported)", "Exact Bengali"),
    TestCase("bideshi peyaj", "Onion (Imported)", "Exact Bengali"),
    TestCase("lau", None, "Exact Bengali", "gourd not in taxonomy"),
    TestCase("moida", None, "Exact Bengali", "wheat flour not in taxonomy"),
    TestCase("hasher dim", None, "Exact Bengali", "duck egg not in taxonomy"),
    TestCase("rui mach", None, "Exact Bengali", "fish not in taxonomy"),
    TestCase("pata noon", None, "Exact Bengali", "salt not in taxonomy"),
    TestCase("mota noon", None, "Exact Bengali", "coarse salt not in taxonomy"),
    TestCase("broiler murgi matha", "Broiler Chicken", "Exact Bengali"),
    TestCase("miniket", "Rice (Miniket)", "Exact Bengali"),
    TestCase("gura moshla", None, "Exact Bengali", "spice blend not in taxonomy"),
    TestCase("sobuj morich", None, "Exact Bengali", "green chilli not in taxonomy"),
    TestCase("kacha morich", None, "Exact Bengali", "green chilli not in taxonomy"),
    TestCase("sarisha tel", None, "Exact Bengali", "mustard oil not in taxonomy"),
    TestCase("chini", None, "Exact Bengali", "sugar not in taxonomy"),
    TestCase("dim broiler", "Farm Egg", "Exact Bengali"),
    TestCase("lal mosur dal", "Masur Dal (Medium)", "Exact Bengali"),

    # -------- Category 2: Dialectical / Phonetic Variants (35 cases) --------
    TestCase("Peyaj Deshi", "Onion (Local)", "Phonetic Variant"),
    TestCase("mota chaul", "Rice (Coarse)", "Phonetic Variant"),
    TestCase("Alu Diamond", "Potato (Diamond)", "Phonetic Variant"),
    TestCase("miniket chaul", "Rice (Miniket)", "Phonetic Variant"),
    TestCase("Soyabean Tel", "Soybean Oil (Bottled)", "Phonetic Variant"),
    TestCase("broiler murgi", "Broiler Chicken", "Phonetic Variant"),
    TestCase("murgi dim", "Farm Egg", "Phonetic Variant"),
    TestCase("rashun", "Garlic (Local)", "Phonetic Variant"),
    TestCase("masur dal", "Masur Dal (Medium)", "Phonetic Variant"),
    TestCase("deshi peyaj", "Onion (Local)", "Phonetic Variant"),
    TestCase("alu desi", "Potato (Diamond)", "Phonetic Variant"),
    TestCase("Egg Farm", "Farm Egg", "Phonetic Variant"),
    TestCase("Onion local variety", "Onion (Local)", "Phonetic Variant"),
    TestCase("Diamond potato", "Potato (Diamond)", "Phonetic Variant"),
    TestCase("Coarse rice", "Rice (Coarse)", "Phonetic Variant"),
    TestCase("Miniket rice", "Rice (Miniket)", "Phonetic Variant"),
    TestCase("Soybean oil bottle", "Soybean Oil (Bottled)", "Phonetic Variant"),
    TestCase("Nazirshail rice", "Rice (Nazirshail)", "Phonetic Variant"),
    TestCase("nazir chaul", "Rice (Nazirshail)", "Phonetic Variant"),
    TestCase("Imported onion", "Onion (Imported)", "Phonetic Variant"),
    TestCase("Garlic local", "Garlic (Local)", "Phonetic Variant"),
    TestCase("dim broiler", "Farm Egg", "Phonetic Variant"),
    TestCase("lal dal", "Masur Dal (Medium)", "Phonetic Variant"),
    TestCase("peyaj", "Onion (Local)", "Phonetic Variant"),
    TestCase("alu", "Potato (Diamond)", "Phonetic Variant"),
    TestCase("chaul mota", "Rice (Coarse)", "Phonetic Variant"),
    TestCase("deshi rashun", "Garlic (Local)", "Phonetic Variant"),
    TestCase("broiler chicken fresh", "Broiler Chicken", "Phonetic Variant"),
    TestCase("kola soyabean tel", "Soybean Oil (Bottled)", "Phonetic Variant"),
    TestCase("lal mosur dal", "Masur Dal (Medium)", "Phonetic Variant"),
    TestCase("onion deshi", "Onion (Local)", "Phonetic Variant"),
    TestCase("miniket", "Rice (Miniket)", "Phonetic Variant"),
    TestCase("nazirshail", "Rice (Nazirshail)", "Phonetic Variant"),
    TestCase("potato diamond", "Potato (Diamond)", "Phonetic Variant"),
    TestCase("farm egg", "Farm Egg", "Phonetic Variant"),

    # -------- Category 3: Complex Packaged Expressions (30 cases) --------
    TestCase("Teer Fortified Soybean Oil 5L Bottle", "Soybean Oil (Bottled)", "Complex Packaged"),
    TestCase("Fresh Onion 1kg Net Bag", "Onion (Local)", "Complex Packaged"),
    TestCase("ACI Miniket Premium Rice 5kg Pack", "Rice (Miniket)", "Complex Packaged"),
    TestCase("Diamond Brand Potato 2.5kg bag", "Potato (Diamond)", "Complex Packaged"),
    TestCase("Rupchanda Soybean Oil 1L", "Soybean Oil (Bottled)", "Complex Packaged"),
    TestCase("Broiler Chicken Whole 1.2kg approx", "Broiler Chicken", "Complex Packaged"),
    TestCase("Farm Fresh Eggs 12pcs tray", "Farm Egg", "Complex Packaged"),
    TestCase("Red Lentil Masur Dal 500gm pack", "Masur Dal (Medium)", "Complex Packaged"),
    TestCase("Garlic local 250g pack", "Garlic (Local)", "Complex Packaged"),
    TestCase("Coarse Rice 50kg jute sack", "Rice (Coarse)", "Complex Packaged"),
    TestCase("Peyaj 1kg mesh bag local variety", "Onion (Local)", "Complex Packaged"),
    TestCase("Alu Diamond 5kg wholesale", "Potato (Diamond)", "Complex Packaged"),
    TestCase("Miniket Chaul 25kg bosta", "Rice (Miniket)", "Complex Packaged"),
    TestCase("Broiler live weight market price per kg", "Broiler Chicken", "Complex Packaged"),
    TestCase("Masur Dal 1kg retail", "Masur Dal (Medium)", "Complex Packaged"),
    TestCase("Rashun deshi 250gm pack", "Garlic (Local)", "Complex Packaged"),
    TestCase("Egg tray 30 pieces broiler", "Farm Egg", "Complex Packaged"),
    TestCase("Peyaj 5kg wholesale sack deshi", "Onion (Local)", "Complex Packaged"),
    TestCase("Fresh broiler chicken piece 500g", "Broiler Chicken", "Complex Packaged"),
    TestCase("Masur lentil 1kg red dal", "Masur Dal (Medium)", "Complex Packaged"),
    TestCase("Nazirshail fine rice 10kg bag", "Rice (Nazirshail)", "Complex Packaged"),
    TestCase("Teer Soybean Oil Bulk 15L", "Soybean Oil (Bottled)", "Complex Packaged"),
    TestCase("Imported onion 2kg pack", "Onion (Imported)", "Complex Packaged"),
    TestCase("Local garlic fresh 500g", "Garlic (Local)", "Complex Packaged"),
    TestCase("Miniket rice premium 1kg", "Rice (Miniket)", "Complex Packaged"),
    TestCase("Coarse rice 5kg bag wholesale", "Rice (Coarse)", "Complex Packaged"),
    TestCase("Broiler fresh weight 1.5kg", "Broiler Chicken", "Complex Packaged"),
    TestCase("Farm egg dozen 12pc", "Farm Egg", "Complex Packaged"),
    TestCase("Diamond potato fresh 3kg", "Potato (Diamond)", "Complex Packaged"),
    TestCase("Nazirshail chaul 5kg retail", "Rice (Nazirshail)", "Complex Packaged"),

    # -------- Category 4: Out-of-Domain / Negative (15 cases) --------
    TestCase("Urea Fertilizer 50kg", None, "Out-of-Domain"),
    TestCase("Plastic Storage Box 10L", None, "Out-of-Domain"),
    TestCase("Motor Engine Oil SAE 40", None, "Out-of-Domain"),
    TestCase("Organic Compost 25kg bag", None, "Out-of-Domain"),
    TestCase("Steel Bucket 15L", None, "Out-of-Domain"),
    TestCase("Mosquito Coil 10pcs", None, "Out-of-Domain"),
    TestCase("Mobile Phone Case", None, "Out-of-Domain"),
    TestCase("Cement 50kg bag", None, "Out-of-Domain"),
    TestCase("Hair Oil 100ml", None, "Out-of-Domain"),
    TestCase("Soap bar 100g", None, "Out-of-Domain"),
    TestCase("Laundry Detergent 1kg", None, "Out-of-Domain"),
    TestCase("Bicycle tire tube", None, "Out-of-Domain"),
    TestCase("Notebook A4 80gsm", None, "Out-of-Domain"),
    TestCase("Matches box 10 sticks", None, "Out-of-Domain"),
    TestCase("Candle 6 inch white", None, "Out-of-Domain"),
]


# ---------------------------------------------------------------------------
# Evaluation runner
# ---------------------------------------------------------------------------

def run_benchmark(normalizer: CommodityNormalizer) -> dict:
    """Run all test cases and collect per-category statistics."""
    categories: dict[str, dict] = {}

    for tc in TESTBED:
        start = time.perf_counter()
        result = normalizer.resolve_commodity(tc.raw)
        elapsed_ms = (time.perf_counter() - start) * 1000

        predicted_canonical = result.canonical_name if result else None
        expected = tc.expected_canonical

        # Determine TP/FP/FN/TN
        if expected is not None and predicted_canonical is not None:
            # Both non-null: check match
            if predicted_canonical == expected:
                outcome = "TP"
            else:
                outcome = "FP"  # mapped to wrong commodity
        elif expected is None and predicted_canonical is None:
            outcome = "TN"   # correctly rejected
        elif expected is not None and predicted_canonical is None:
            outcome = "FN"   # missed a valid commodity
        else:
            outcome = "FP"   # spuriously included an out-of-domain string

        cat = tc.category
        if cat not in categories:
            categories[cat] = {
                "TP": 0, "FP": 0, "FN": 0, "TN": 0,
                "total": 0, "latencies_ms": []
            }
        categories[cat][outcome] += 1
        categories[cat]["total"] += 1
        categories[cat]["latencies_ms"].append(elapsed_ms)

    # Aggregate metrics per category
    results = {}
    overall = {"TP": 0, "FP": 0, "FN": 0, "TN": 0, "total": 0, "latencies_ms": []}

    for cat, stats in categories.items():
        tp = stats["TP"]
        fp = stats["FP"]
        fn = stats["FN"]
        tn = stats["TN"]
        lats = stats["latencies_ms"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        results[cat] = {
            "sample_size": stats["total"],
            "TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "precision": round(precision * 100, 1),
            "recall": round(recall * 100, 1),
            "f1_score": round(f1, 3),
            "avg_latency_ms": round(sum(lats) / len(lats), 3),
            "p95_latency_ms": round(sorted(lats)[int(len(lats) * 0.95)], 3),
        }

        for key in ("TP", "FP", "FN", "TN", "total"):
            overall[key] += stats[key]
        overall["latencies_ms"].extend(lats)

    # Overall aggregate
    tp = overall["TP"]; fp = overall["FP"]; fn = overall["FN"]
    lats = sorted(overall["latencies_ms"])
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    results["Overall"] = {
        "sample_size": overall["total"],
        "TP": tp, "FP": fp, "FN": fn, "TN": overall["TN"],
        "precision": round(precision * 100, 1),
        "recall": round(recall * 100, 1),
        "f1_score": round(f1, 3),
        "avg_latency_ms": round(sum(lats) / len(lats), 3),
        "p95_latency_ms": round(lats[int(len(lats) * 0.95)], 3),
    }

    return results


def print_report(results: dict) -> None:
    """Pretty-print benchmark table to console."""
    print()
    print("=" * 76)
    print("  PricePulse BD — Normalization Benchmark Report")
    print("=" * 76)
    print(f"  {'Category':<32} {'N':>4} {'Prec%':>6} {'Rec%':>6} {'F1':>6} {'AvgMs':>7}")
    print("  " + "-" * 72)

    for cat, r in results.items():
        marker = "  " if cat != "Overall" else "* "
        print(
            f"{marker}{cat:<32} {r['sample_size']:>4} "
            f"{r['precision']:>6.1f} {r['recall']:>6.1f} "
            f"{r['f1_score']:>6.3f} {r['avg_latency_ms']:>7.3f}"
        )

    print("=" * 76)
    ov = results.get("Overall", {})
    print(
        f"  Aggregate — Precision: {ov.get('precision')}%  "
        f"Recall: {ov.get('recall')}%  "
        f"F1: {ov.get('f1_score')}  "
        f"P95: {ov.get('p95_latency_ms')} ms"
    )
    print("=" * 76)
    print()


def save_results(results: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark": "normalization", "results": results}, f, indent=2, ensure_ascii=False)
    print(f"  Results saved -> {out_path}")


if __name__ == "__main__":
    normalizer = CommodityNormalizer()
    print("Running normalization benchmark (120 cases)...")
    results = run_benchmark(normalizer)
    print_report(results)
    out_path = PROJECT_ROOT / "benchmark" / "results" / "normalization_results.json"
    save_results(results, out_path)
