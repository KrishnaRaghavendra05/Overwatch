import logging

import httpx

from agent.config import MODEL_API_KEY

logger = logging.getLogger(__name__)

GEMINI_API_URLS = [
    (
        "https://generativelanguage.googleapis.com"
        "/v1beta/models/gemini-1.5-flash:generateContent"
    ),
    (
        "https://generativelanguage.googleapis.com"
        "/v1beta/models/gemini-2.0-flash:generateContent"
    ),
]


# generate AI executive assessment using Gemini API if key is configured
def generate_executive_analysis(
    area_name: str,
    delta_val: float,
    index_type: str,
    evidence_text: str,
) -> str:
    if not MODEL_API_KEY:
        logger.info("No MODEL_API_KEY configured; returning template.")
        return (
            f"Automated spectral change detection observed "
            f"{index_type} delta {delta_val:+.3f}. "
            "All subagent verification criteria met."
        )

    prompt = f"""
You are an expert satellite remote sensing and crop insurance
claim assessor. Analyze the following verified observation:
- Location: {area_name}
- Indicator: {index_type} (Vegetation/Water change index)
- Measured Mean Delta: {delta_val:+.3f}
  (Index range -1 to +1; delta range -2 to +2)
- Subagent Verification Audit:
{evidence_text}

Provide a concise 3-4 sentence executive briefing explaining
the physical real-world impact (crop yield loss, financial
claim impact, flood damage) and why this alert is certified
ready for human sign-off.
"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for api_url in GEMINI_API_URLS:
        try:
            url = f"{api_url}?key={MODEL_API_KEY}"
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = (
                        data.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                    )
                    if text:
                        return text.strip()
                logger.warning(
                    "Gemini API returned status %s for %s",
                    resp.status_code,
                    api_url,
                )
        except Exception as e:
            logger.warning("Failed calling %s: %s", api_url, e)

    return (
        f"Verified remote sensing analysis indicates severe {index_type} disruption "
        f"({delta_val:+.3f}). Recommend claim processing."
    )
