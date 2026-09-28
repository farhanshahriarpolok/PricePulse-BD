"""
scripts/run_all_benchmarks.py
=============================
Wrapper to invoke benchmark/run_all_benchmarks.py directly from scripts/.
"""

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    benchmark_script = ROOT_DIR / "benchmark" / "run_all_benchmarks.py"
    cmd = [sys.executable, str(benchmark_script)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd, cwd=str(ROOT_DIR)))
