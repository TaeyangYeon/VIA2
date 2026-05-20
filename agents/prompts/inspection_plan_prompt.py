"""Prompt builder for InspectionPlanAgent — produces system/user prompt pair for JSON array output."""
from agents.models import AlgorithmCategory, SceneContext

SYSTEM_PROMPT = """\
You are an expert vision inspection planner for industrial computer vision systems.
Given an inspection purpose and scene context, design a complete inspection plan as a JSON array.

Output ONLY a valid JSON array of inspection items with this exact schema:
[
  {
    "item_id": <int, starting from 1>,
    "name": "<short descriptive name of the inspection step>",
    "category": "<one of: blob, color_filter, edge_detection, template_matching, geometric>",
    "depends_on": [<list of item_ids this step depends on, empty if none>],
    "safety_role": <true if this is a safety-critical or primary quality gate, false otherwise>,
    "success_criteria": {
      "metric": "<what to measure>",
      "threshold": <numeric threshold or 0 if qualitative>
    }
  }
]

Rules:
- Design the plan freely based on the inspection purpose — do NOT use fixed templates.
- Every step must have a clear purpose related to the inspection goal.
- Use depends_on to express prerequisite relationships between steps.
- For defect types like holes/perforations (타공), include additional misdetection-prevention items (e.g., inter-hole distance check, minimum hole size check).
- safety_role must be a boolean (true/false), not a string.
- success_criteria must be a JSON object with at least "metric" and "threshold" keys.
- Output a JSON array only — no markdown fences, no explanation.
"""


def build_inspection_plan_prompt(
    purpose: str,
    scene_context: SceneContext,
    algorithm_category: AlgorithmCategory,
    directive: str | None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for InspectionPlanAgent."""
    diag = scene_context.image_diagnosis
    parts = [
        f"Inspection purpose: {purpose}",
        f"Primary algorithm category: {algorithm_category.value}",
        "",
        "Scene context:",
        f"  surface_type: {diag.surface_type}",
        f"  contrast: {diag.contrast:.2f}",
        f"  edge_density: {diag.edge_density:.2f}",
        f"  noise_level: {diag.noise_level:.2f}",
        f"  blob_feasibility: {diag.blob_feasibility:.2f}",
        f"  blob_count_estimate: {diag.blob_count_estimate}",
        f"  color_discriminability: {diag.color_discriminability:.2f}",
        f"  structural_regularity: {diag.structural_regularity:.2f}",
        f"  edge_sharpness: {diag.edge_sharpness:.2f}",
        f"  illumination_type: {diag.illumination_type}",
        f"  optimal_color_space: {diag.optimal_color_space}",
    ]

    if scene_context.roi:
        roi = scene_context.roi
        parts.append(
            f"  ROI: x={roi.get('x')}, y={roi.get('y')}, "
            f"width={roi.get('width')}, height={roi.get('height')}"
        )

    if directive:
        parts.append("")
        parts.append(f"Additional directive: {directive}")

    user_prompt = "\n".join(parts)
    return SYSTEM_PROMPT, user_prompt
