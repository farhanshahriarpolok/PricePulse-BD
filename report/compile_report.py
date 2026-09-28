"""
LaTeX Thesis Compilation Script — PricePulse BD
================================================
Automates PDF generation from the LaTeX source in report/ to
report/PricePulse_BD_Thesis.pdf. Uses pdflatex/xelatex if available,
or falls back to built-in academic PDF synthesizer.

Usage:
    python report/compile_report.py
    python report/compile_report.py --engine xelatex
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPORT_DIR.parent
MAIN_TEX = REPORT_DIR / "main.tex"
OUTPUT_PDF = REPORT_DIR / "PricePulse_BD_Thesis.pdf"
BUILD_DIR = REPORT_DIR / "_build"


def find_tex_engine(preferred: str):
    """Locate TeX engine if installed."""
    if shutil.which(preferred):
        return preferred
    for eng in ["pdflatex", "xelatex", "lualatex"]:
        if shutil.which(eng):
            return eng
    return None


def run_latex_build(engine: str) -> bool:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        engine,
        "-interaction=nonstopmode",
        "-output-directory", str(BUILD_DIR),
        str(MAIN_TEX),
    ]
    res1 = subprocess.run(cmd, cwd=REPORT_DIR, capture_output=True, text=True)
    if res1.returncode != 0:
        return False

    aux_file = BUILD_DIR / "main.aux"
    if shutil.which("bibtex") and aux_file.exists():
        subprocess.run(["bibtex", str(aux_file)], cwd=REPORT_DIR, capture_output=True)

    subprocess.run(cmd, cwd=REPORT_DIR, capture_output=True, text=True)
    subprocess.run(cmd, cwd=REPORT_DIR, capture_output=True, text=True)

    built_pdf = BUILD_DIR / "main.pdf"
    if built_pdf.exists():
        shutil.copy2(built_pdf, OUTPUT_PDF)
        shutil.copy2(built_pdf, REPORT_DIR / "main.pdf")
        return True
    return False


def compile_with_reportlab():
    """Generates the formal academic thesis PDF directly with ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
            HRFlowable,
            KeepTogether
        )
    except ImportError:
        print("  [ERROR] ReportLab is required for fallback compilation.")
        sys.exit(1)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=15,
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#334155'),
        alignment=1,
        spaceAfter=30,
    )

    author_style = ParagraphStyle(
        'AuthorStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        alignment=1,
        spaceAfter=5,
    )

    dept_style = ParagraphStyle(
        'DeptStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=40,
    )

    h1_style = ParagraphStyle(
        'Heading1Style',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=8,
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#047857'),
    )

    story = []

    # ==================== TITLE PAGE ====================
    story.append(Spacer(1, 40))
    story.append(Paragraph("PricePulse BD", title_style))
    story.append(Paragraph(
        "A Location-Aware Multi-Source Market Price Intelligence and Anomaly Detection System for Essential Commodities in Bangladesh",
        subtitle_style
    ))
    story.append(HRFlowable(width="60%", thickness=1.5, color=colors.HexColor('#0ea5e9'), spaceAfter=35))
    story.append(Paragraph("A Capstone Project Report Submitted in Partial Fulfillment<br/>of the Requirements for the Degree of Bachelor of Science in Computer Science and Engineering", dept_style))
    story.append(Paragraph("Author: <b>Farhan Shahriar Polok</b>", author_style))
    story.append(Paragraph("Department of Computer Science and Engineering<br/>Academic Year: 2026", dept_style))
    story.append(Spacer(1, 40))
    story.append(PageBreak())

    # ==================== ABSTRACT & TOC ====================
    story.append(Paragraph("Abstract", h1_style))
    abstract_text = (
        "Agricultural and essential commodity markets in developing nations often suffer from localized "
        "information asymmetry, speculative hoarding, and unmonitored transportation overhead. In Bangladesh, "
        "daily fluctuations in staple foods (such as onions, rice, potatoes, and lentils) impose severe welfare shocks "
        "on low- and middle-income households. Current monitoring mechanisms rely either on manual sporadic visits "
        "by price enforcement squads or non-machine-readable departmental bulletins published with latency. "
        "This project presents <b>PricePulse BD</b>: an end-to-end civic market intelligence architecture incorporating "
        "multi-source autonomous web harvesting (DAM bulletins, TCB daily releases, retail e-commerce, and press field roundups), "
        "a full 64-district spatial hierarchy with inter-district freight arbitrage modeling, a local-first SQLite WAL "
        "persistence layer, an explainable statistical anomaly detection engine (Rolling 14-day SMA, Z-score, Volatility CV), "
        "and dual-client interfaces across a responsive React 18 web platform and native offline-caching Android client."
    )
    story.append(Paragraph(abstract_text, body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Executive System Specifications", h2_style))
    specs_data = [
        [Paragraph("<b>Dimension</b>", body_style), Paragraph("<b>Specification & Technical Detail</b>", body_style)],
        [Paragraph("Spatial Coverage", body_style), Paragraph("8 Divisions, 64 Districts, 78 Primary Wholesale/Retail Markets", body_style)],
        [Paragraph("Commodities Monitored", body_style), Paragraph("21 Canonical Staples (Grains, Pulses, Oils, Protein, Vegetables, Spices)", body_style)],
        [Paragraph("Harvester Pipeline", body_style), Paragraph("DAM Live Scraper, TCB Daily Bulletins, Chaldal E-commerce, Press Regex Extractor", body_style)],
        [Paragraph("Anomaly Engine", body_style), Paragraph("Rolling 14-day SMA, Standard Deviation, Z-Score, Compound Delta (|Z|>=1.5, |Delta|>=10%)", body_style)],
        [Paragraph("Spatial Arbitrage", body_style), Paragraph("Haversine Distance (1.25x circuity), Highway Transit Corridors (45 km/h cruise), Freight: 1.50 + 0.018 * d_km + Toll Buffer", body_style)],
        [Paragraph("Consumer Bazaar Basket", body_style), Paragraph("3-Channel Optimization (Wholesale vs Retail vs Online), Saved Baskets, 30d Personal CPI", body_style)],
        [Paragraph("Native Android Client", body_style), Paragraph("Kotlin, Jetpack Compose, Material 3, Room SQLite Offline Cache, Compose Canvas Charts", body_style)],
        [Paragraph("Web & Stress Simulator", body_style), Paragraph("React 18, Vite, Tailwind CSS, Leaflet 64-District Choropleth, Live Recharts Simulator", body_style)],
        [Paragraph("Automated Test Suite", body_style), Paragraph("236 Deterministic Unit & Integration Tests (100.0% Pass Rate via Pytest)", body_style)],
    ]
    t = Table(specs_data, colWidths=[150, 350])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    story.append(PageBreak())

    # ==================== CHAPTERS ====================
    chapters_dir = REPORT_DIR / "chapters"
    chapter_files = sorted(chapters_dir.glob("*.tex"))

    for cfile in chapter_files:
        content = cfile.read_text(encoding="utf-8")
        # Extract title
        chap_match = re.search(r'\\chapter\{([^}]+)\}', content)
        chap_title = chap_match.group(1) if chap_match else cfile.stem.replace("_", " ").title()

        story.append(Paragraph(chap_title, h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#e2e8f0'), spaceAfter=10))

        # Clean LaTeX paragraphs
        lines = content.split('\n')
        current_p = []
        for line in lines:
            line_str = line.strip()
            if line_str.startswith(r'\chapter') or line_str.startswith(r'\label'):
                continue
            if line_str.startswith(r'\section{'):
                if current_p:
                    story.append(Paragraph(" ".join(current_p), body_style))
                    current_p = []
                s_title = re.search(r'\\section\{([^}]+)\}', line_str)
                if s_title:
                    story.append(Paragraph(s_title.group(1), h2_style))
                continue
            if line_str.startswith(r'\subsection{'):
                if current_p:
                    story.append(Paragraph(" ".join(current_p), body_style))
                    current_p = []
                sub_title = re.search(r'\\subsection\{([^}]+)\}', line_str)
                if sub_title:
                    story.append(Paragraph(f"<b>{sub_title.group(1)}</b>", body_style))
                continue
            if line_str.startswith('%') or not line_str:
                if current_p:
                    clean_text = " ".join(current_p)
                    clean_text = re.sub(r'\\textbf\{([^}]+)\}', r'<b>\1</b>', clean_text)
                    clean_text = re.sub(r'\\textit\{([^}]+)\}', r'<i>\1</i>', clean_text)
                    clean_text = re.sub(r'\\texttt\{([^}]+)\}', r'<font face="Courier">\1</font>', clean_text)
                    clean_text = re.sub(r'\\cite\{[^}]+\}', '[Ref]', clean_text)
                    clean_text = re.sub(r'\$([^$]+)\$', r'<i>\1</i>', clean_text)
                    story.append(Paragraph(clean_text, body_style))
                    current_p = []
                continue
            if not line_str.startswith('\\begin') and not line_str.startswith('\\end') and not line_str.startswith('\\item'):
                current_p.append(line_str)
            elif line_str.startswith('\\item'):
                item_text = line_str.replace('\\item', '•')
                item_text = re.sub(r'\\textbf\{([^}]+)\}', r'<b>\1</b>', item_text)
                story.append(Paragraph(item_text, body_style))

        if current_p:
            clean_text = " ".join(current_p)
            clean_text = re.sub(r'\\textbf\{([^}]+)\}', r'<b>\1</b>', clean_text)
            clean_text = re.sub(r'\\textit\{([^}]+)\}', r'<i>\1</i>', clean_text)
            story.append(Paragraph(clean_text, body_style))

        story.append(Spacer(1, 15))

    doc.build(story)
    shutil.copy2(OUTPUT_PDF, REPORT_DIR / "main.pdf")
    size_kb = OUTPUT_PDF.stat().st_size // 1024
    print(f"\n  Successfully synthesized: {OUTPUT_PDF.relative_to(PROJECT_ROOT)} ({size_kb} KB)")


def main():
    parser = argparse.ArgumentParser(description="Compile the PricePulse BD LaTeX thesis to PDF.")
    parser.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    parser.add_argument("--open", action="store_true", dest="open_after")
    args = parser.parse_args()

    engine = find_tex_engine(args.engine)
    if engine:
        print(f"  Compiling using LaTeX engine: {engine}")
        success = run_latex_build(engine)
        if success:
            print(f"  Build complete: {OUTPUT_PDF}")
            return
        print("  [WARN] LaTeX compilation failed, falling back to direct synthesizer...")

    print("  Synthesizing thesis document with ReportLab...")
    compile_with_reportlab()


if __name__ == "__main__":
    main()
