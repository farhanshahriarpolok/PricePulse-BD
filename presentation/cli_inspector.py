"""
CLI System Inspector — PricePulse BD
======================================
Interactive terminal-based inspector for viva defense and offline demonstration.
Provides real-time API inspection, anomaly status, and benchmark result display.

Usage:
    python presentation/cli_inspector.py
    python presentation/cli_inspector.py --no-api   (offline mode only)

Requirements:
    FastAPI server running at http://127.0.0.1:8000 (for live mode).
    Python 3.11+ with httpx installed.
"""

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

BASE_URL = "http://127.0.0.1:8000/api/v1"
BENCHMARK_SUMMARY = PROJECT_ROOT / "benchmark" / "results" / "combined_summary.json"


# ---------------------------------------------------------------------------
# Terminal color helpers (ANSI — works on Windows 10+ with VT processing)
# ---------------------------------------------------------------------------

def _enable_ansi_windows():
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    INDIGO = "\033[38;5;105m"
    CYAN   = "\033[38;5;87m"
    GREEN  = "\033[38;5;83m"
    AMBER  = "\033[38;5;214m"
    ROSE   = "\033[38;5;204m"
    WHITE  = "\033[97m"
    GRAY   = "\033[38;5;245m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{C.RESET}"


def header(title: str) -> None:
    bar = "═" * 70
    print(f"\n{c(bar, C.INDIGO)}")
    print(f"  {c(title, C.BOLD + C.WHITE)}")
    print(f"{c(bar, C.INDIGO)}\n")


def sub(title: str) -> None:
    print(f"\n  {c('▶ ' + title, C.CYAN + C.BOLD)}")
    print(f"  {c('─' * 60, C.GRAY)}")


def kv(key: str, value, unit: str = "") -> None:
    v_str = str(value) + (f" {unit}" if unit else "")
    print(f"    {c(key + ':', C.GRAY):<30} {c(v_str, C.WHITE)}")


