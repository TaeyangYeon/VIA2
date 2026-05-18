"""Prompt builder for SpecAgent — produces system/user prompt pair for JSON output."""

SYSTEM_PROMPT = """\
You are an expert vision system requirements analyst.
Analyze the user's vision inspection or alignment request and extract structured specifications.

Output ONLY valid JSON with this exact schema:
{
  "mode": "inspection" or "align",
  "goal": "<concise description of what to inspect or align>",
  "success_criteria": {
    "accuracy": <float 0-1 or null>,
    "fp_rate": <float 0-1 or null>,
    "fn_rate": <float 0-1 or null>,
    "coord_error": <float in mm/pixels or null>
  },
  "raw_input": "<original user text verbatim>"
}

Rules:
- mode is "inspection" if the user wants to detect defects, anomalies, or verify quality.
- mode is "align" if the user wants to position, center, or register objects.
- If the user specifies numeric accuracy/fp_rate/fn_rate/coord_error, extract them; otherwise use null.
- goal must be in English regardless of input language.
- raw_input must be the verbatim original user text.
- Output JSON only — no markdown fences, no explanation.
"""


def build_spec_prompt(
    user_text: str,
    roi: dict | None = None,
    directive: str | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for SpecAgent."""
    parts = [f"User request: {user_text}"]

    if roi is not None:
        parts.append(
            f"ROI coordinates: x={roi.get('x')}, y={roi.get('y')}, "
            f"width={roi.get('width')}, height={roi.get('height')}"
        )

    if directive:
        parts.append(f"Additional directive: {directive}")

    user_prompt = "\n".join(parts)
    return SYSTEM_PROMPT, user_prompt
