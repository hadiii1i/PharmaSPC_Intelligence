"""
PDF Report Generator for PharmaSPC Intelligence.

Generates a professional quality report using ReportLab.
The report includes process information, statistical summary,
capability indices, detected SPC rules, and recommendations.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import List, Dict
import datetime
import io


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLOR_PRIMARY = colors.HexColor("#2d3250")
COLOR_ACCENT = colors.HexColor("#4a90d9")
COLOR_SUCCESS = colors.HexColor("#276749")
COLOR_WARNING = colors.HexColor("#744210")
COLOR_DANGER = colors.HexColor("#742a2a")
COLOR_LIGHT = colors.HexColor("#f7fafc")
COLOR_BORDER = colors.HexColor("#e2e8f0")


def _build_styles() -> dict:
    """Build and return custom paragraph styles for the report."""
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=22,
            textColor=COLOR_PRIMARY,
            spaceAfter=4,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#718096"),
            spaceAfter=16,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "SectionHeader",
            parent=base["Normal"],
            fontSize=12,
            textColor=COLOR_PRIMARY,
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#2d3748"),
            spaceAfter=4,
            leading=14,
        ),
        "finding": ParagraphStyle(
            "Finding",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#2d3748"),
            spaceAfter=4,
            leading=14,
            leftIndent=10,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#718096"),
            spaceAfter=2,
        ),
    }
    return styles


def _section_header(text: str, styles: dict) -> list:
    """Return a styled section header with a horizontal rule."""
    return [
        Paragraph(text, styles["section"]),
        HRFlowable(
            width="100%",
            thickness=1,
            color=COLOR_BORDER,
            spaceAfter=6,
        ),
    ]


def _stats_table(stats: dict, limits: dict) -> Table:
    """Build the statistical summary table."""
    data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Mean", f"{stats['mean']:.4f}",
         "UCL (3σ)", f"{limits['ucl']:.4f}"],
        ["Std Dev (σ)", f"{stats['std_dev']:.4f}",
         "Centerline", f"{limits['centerline']:.4f}"],
        ["Range", f"{stats['range']:.4f}",
         "LCL (3σ)", f"{limits['lcl']:.4f}"],
        ["Sample Count", str(stats['count']), "", ""],
    ]

    table = Table(data, colWidths=[4.5 * cm, 3.5 * cm, 4.5 * cm, 3.5 * cm])
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Data rows
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _capability_table(cp: float, cpk: float,
                       usl: float, lsl: float, interpretation: str) -> Table:
    """Build the process capability table."""
    # Determine status color
    if cpk >= 1.33:
        status_color = COLOR_SUCCESS
        status_text = "CAPABLE"
    elif cpk >= 1.0:
        status_color = COLOR_WARNING
        status_text = "MARGINAL"
    else:
        status_color = COLOR_DANGER
        status_text = "NOT CAPABLE"

    data = [
        ["Index", "Value", "Spec Limits", "Value", "Status", ""],
        ["Cp", f"{cp:.4f}", "USL", f"{usl:.3f}", status_text, ""],
        ["Cpk", f"{cpk:.4f}", "LSL", f"{lsl:.3f}", "", ""],
    ]

    table = Table(data, colWidths=[2.5*cm, 3*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("BACKGROUND", (4, 1), (4, 1), status_color),
        ("TEXTCOLOR", (4, 1), (4, 1), colors.white),
        ("FONTNAME", (4, 1), (4, 1), "Helvetica-Bold"),
        ("ALIGN", (4, 1), (4, 1), "CENTER"),
        ("SPAN", (4, 1), (5, 2)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def generate_pdf_report(
    process_name: str,
    parameter_name: str,
    unit: str,
    measurements: List[float],
    stats: dict,
    limits: dict,
    cp: float,
    cpk: float,
    usl: float,
    lsl: float,
    interpretation: str,
    rule_results: dict,
    recommendations: List[dict],
) -> bytes:
    """
    Generate a complete PDF quality report.

    Args:
        process_name: Name of the manufacturing process (e.g. 'Tablet Compression').
        parameter_name: Measured parameter name (e.g. 'Tablet Weight').
        unit: Unit of measurement (e.g. 'mg').
        measurements: List of numeric measurement values.
        stats: Dict with keys: mean, std_dev, range, count.
        limits: Dict with keys: ucl, centerline, lcl.
        cp: Process capability index Cp.
        cpk: Process capability index Cpk.
        usl: Upper Specification Limit.
        lsl: Lower Specification Limit.
        interpretation: Plain-language Cpk interpretation string.
        rule_results: Output from rule_engine.run_all_rules().
        recommendations: Output from assistant.generate_recommendations().

    Returns:
        PDF file content as bytes (ready for download or file write).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story = []

    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------
    story.append(Paragraph("💊 PharmaSPC Intelligence", styles["title"]))
    story.append(Paragraph(
        "Statistical Process Control Quality Report", styles["subtitle"]
    ))
    story.append(HRFlowable(
        width="100%", thickness=2, color=COLOR_PRIMARY, spaceAfter=12
    ))

    # Report metadata table
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    meta_data = [
        ["Process", process_name, "Generated", generated_at],
        ["Parameter", f"{parameter_name} ({unit})", "Sample Count", str(len(measurements))],
        ["USL / LSL", f"{usl} / {lsl}", "Analysis Method", "Western Electric Rules"],
    ]
    meta_table = Table(meta_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_PRIMARY),
        ("TEXTCOLOR", (2, 0), (2, -1), COLOR_PRIMARY),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [COLOR_LIGHT, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # -----------------------------------------------------------------------
    # Statistical Summary
    # -----------------------------------------------------------------------
    story.extend(_section_header("1. Statistical Summary", styles))
    story.append(_stats_table(stats, limits))
    story.append(Spacer(1, 0.3 * cm))

    # -----------------------------------------------------------------------
    # Process Capability
    # -----------------------------------------------------------------------
    story.extend(_section_header("2. Process Capability", styles))
    story.append(_capability_table(cp, cpk, usl, lsl, interpretation))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Interpretation: {interpretation}", styles["body"]
    ))
    story.append(Spacer(1, 0.3 * cm))

    # -----------------------------------------------------------------------
    # SPC Rule Detection Results
    # -----------------------------------------------------------------------
    story.extend(_section_header("3. SPC Rule Detection Results", styles))

    any_detected = rule_results.get("any_detected", False)
    if not any_detected:
        story.append(Paragraph(
            "✅ No SPC rule violations detected. Process is in statistical control.",
            styles["body"]
        ))
    else:
        r1 = rule_results.get("rule1", {})
        r2 = rule_results.get("rule2", {})
        r3 = rule_results.get("rule3", {})

        rule_data = [["Rule", "Status", "Detail"]]

        # Rule 1
        if r1.get("detected"):
            detail = f"Samples: {r1['violations'][:5]}"
            rule_data.append(["Rule 1 — Control Limit Violation", "⚠ DETECTED", detail])
        else:
            rule_data.append(["Rule 1 — Control Limit Violation", "✓ OK", "No violations"])

        # Rule 2
        if r2.get("detected"):
            detail = (f"{r2['direction'].capitalize()} trend, "
                      f"samples {r2['start_index']}–{r2['end_index']}")
            rule_data.append(["Rule 2 — Trend Detection", "⚠ DETECTED", detail])
        else:
            rule_data.append(["Rule 2 — Trend Detection", "✓ OK", "No trend detected"])

        # Rule 3
        if r3.get("detected"):
            detail = (f"Shift {r3['direction']}, "
                      f"samples {r3['start_index']}–{r3['end_index']}")
            rule_data.append(["Rule 3 — Process Shift", "⚠ DETECTED", detail])
        else:
            rule_data.append(["Rule 3 — Process Shift", "✓ OK", "No shift detected"])

        rule_table = Table(rule_data, colWidths=[7*cm, 3.5*cm, 6.5*cm])
        rule_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(rule_table)

    story.append(Spacer(1, 0.3 * cm))

    # -----------------------------------------------------------------------
    # Investigation Recommendations
    # -----------------------------------------------------------------------
    story.extend(_section_header("4. Investigation Recommendations", styles))

    for rec in recommendations:
        severity = rec.get("severity", "info")
        if severity == "critical":
            prefix = "🔴"
        elif severity == "warning":
            prefix = "🟡"
        else:
            prefix = "🟢"

        story.append(Paragraph(
            f"{prefix} <b>{rec['title']}</b>", styles["body"]
        ))
        story.append(Paragraph(
            f"Finding: {rec['finding']}", styles["finding"]
        ))

        if rec.get("probable_causes"):
            story.append(Paragraph("Probable Causes:", styles["body"]))
            for cause in rec["probable_causes"]:
                story.append(Paragraph(f"• {cause}", styles["finding"]))

        if rec.get("investigation_steps"):
            story.append(Paragraph("Investigation Steps:", styles["body"]))
            for i, step in enumerate(rec["investigation_steps"], 1):
                story.append(Paragraph(f"{i}. {step}", styles["finding"]))

        story.append(Spacer(1, 0.3 * cm))

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------
    story.append(HRFlowable(
        width="100%", thickness=1, color=COLOR_BORDER, spaceBefore=12
    ))
    story.append(Paragraph(
        f"Generated by PharmaSPC Intelligence · {generated_at} · "
        f"For Quality Engineering use only.",
        styles["caption"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()