def badge(label: str, severity: str) -> str:
    colors = {
        "Critical": C.ROSE, "Severe": C.AMBER,
        "Moderate": C.INDIGO, "Normal": C.GREEN,
    }
    col = colors.get(severity, C.GRAY)
    return f"{c('[', C.GRAY)}{c(severity.upper(), col + C.BOLD)}{c(']', C.GRAY)} {label}"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _get(client, path: str, params: dict = None):
    try:
        resp = client.get(f"{BASE_URL}{path}", params=params or {}, timeout=5.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Inspection modules
# ---------------------------------------------------------------------------

def show_commodities(client) -> None:
    sub("Commodity Catalog")
    data = _get(client, "/commodities")
    if "error" in data:
        print(f"    {c('API error: ' + data['error'], C.ROSE)}")
        return
    items = data.get("items", [])
    print(f"    Total registered commodities: {c(str(data.get('total', len(items))), C.AMBER)}\n")
    for item in items[:12]:
        cats = item.get("category", "")
        print(f"    {c(str(item['id']).rjust(3), C.GRAY)}  {c(item['canonical_name'], C.WHITE):<32}  "
              f"{c(item.get('bangla_name',''), C.CYAN):<20}  "
              f"{c('[' + cats + ']', C.GRAY)}")
    if len(items) > 12:
        print(f"    {c(f'... and {len(items)-12} more.', C.GRAY)}")


def show_anomaly_monitor(client) -> None:
    sub("Anomaly Monitor — Today's Market Status")
    data = _get(client, "/anomalies/monitor")
    if "error" in data:
        print(f"    {c('API error: ' + data['error'], C.ROSE)}")
        return
    alerts = data.get("anomalies", [])
    total = data.get("total_commodities", "?")
    flagged = data.get("flagged_count", len(alerts))
    print(f"    Commodities evaluated: {c(str(total), C.WHITE)}  |  Flagged: {c(str(flagged), C.ROSE)}\n")
    if not alerts:
        print(f"    {c('[OK] No anomalies detected — market operating normally.', C.GREEN)}")
        return
    for a in alerts:
        print(f"    {badge(a.get('commodity_name', ''), a.get('severity', 'Normal'))}")
        kv("  Z-Score", a.get("z_score"))
        kv("  Δ% from baseline", a.get("delta_pct"), "%")
        kv("  CV%", a.get("cv_pct"), "%")
        if a.get("explanation"):
            print(f"    {c('Explanation:', C.GRAY)}")
            for line in _wrap(a["explanation"], 66):
                print(f"      {c(line, C.DIM + C.WHITE)}")
        print()


def show_pulse(client) -> None:
    sub(f"Today's Price Pulse ({date.today()})")
    data = _get(client, "/pulse/today")
    if "error" in data:
        print(f"    {c('API error: ' + data['error'], C.ROSE)}")
        return
    items = data.get("items", data.get("pulse", []))
    if not items:
        print(f"    {c('No observations for today. Run: python scripts/generate_demo_history.py', C.AMBER)}")
        return
    print(f"    {'Commodity':<32} {'Market':<20} {'Price':>8} {'Unit':<8} {'Conf':>6}")
    print(f"    {c('-'*76, C.GRAY)}")
    for item in items[:15]:
        name = item.get("canonical_name") or item.get("commodity_name", "")
        mkt = item.get("market_name", "")
        price = item.get("normalized_price") or item.get("price", "")
        unit = item.get("normalized_unit") or item.get("unit", "")
        conf = item.get("confidence_score") or item.get("confidence", "")
        conf_str = f"{float(conf):.2f}" if conf else "—"
        price_str = f"{float(price):.2f}" if price else "—"
        print(f"    {name:<32} {mkt:<20} {c(price_str, C.AMBER):>8} {unit:<8} {c(conf_str, C.CYAN):>6}")


def show_benchmark_summary() -> None:
    sub("Benchmark Results Summary")
    if not BENCHMARK_SUMMARY.exists():
        print(f"    {c('No benchmark results found.', C.AMBER)}")
        print(f"    Run: {c('python benchmark/run_all_benchmarks.py', C.CYAN)}")
        return
    with open(BENCHMARK_SUMMARY, "r", encoding="utf-8") as f:
        s = json.load(f)

    n = s.get("normalization", {})
    a = s.get("anomaly_detection", {})
    l = s.get("latency", {})

    print(f"    {c('Normalization Engine', C.BOLD + C.WHITE)}")
    kv("  Sample Size", n.get("sample_size", 120))
    kv("  Precision", n.get("precision_pct"), "%")
    kv("  Recall", n.get("recall_pct"), "%")
    kv("  F1-Score", n.get("f1_score"))
    kv("  Avg Latency", n.get("avg_latency_ms"), "ms")

    print(f"\n    {c('Anomaly Detection Engine', C.BOLD + C.WHITE)}")
    kv("  Scenarios", a.get("total_scenarios"))
    kv("  Passed", a.get("passed"))
    kv("  Accuracy", a.get("accuracy_pct"), "%")

    print(f"\n    {c('REST API Latency (GET /commodities)', C.BOLD + C.WHITE)}")
    kv("  P95 Latency", l.get("commodities_p95_ms"), "ms")
    kv("  P99 Latency", l.get("commodities_p99_ms"), "ms")
    kv("  Mode", l.get("mode"))


def show_source_health(client) -> None:
    sub("Data Source Health")
    data = _get(client, "/system/sources")
    if "error" in data:
        print(f"    {c('API error: ' + data['error'], C.ROSE)}")
        return
    sources = data.get("sources", [])
    for src in sources:
        status = src.get("status", "unknown")
        sc = C.GREEN if status == "healthy" else (C.AMBER if status == "degraded" else C.ROSE)
        print(f"    {c('[' + status.upper() + ']', sc + C.BOLD):>18}  {src.get('name', '')} "
              f"{c('(' + src.get('code', '') + ')', C.GRAY)}")
        kv("  Success rate", src.get("success_rate"), "%")
        kv("  Last fetch", src.get("last_fetch_at", "never"))
        print()


def _wrap(text: str, width: int) -> list:
    """Basic word wrap."""
    words = text.split()
    lines = []
    line = []
    length = 0
    for w in words:
        if length + len(w) + 1 > width:
            lines.append(" ".join(line))
            line = [w]
            length = len(w)
        else:
            line.append(w)
            length += len(w) + 1
    if line:
        lines.append(" ".join(line))
    return lines


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

MENU = [
    ("1", "Commodity Catalog",       "show_commodities"),
    ("2", "Today's Price Pulse",     "show_pulse"),
    ("3", "Anomaly Monitor",         "show_anomaly_monitor"),
    ("4", "Source Health",           "show_source_health"),
    ("5", "Benchmark Results",       "show_benchmark_summary"),
    ("q", "Quit",                    None),
]


def print_menu(api_available: bool) -> None:
    header("PricePulse BD — Viva CLI Inspector")
    mode_label = c("LIVE API", C.GREEN + C.BOLD) if api_available else c("OFFLINE", C.AMBER + C.BOLD)
    print(f"  Mode: {mode_label}  |  Backend: {c(BASE_URL, C.GRAY)}\n")
    for key, label, _ in MENU:
        suffix = c("  [API required]", C.GRAY) if _ in ("show_commodities", "show_pulse", "show_anomaly_monitor", "show_source_health") and not api_available else ""
        print(f"    {c('[' + key + ']', C.INDIGO + C.BOLD)}  {label}{suffix}")
    print()


def check_api() -> bool:
    if not HTTPX_AVAILABLE:
        return False
    try:
        with httpx.Client(timeout=3.0) as c:
            c.get(f"{BASE_URL}/commodities")
        return True
    except Exception:
        return False


def main():
    _enable_ansi_windows()
    api_available = check_api()

    client = None
    if api_available and HTTPX_AVAILABLE:
        client = httpx.Client(timeout=10.0)

    try:
        while True:
            print_menu(api_available)
            choice = input(f"  {c('Select option:', C.WHITE)} ").strip().lower()
            print()

            if choice == "q":
                print(f"  {c('Goodbye.', C.GRAY)}\n")
                break
            elif choice == "1":
                if client:
                    show_commodities(client)
                else:
                    print(f"  {c('API not available.', C.AMBER)} Start the server with: python run_system.py")
            elif choice == "2":
                if client:
                    show_pulse(client)
                else:
                    print(f"  {c('API not available.', C.AMBER)}")
            elif choice == "3":
                if client:
                    show_anomaly_monitor(client)
                else:
                    print(f"  {c('API not available.', C.AMBER)}")
            elif choice == "4":
                if client:
                    show_source_health(client)
                else:
                    print(f"  {c('API not available.', C.AMBER)}")
            elif choice == "5":
                show_benchmark_summary()
            else:
                print(f"  {c('Invalid option.', C.ROSE)}")

            input(f"\n  {c('Press Enter to continue...', C.GRAY)}")

    finally:
        if client:
            client.close()


if __name__ == "__main__":
    main()
