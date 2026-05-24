"""Prompt builder for DecisionAgent — NG defect pattern analysis for InternVL."""


def build_decision_prompt(
    mode: str,
    dinov2_cv: float | None,
    vision_judge_avg: float | None,
    evaluation_summary: dict | None,
    feedback_summary: dict | None,
    success_criteria: dict | None,
    directive: str = "",
) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for InternVL NG image pattern analysis.

    The system prompt sets InternVL's role as a visual defect pattern analyst.
    The user prompt includes statistical context and asks for structured JSON output.
    """
    system = """\
You are a machine vision expert specializing in industrial defect pattern analysis.
Analyze NG (defective) product images and classify the defect pattern type.

Evaluate the visual diversity of defects across the provided images:
- "consistent": All images show similar, repeatable defect patterns with low visual variation
- "diverse": Images show significantly different defect patterns with high visual variation
- "mixed": Images show both consistent and diverse elements

Output ONLY valid JSON with this exact schema — no markdown fences, no explanation:
{
  "pattern_type": "consistent" | "diverse" | "mixed",
  "complexity_score": <float 0.0-1.0>,
  "reasoning": "<string>"
}"""

    context_lines: list[str] = [f"Inspection mode: {mode}"]

    if dinov2_cv is not None:
        context_lines.append(f"DINOv2 feature variability (CV): {dinov2_cv:.4f}")
        if dinov2_cv < 0.2:
            context_lines.append(
                "Statistical analysis suggests CONSISTENT defect patterns (CV < 0.2 threshold)"
            )
        else:
            context_lines.append(
                "Statistical analysis suggests DIVERSE defect patterns (CV >= 0.2 threshold)"
            )

    if vision_judge_avg is not None:
        context_lines.append(f"Vision Judge average score: {vision_judge_avg:.3f}")

    if evaluation_summary:
        failed = evaluation_summary.get("failed_items", 0)
        total = evaluation_summary.get("total_items", 0)
        if total > 0:
            context_lines.append(f"Evaluation result: {failed}/{total} items failed")

    if success_criteria:
        context_lines.append(f"Success criteria: {success_criteria}")

    if feedback_summary:
        tried = feedback_summary.get("tried_strategies", [])
        if tried:
            context_lines.append(f"Previously tried strategies: {', '.join(tried)}")

    user = "Analyze these NG (defective) images and classify the defect pattern type.\n\n"
    user += "\n".join(context_lines)
    user += "\n\nProvide your visual pattern assessment in the required JSON format."

    if directive:
        user += f"\n\nAdditional guidance: {directive}"

    return system, user
