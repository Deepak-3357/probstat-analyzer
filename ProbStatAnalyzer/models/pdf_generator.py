from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from scipy import stats


def _p(text: object) -> str:
    return escape(str(text))


def _formula_text(text: object) -> str:
    replacements = {
        r"\lambda": "lambda",
        r"\mu": "mu",
        r"\sigma": "sigma",
        r"\pi": "pi",
        r"\sqrt": "sqrt",
        r"\frac": "frac",
        r"\sum": "sum",
        r"\le": "<=",
        r"\ge": ">=",
        r"\quad": " ",
        r"\exp": "exp",
        r"\binom": "C",
        r"\text": "",
        r"\operatorname": "",
    }
    value = str(text)
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = value.replace("{", "(").replace("}", ")")
    value = re.sub(r"frac\(([^()]+)\)\(([^()]+)\)", r"(\1) / (\2)", value)
    return value


def _figure_image(series: pd.Series, title: str, kind: str, best: dict | None = None) -> Image:
    fig, ax = plt.subplots(figsize=(6.7, 3.2), dpi=140)
    values = series.to_numpy()
    if kind == "hist":
        ax.hist(values, bins=25, color="#2563eb", alpha=0.75, density=True)
    elif kind == "box":
        ax.boxplot(values, vert=False)
    elif kind == "ecdf":
        sorted_values = np.sort(values)
        ax.plot(sorted_values, np.arange(1, len(sorted_values) + 1) / len(sorted_values), color="#0f766e")
    elif kind == "pdf" and best:
        x = np.linspace(float(series.min()), float(series.max()), 300)
        dist = getattr(stats, best["name"])
        y = dist.pmf(np.rint(x), *best["params"]) if best["name"] in {"poisson", "binom", "geom"} else dist.pdf(x, *best["params"])
        ax.plot(x, y, color="#dc2626", linewidth=2)
    ax.set_title(title)
    ax.grid(alpha=0.25)
    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return Image(buffer, width=6.7 * inch, height=3.2 * inch)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(inch, 0.45 * inch, "ProbStat Analyzer")
    canvas.drawRightString(doc.pagesize[0] - inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf_report(path: Path, dataset: dict, analysis: dict, series: pd.Series, probability: dict | None) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=landscape(letter), rightMargin=40, leftMargin=40, topMargin=45, bottomMargin=45)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("ProbStat Analyzer Report", styles["Title"]),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Uploaded File: {dataset['original_name']}", styles["Normal"]),
        Paragraph(f"Selected Column: {analysis['column']}", styles["Normal"]),
        Spacer(1, 14),
        Paragraph("Descriptive Statistics", styles["Heading2"]),
    ]

    stats_rows = [["Statistic", "Full Form", "Definition", "Formula", "Value", "Interpretation"]]
    for group in ("basic", "advanced"):
        for item in analysis["statistic_cards"][group]:
            stats_rows.append([
                Paragraph(_p(item["name"]), styles["Normal"]),
                Paragraph(_p(item["full_form"]), styles["Normal"]),
                Paragraph(_p(item["definition"]), styles["Normal"]),
                Paragraph(_p(item.get("formula_text", item["formula"])), styles["Normal"]),
                Paragraph(_p(item["value"]), styles["Normal"]),
                Paragraph(_p(item["interpretation"]), styles["Normal"]),
            ])
    stats_table = Table(stats_rows, colWidths=[0.9 * inch, 1.35 * inch, 2.25 * inch, 1.6 * inch, 0.8 * inch, 2.3 * inch], repeatRows=1)
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.extend([stats_table, Spacer(1, 16), Paragraph("Best Fitting Distribution", styles["Heading2"])])

    best = analysis["distribution"]["best"]
    explanation = analysis["distribution"].get("explanation", {})
    story.extend([
        Paragraph(_p(f"{best['display_name']} with {best.get('confidence_score', 0)}% confidence score."), styles["Normal"]),
        Paragraph(_p(analysis["distribution"]["reason"]), styles["Normal"]),
        Spacer(1, 10),
        Paragraph("Distribution Comparison", styles["Heading2"]),
    ])

    comparison_rows = [["Distribution", "Type", "Status", "Reason", "KS", "AIC", "BIC", "Rank", "Selected"]]
    for item in analysis["distribution"]["candidates"]:
        comparison_rows.append([
            item["display_name"],
            item["type"].replace(" Distribution", ""),
            item.get("status", "Successfully Fitted"),
            Paragraph(_p(item.get("reason", "")), styles["Normal"]),
            "-" if item.get("status") == "Not Suitable" else f"{item['ks_statistic']:.5f}",
            "-" if item.get("status") == "Not Suitable" else f"{item['aic']:.2f}",
            "-" if item.get("status") == "Not Suitable" else f"{item['bic']:.2f}",
            f"#{item['rank']}" if item.get("rank") else "-",
            "Yes" if item.get("selected") else "No",
        ])
    comparison_table = Table(comparison_rows, colWidths=[1.35 * inch, 0.8 * inch, 1.0 * inch, 2.25 * inch, 0.55 * inch, 0.65 * inch, 0.65 * inch, 0.45 * inch, 0.65 * inch])
    comparison_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.extend([
        comparison_table,
        Spacer(1, 10),
        Paragraph("Analysis Summary", styles["Heading3"]),
        Paragraph(_p(analysis["distribution"].get("analysis_summary", "")), styles["Normal"]),
        Spacer(1, 14),
    ])

    if explanation:
        story.extend([
            Paragraph("Distribution Explanation", styles["Heading2"]),
            Paragraph(_p(f"Detected Dataset Type: {explanation.get('detected_dataset_type', explanation['distribution_type'])}"), styles["Normal"]),
            Paragraph(_p(f"Reason: {explanation.get('detected_dataset_reason', '')}"), styles["Normal"]),
            Paragraph(_p(f"Distribution Type: {explanation['distribution_type']}"), styles["Normal"]),
            Paragraph(_p(f"Best Fitted Distribution: {explanation['best_distribution']}"), styles["Normal"]),
            Paragraph(_p(f"Selection Reason: {explanation['selection_reason']}"), styles["Normal"]),
            Spacer(1, 6),
            Paragraph("Parameter Estimation", styles["Heading3"]),
        ])
        for param in explanation["parameters"]:
            story.append(Paragraph(_p(f"{_formula_text(param['symbol'])} = {param['value']}"), styles["Normal"]))
        story.extend([
            Spacer(1, 6),
            Paragraph(_p(f"{explanation['formula_title']}: {explanation.get('formula_text', _formula_text(explanation['formula']))}"), styles["Normal"]),
            Paragraph(_p(f"Mean Formula: {explanation.get('mean_formula_text', _formula_text(explanation['mean_formula']))}"), styles["Normal"]),
            Paragraph(_p(f"Mean Estimated: {_formula_text(explanation['mean_estimate'])}"), styles["Normal"]),
            Paragraph(_p(f"Variance Formula: {explanation.get('variance_formula_text', _formula_text(explanation['variance_formula']))}"), styles["Normal"]),
            Paragraph(_p(f"Variance Estimated: {_formula_text(explanation['variance_estimate'])}"), styles["Normal"]),
            Paragraph(_p(f"MGF: {explanation.get('mgf_text', _formula_text(explanation['mgf']))}"), styles["Normal"]),
            Paragraph(_p(f"MGF With Estimated Parameters: {_formula_text(explanation['mgf_estimate'])}"), styles["Normal"]),
            Spacer(1, 10),
            Paragraph("Interpretation", styles["Heading3"]),
        ])
        for line in explanation["interpretation"]:
            story.append(Paragraph(_p(f"- {line}"), styles["Normal"]))
        story.append(Spacer(1, 10))

    story.extend([
        Paragraph("Engineering Interpretation", styles["Heading2"]),
    ])
    for insight in analysis["insights"]:
        story.append(Paragraph(_p(f"- {insight}"), styles["Normal"]))

    if probability:
        story.extend([
            Spacer(1, 10),
            Paragraph("Probability Calculation Example", styles["Heading2"]),
            Paragraph(_p(f"{probability['formula']} = {probability['result']}"), styles["Normal"]),
            Paragraph(_p(probability["interpretation"]), styles["Normal"]),
        ])
        for step in probability.get("steps", []):
            story.append(Paragraph(_p(f"{step['label']}: {_formula_text(step['math'])}"), styles["Normal"]))

    story.extend([PageBreak(), Paragraph("Graphs", styles["Heading2"])])
    for title, kind in [
        ("Histogram", "hist"),
        ("Box Plot", "box"),
        ("ECDF", "ecdf"),
        ("Fitted PDF / PMF", "pdf"),
    ]:
        story.extend([_figure_image(series, title, kind, best), Spacer(1, 12)])

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
