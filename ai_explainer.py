
import json
import time

from google import genai
from google.genai import errors as genai_errors
from config import GEMINI_API_KEY


MODEL_NAME = "gemini-3.5-flash-lite"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2


def build_ai_summary(report: dict) -> dict:
    """
    Prepare a compact summary for Gemini.
    Avoid sending the entire dataset statistics.
    """

    statistics = {}

    for column, info in list(
        report.get("statistics", {}).items()
    )[:20]:

        if "mean" not in info:
            continue

        statistics[column] = {
            "mean": round(info["mean"], 2),
            "median": round(info["median"], 2),
            "min": round(info["min"], 2),
            "max": round(info["max"], 2),
            "missing": info["missing"],
        }

    # ANOMALIES

    anomalies = {}

    for column, info in report.get("outliers", {}).items():

        statistical = info.get("statistical", {})
        business = info.get("business_rules", {})

        if (
            statistical.get("count", 0) == 0
            and business.get("count", 0) == 0
        ):
            continue

        anomalies[column] = {
            "statistical_outliers": {
                "count": statistical.get("count", 0),
                "examples": [
                    item.get("value")
                    for item in statistical.get("sample", [])[:3]
                ],
            },
            "business_rule_violations": {
                "count": business.get("count", 0),
                "examples": [
                    item.get("value")
                    for item in business.get("sample", [])[:3]
                ],
            },
        }

    # CALCULATION ERRORS

    calculation_errors = {}

    for column, info in report.get(
        "calculation_errors", {}
    ).items():

        calculation_errors[column] = {
            "count": info.get("count", 0),
            "examples": [
                {
                    "row": item.get("row"),
                    "actual": item.get("actual"),
                    "expected": item.get("expected"),
                }
                for item in info.get("sample", [])[:3]
            ],
        }

    summary = {
        "dataset": {
            "rows": report.get("rows", 0),
            "columns": report.get("columns", 0),
        },
        "data_quality": report.get("data_quality", {}),
        "numeric_statistics": statistics,
        "anomalies": anomalies,
        "calculation_errors": calculation_errors,
        "available_insights": report.get("insights", []),
    }

    return summary


def explain_analysis(report: dict) -> str:

    if not GEMINI_API_KEY or not GEMINI_API_KEY.strip():
        raise ValueError(
            "GEMINI_API_KEY is missing. AI analysis is disabled."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    compact_report = build_ai_summary(report)

    report_json = json.dumps(
        compact_report,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    prompt = f"""
You are a professional business data analyst.

Analyze the following summarized CSV analysis results:

{report_json}

Write a concise professional report in English.

Use exactly these four sections:

## 1. Main Findings
Give the 2 most important findings.

## 2. Important Trends
Explain trends only when the supplied data supports them.
If no reliable time-based trends are available, clearly say so.
Do not compare the first and last CSV rows as a trend.

## 3. Potential Problems
Mention important data quality issues, business-rule violations,
and calculation errors.

Explain calculation errors using the actual and expected values
when useful.

Distinguish:
- Statistical outliers: unusual values, not necessarily errors.
- Business-rule violations: values that break defined rules.
- Calculation errors: values that do not match expected formulas.

Do not count the same underlying problem as independent errors
without explaining the overlap.

## 4. Business Recommendations
Give 2 practical recommendations based only on the available data.

STRICT RULES:
- Maximum 200 words.
- Use 1-2 short bullet points per section.
- Avoid unnecessary introductions and conclusions.
- Do not repeat every statistic from the main report.
- Do not invent facts, causes, or explanations.
- Do not claim causation from correlation.
- Do not treat missing values as errors without considering context.
- Clearly mention limitations when necessary.
- Do not assume every statistical outlier is invalid.
- Do not assume business thresholds are universal standards.
- Use standard Markdown.
- Use ## for section headings.
- Use **text** for bold emphasis.
- Use - for bullet points.
- Never escape Markdown symbols with backslashes.
- Do not use HTML tags.
- Do not include greetings or conversational filler.
"""

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            if not response.text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            return response.text.strip()

        except genai_errors.ServerError as error:
            last_error = error

            if attempt == MAX_RETRIES:
                break

            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))

            time.sleep(delay)

    raise last_error
