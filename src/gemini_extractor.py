
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("LLM_API_KEY"))

client = genai.GenerativeModel("gemini-pro")

def extract_with_gemini(pages, config):
    """
    Uses Gemini 1.5 Flash to extract ESG metrics.

    Returns:
      {
        metric_name: {
          "value": number | bool | str | null,
          "insight": str
        }
      }
    """
    text = "\n".join(pages)

    prompt = f"""
You are an ESG analyst.

Extract the following ESG metrics from the company report.

For each metric, return:
- "value": numeric, %, boolean, or null if not found
- "insight": one short sentence explaining where the value came from
  or why it is missing.

If a metric is not disclosed, use:
value = null
insight = "Not disclosed in this report"

Metrics to extract:
{json.dumps(config, indent=2)}

Text to analyze:
{text[:15000]}

Return ONLY valid JSON in the format:
{{
  "metric_name": {{
    "value": <number | boolean | string | null>,
    "insight": "<short explanation>"
  }}
}}
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    raw_text = response.text.strip()

    try:
        return json.loads(raw_text)
    except Exception:
        return {
            "error": "Invalid JSON returned by Gemini",
            "raw_output": raw_text
        }
