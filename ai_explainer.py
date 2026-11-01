from google import genai
from config import GEMINI_API_KEY


MODEL_NAME = "gemini-3.5-flash-lite"

client = genai.Client(api_key=GEMINI_API_KEY)


def explain_analysis(report: dict) -> str:

    prompt = f"""
You are a professional business data analyst.

Analyze these CSV analysis results:

{report}

Write a concise professional report in English.

Use exactly these four sections:

## 1. Main Findings
Give the 2 most important findings.

## 2. Important Trends
Explain the most important trends in the data.

## 3. Potential Problems
Mention important limitations or data quality issues.

## 4. Business Recommendations
Give 2 practical recommendations based only on the data.

STRICT RULES:
- Maximum 200 words.
- Use 1-2 short bullet points per section.
- Avoid unnecessary introductions and conclusions.
- Do not repeat every statistic from the main report.
- Do not invent facts, causes, or explanations.
- Do not claim causation from correlation.
- Clearly mention limitations when necessary.
- Use standard Markdown.
- Use ## for section headings.
- Use **text** for bold emphasis.
- Use - for bullet points.
- Never escape Markdown symbols with backslashes.
- Do not use HTML tags.
- Do not include greetings or conversational filler.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text.strip()