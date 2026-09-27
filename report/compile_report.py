"""
LaTeX Thesis Compilation Script — PricePulse BD
================================================
Automates PDF generation from the LaTeX source in report/ using
pdflatex (primary) or xelatex (fallback). Runs the bibtex pass
and two follow-up pdflatex compilations for cross-reference resolution.

Usage:
    python report/compile_report.py
    python report/compile_report.py --engine xelatex
    python report/compile_report.py --open   (opens PDF after build)

Requirements:
    A working TeX distribution must be installed:
      - Windows: MiKTeX (https://miktex.org/) or TeX Live
      - Check: pdflatex --version
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
MAIN_TEX = REPORT_DIR / "main.tex"
OUTPUT_PDF = REPORT_DIR / "main.pdf"
BUILD_DIR = REPORT_DIR / "_build"


def find_engine(preferred: str) -> str:
    """Locate the preferred TeX engine or fall back gracefully."""
    if shutil.which(preferred):
        return preferred
    fallbacks = ["pdflatex", "xelatex", "lualatex"]
    for eng in fallbacks:
        if shutil.which(eng):
            print(f"  [WARN] '{preferred}' not found — using '{eng}'.")
            return eng
    print(
        "  [ERROR] No LaTeX engine found. Install MiKTeX or TeX Live first.\n"
        "          MiKTeX: https://miktex.org/download"
    )
    sys.exit(1)


def run_latex(engine: str, tex_file: Path, cwd: Path) -> subprocess.CompletedProcess:
    cmd = [
        engine,
        "-interaction=nonstopmode",
        "-output-directory", str(BUILD_DIR),
        str(tex_file),
    ]
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def run_bibtex(cwd: Path) -> None:
    if shutil.which("bibtex"):
        aux_file = BUILD_DIR / "main.aux"
        if aux_file.exists():
            subprocess.run(["bibtex", str(aux_file)], cwd=cwd, capture_output=True)


def check_log_for_errors(log_path: Path) -> list[str]:
    """Extract LaTeX error lines from the build log."""
    errors = []
    if not log_path.exists():
        return errors
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("!") or "LaTeX Error" in line:
                errors.append(line.rstrip())
    return errors


def compile_report(engine: str, open_after: bool) -> None:
    print(f"\n  PricePulse BD — LaTeX Compilation")
    print(f"  Engine  : {engine}")
    print(f"  Source  : {MAIN_TEX.relative_to(PROJECT_ROOT)}")
    print(f"  Output  : {OUTPUT_PDF.relative_to(PROJECT_ROOT)}")
    print()

    if not MAIN_TEX.exists():
        print(f"  [ERROR] Source file not found: {MAIN_TEX}")
        sys.exit(1)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # --- Pass 1: initial compile ---
    print("  Pass 1/3 — Initial compilation...")
    result = run_latex(engine, MAIN_TEX, REPORT_DIR)
    if result.returncode != 0:
        log_path = BUILD_DIR / "main.log"
        errors = check_log_for_errors(log_path)
        if errors:
            print("  [ERROR] LaTeX reported errors:")
            for e in errors[:10]:
                print(f"    {e}")
        else:
            print(f"  [ERROR] Compilation failed (exit code {result.returncode})")
            print(result.stderr[-800:] if result.stderr else "")
        print(f"  Full log: {log_path}")
        sys.exit(1)

    # --- BibTeX pass ---
    print("  Pass 2/3 — Running BibTeX for references...")
    run_bibtex(REPORT_DIR)

    # --- Pass 3: re-compile for cross-references ---
    print("  Pass 3/3 — Final compilation (cross-reference resolution)...")
    run_latex(engine, MAIN_TEX, REPORT_DIR)
    run_latex(engine, MAIN_TEX, REPORT_DIR)  # second pass for TOC/refs

    # Move PDF from build dir to report/
    built_pdf = BUILD_DIR / "main.pdf"
    if built_pdf.exists():
        shutil.copy2(built_pdf, OUTPUT_PDF)
        size_kb = OUTPUT_PDF.stat().st_size // 1024
        print(f"\n  Build complete: {OUTPUT_PDF.relative_to(PROJECT_ROOT)} ({size_kb} KB)")
    else:
        print(f"\n  [ERROR] PDF was not produced. Check {BUILD_DIR / 'main.log'}")
        sys.exit(1)

    log_path = BUILD_DIR / "main.log"
    errors = check_log_for_errors(log_path)
    if errors:
        print(f"\n  [WARN] {len(errors)} LaTeX warning(s)/error(s) detected in log:")
        for e in errors[:5]:
            print(f"    {e}")
    else:
        print("  No errors reported.")

    if open_after:
        _open_file(OUTPUT_PDF)


def _open_file(path: Path) -> None:
    import os
    import platform

    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))
    elif system == "Darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile the PricePulse BD LaTeX thesis to PDF."
    )
    parser.add_argument(
        "--engine",
        default="pdflatex",
        choices=["pdflatex", "xelatex", "lualatex"],
        help="TeX engine to use (default: pdflatex).",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_after",
        help="Open the generated PDF after a successful build.",
    )
    args = parser.parse_args()

    engine = find_engine(args.engine)
    compile_report(engine, args.open_after)


if __name__ == "__main__":
    main()
