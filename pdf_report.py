
import os
import re
import html

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

    file_path = "reports/analysis_report.pdf"

    document = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#17365D"),
        alignment=TA_CENTER,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#24527A"),
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "CustomNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        spaceAfter=5
    )

    story = []

    # Main title
    story.append(
        Paragraph("DATA ANALYST REPORT", title_style)
    )

    story.append(
        Paragraph(
            f"Rows: {report['rows']} | "
            f"Columns: {report['columns']}",
            normal_style
        )
    )

    story.append(Spacer(1, 15))

    # Data quality
    story.append(
        Paragraph("DATA QUALITY", heading_style)
    )

    quality = report["data_quality"]

    story.append(
        Paragraph(
            f"Missing values: {quality['missing_values']}<br/>"
            f"Duplicate rows: {quality['duplicate_rows']}",
            normal_style
        )
    )

    # Anomaly detection
    story.append(
        Paragraph("ANOMALY DETECTION", heading_style)
    )

    found_outliers = False

    for column, values in report["outliers"].items():
        if values:
            found_outliers = True

            story.append(
                Paragraph(
                    f"<b>{html.escape(str(column))}:</b> "
                    f"{html.escape(str(values))}",
                    normal_style
                )
            )

    if not found_outliers:
        story.append(
            Paragraph("No anomalies detected.", normal_style)
        )

    story.append(Spacer(1, 10))

    # AI analysis
    story.append(
        Paragraph("AI ANALYSIS", heading_style)
    )

    for line in ai_explanation.splitlines():
        line = line.strip()

        if not line:
            continue

        # Convert Markdown headings
        if line.startswith("## "):
            heading = html.escape(line[3:])

            story.append(
                Paragraph(heading, heading_style)
            )
            continue

        # Escape HTML characters
        line = html.escape(line)

        # Convert Markdown bold text
        line = re.sub(
            r"\*\*(.*?)\*\*",
            r"<b>\1</b>",
            line
        )

        # Convert Markdown bullet points
        if line.startswith("- "):
            line = "&#8226; " + line[2:]

        story.append(
            Paragraph(line, normal_style)
        )

    # Generate PDF
    document.build(story)

    return file_path
