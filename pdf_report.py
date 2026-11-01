
import os
import re
import html
import uuid

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)


def create_pdf_report(report: dict, ai_explanation: str) -> str:

    os.makedirs("reports", exist_ok=True)

    unique_id = uuid.uuid4().hex
    file_path = f"reports/analysis_report_{unique_id}.pdf"

    document = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#17365D"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#24527A"),
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        spaceAfter=5,
    )

    story = []

    # MAIN TITLE

    story.append(
        Paragraph("DATA ANALYST REPORT", title_style)
    )

    story.append(
        Paragraph(
            f"Rows: {report['rows']} | "
            f"Columns: {report['columns']}",
            normal_style,
        )
    )

    story.append(Spacer(1, 15))

    # DATA QUALITY

    story.append(
        Paragraph("DATA QUALITY", heading_style)
    )

    quality = report["data_quality"]

    story.append(
        Paragraph(
            f"Missing values: {quality['missing_values']}<br/>"
            f"Duplicate rows: {quality['duplicate_rows']}",
            normal_style,
        )
    )

    # ANOMALY DETECTION

    story.append(
        Paragraph("ANOMALY DETECTION", heading_style)
    )

    outliers = report.get("outliers", {})

    statistical_total = 0
    business_total = 0

    for info in outliers.values():
        statistical_total += info.get(
            "statistical", {}
        ).get("count", 0)

        business_total += info.get(
            "business_rules", {}
        ).get("count", 0)

    story.append(
        Paragraph(
            f"Statistical outliers: {statistical_total}<br/>"
            f"Business rule violations: {business_total}<br/>"
            f"Total flagged values: "
            f"{statistical_total + business_total}",
            normal_style,
        )
    )

    # STATISTICAL OUTLIERS

    story.append(
        Paragraph("STATISTICAL OUTLIERS", heading_style)
    )

    found_statistical = False

    for column, info in outliers.items():

        statistical = info.get("statistical", {})
        count = statistical.get("count", 0)

        if count <= 0:
            continue

        found_statistical = True
        sample = statistical.get("sample", [])

        sample_text = ", ".join(
            f"row {item['row']}: {item['value']}"
            for item in sample
        )

        remaining = count - len(sample)

        line = (
            f"<b>{html.escape(str(column))}:</b> "
            f"{count} unusual value(s)."
        )

        if sample_text:
            line += (
                f" Examples: {html.escape(sample_text)}"
            )

        if remaining > 0:
            line += f" And {remaining} more."

        story.append(
            Paragraph(line, normal_style)
        )

    if not found_statistical:
        story.append(
            Paragraph(
                "No statistical outliers detected.",
                normal_style,
            )
        )

    # BUSINESS RULE VIOLATIONS

    story.append(
        Paragraph(
            "BUSINESS RULE VIOLATIONS",
            heading_style,
        )
    )

    found_business = False

    for column, info in outliers.items():

        business = info.get("business_rules", {})
        count = business.get("count", 0)

        if count <= 0:
            continue

        found_business = True
        sample = business.get("sample", [])

        sample_text = ", ".join(
            f"row {item['row']}: {item['value']}"
            for item in sample
        )

        remaining = count - len(sample)

        line = (
            f"<b>{html.escape(str(column))}:</b> "
            f"{count} violation(s)."
        )

        if sample_text:
            line += (
                f" Examples: {html.escape(sample_text)}"
            )

        if remaining > 0:
            line += f" And {remaining} more."

        story.append(
            Paragraph(line, normal_style)
        )

    if not found_business:
        story.append(
            Paragraph(
                "No business rule violations detected.",
                normal_style,
            )
        )

    # CALCULATION ERRORS

    story.append(
        Paragraph(
            "CALCULATION ERRORS",
            heading_style,
        )
    )

    calculation_errors = report.get(
        "calculation_errors", {}
    )

    total_calculation_errors = sum(
        info.get("count", 0)
        for info in calculation_errors.values()
    )

    story.append(
        Paragraph(
            f"Total calculation errors: "
            f"{total_calculation_errors}",
            normal_style,
        )
    )

    if calculation_errors:

        for column, info in calculation_errors.items():

            count = info.get("count", 0)

            story.append(
                Paragraph(
                    f"<b>{html.escape(str(column))}:</b> "
                    f"{count} error(s)",
                    normal_style,
                )
            )

            for item in info.get("sample", []):

                row = item["row"]
                actual = item["actual"]
                expected = item["expected"]

                story.append(
                    Paragraph(
                        f"Row {row}: "
                        f"Actual = {actual:.2f}; "
                        f"Expected = {expected:.2f}",
                        normal_style,
                    )
                )

    else:
        story.append(
            Paragraph(
                "No calculation errors detected.",
                normal_style,
            )
        )

    story.append(Spacer(1, 10))

    # AI ANALYSIS

    story.append(
        Paragraph("AI ANALYSIS", heading_style)
    )

    for line in ai_explanation.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            heading_text = line.lstrip("#").strip()

            story.append(
                Paragraph(
                    html.escape(heading_text),
                    heading_style,
                )
            )
            continue

        # Escape HTML before applying Markdown formatting.
        line = html.escape(line)

        # Markdown bold
        line = re.sub(
            r"\*\*(.+?)\*\*",
            r"<b>\1</b>",
            line,
        )

        # Markdown italic
        line = re.sub(
            r"(?<!\*)\*([^*]+)\*(?!\*)",
            r"<i>\1</i>",
            line,
        )

        # Markdown bullet points
        if line.startswith("- ") or line.startswith("* "):
            line = "&#8226; " + line[2:]

        story.append(
            Paragraph(line, normal_style)
        )

    # GENERATE PDF

    document.build(story)

    return file_path
