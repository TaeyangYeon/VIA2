"""AlgorithmSelector — deterministic rule-based algorithm category selector."""
import time
from typing import Optional

from agents.base_agent import BaseAgent
from agents.models import AgentResult, AlgorithmCategory, ImageDiagnosis, SceneContext


class AlgorithmSelector(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__(name="algorithm_selector", directive=directive)

    async def run(self, scene_context: Optional[SceneContext] = None, **kwargs) -> AgentResult:
        start = time.monotonic()

        if scene_context is None:
            return AgentResult(
                status="error",
                data={},
                error_message="SceneContext is required",
                execution_time_ms=0.0,
            )

        diagnosis: Optional[ImageDiagnosis] = scene_context.image_diagnosis
        if diagnosis is None:
            return AgentResult(
                status="error",
                data={},
                error_message="ImageDiagnosis is required in SceneContext",
                execution_time_ms=0.0,
            )

        if self.directive:
            self._log("info", f"Directive received (informational only): {self.directive}")

        category, reason, decision_path = self._classify(diagnosis)

        scores = {
            "contrast": diagnosis.contrast,
            "blob_feasibility": diagnosis.blob_feasibility,
            "color_discriminability": diagnosis.color_discriminability,
            "edge_density": diagnosis.edge_density,
            "structural_regularity": diagnosis.structural_regularity,
            "pattern_repetition": diagnosis.pattern_repetition,
        }

        elapsed = (time.monotonic() - start) * 1000
        return AgentResult(
            status="success",
            data={
                "category": category.value,
                "reason": reason,
                "scores": scores,
                "decision_path": decision_path,
            },
            execution_time_ms=elapsed,
        )

    def _classify(
        self, d: ImageDiagnosis
    ) -> tuple[AlgorithmCategory, str, list[str]]:
        path: list[str] = []

        check = f"contrast({d.contrast:.3f}) > 0.4 AND blob_feasibility({d.blob_feasibility:.3f}) > 0.6"
        if d.contrast > 0.4 and d.blob_feasibility > 0.6:
            path.append(f"[MATCH] {check}")
            return (
                AlgorithmCategory.BLOB,
                f"High contrast ({d.contrast:.3f}) and blob feasibility ({d.blob_feasibility:.3f}) indicate distinct blobs.",
                path,
            )
        path.append(f"[SKIP]  {check}")

        check = f"color_discriminability({d.color_discriminability:.3f}) > 0.5"
        if d.color_discriminability > 0.5:
            path.append(f"[MATCH] {check}")
            return (
                AlgorithmCategory.COLOR_FILTER,
                f"High color discriminability ({d.color_discriminability:.3f}) enables color-based segmentation.",
                path,
            )
        path.append(f"[SKIP]  {check}")

        check = f"edge_density({d.edge_density:.3f}) > 0.3 AND structural_regularity({d.structural_regularity:.3f}) > 0.5"
        if d.edge_density > 0.3 and d.structural_regularity > 0.5:
            path.append(f"[MATCH] {check}")
            return (
                AlgorithmCategory.EDGE_DETECTION,
                f"Dense edges ({d.edge_density:.3f}) and structural regularity ({d.structural_regularity:.3f}) favor edge-based detection.",
                path,
            )
        path.append(f"[SKIP]  {check}")

        check = f"pattern_repetition({d.pattern_repetition:.3f}) > 0.7"
        if d.pattern_repetition > 0.7:
            path.append(f"[MATCH] {check}")
            return (
                AlgorithmCategory.TEMPLATE_MATCHING,
                f"High pattern repetition ({d.pattern_repetition:.3f}) suggests template-based matching.",
                path,
            )
        path.append(f"[SKIP]  {check}")

        path.append("[DEFAULT] No condition matched — falling back to BLOB.")
        return (
            AlgorithmCategory.BLOB,
            "No specific condition matched; defaulting to BLOB as the general-purpose fallback.",
            path,
        )
