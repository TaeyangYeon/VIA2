"""EvaluationAgent — rule-based failure reason classifier for test results. No LLM."""
import time
from typing import Optional

from agents.base_agent import BaseAgent
from agents.models import (
    AgentResult,
    FailureReason,
    InspectionItem,
    InspectionPlan,
    ProcessingPipeline,
)

# Block IDs that indicate edge-based processing capability
_EDGE_BLOCK_IDS: frozenset[str] = frozenset({"canny", "sobel", "laplacian", "scharr"})

# Block IDs that indicate threshold/morphology (blob/geometric-capable)
_BLOB_BLOCK_IDS: frozenset[str] = frozenset({
    "otsu", "adaptive_mean", "adaptive_gauss", "dynamic_threshold",
    "erosion", "dilation", "opening", "closing",
    "tophat", "blackhat", "morph_gradient",
})

# Block IDs that indicate color-space differentiation (non-grayscale)
_COLOR_BLOCK_IDS: frozenset[str] = frozenset({"hsv_s", "hsv_v", "lab_l", "ycrcb_cr"})

# min_accuracy threshold above which the spec is considered unreachable
_SPEC_ISSUE_MIN_ACC = 0.95

# accuracy below this means the pipeline fundamentally doesn't fit
_BAD_FIT_ACCURACY = 0.5


def _pipeline_block_ids(pipeline: Optional[ProcessingPipeline]) -> frozenset[str]:
    if pipeline is None:
        return frozenset()
    return frozenset(b.block_id for b in pipeline.blocks)


def _is_algorithm_mismatch(category: str, block_ids: frozenset[str]) -> bool:
    """True if pipeline block types fundamentally conflict with the item category."""
    if not block_ids:
        return False
    cat = category.upper()
    if cat == "EDGE_DETECTION":
        return not (_EDGE_BLOCK_IDS & block_ids)
    if cat == "COLOR_FILTER":
        return not (_COLOR_BLOCK_IDS & block_ids)
    if cat == "BLOB":
        # Mismatch if pipeline has ONLY edge blocks with no threshold/morphology
        has_blob = bool(_BLOB_BLOCK_IDS & block_ids)
        has_only_edge = bool(_EDGE_BLOCK_IDS & block_ids) and not has_blob
        return has_only_edge
    return False


def _classify_failed(
    item_result: dict,
    plan_item: Optional[InspectionItem],
    block_ids: frozenset[str],
) -> FailureReason:
    """Classify a non-skipped failed item into a FailureReason."""
    accuracy = float(item_result.get("accuracy", 0.0))
    category = item_result.get("category", "")

    # Spec issue takes highest priority among active failures
    if plan_item is not None:
        min_acc = float(plan_item.success_criteria.get("min_accuracy", 0.8))
        if min_acc >= _SPEC_ISSUE_MIN_ACC:
            return FailureReason.SPEC_ISSUE

    # Algorithm category mismatch
    if _is_algorithm_mismatch(category, block_ids):
        return FailureReason.ALGORITHM_WRONG_CATEGORY

    # Accuracy-based classification
    if accuracy < _BAD_FIT_ACCURACY:
        return FailureReason.PIPELINE_BAD_FIT

    return FailureReason.PIPELINE_BAD_PARAMS


def _classify_skipped(plan_item: Optional[InspectionItem]) -> FailureReason:
    if plan_item is not None and plan_item.depends_on:
        return FailureReason.INSPECTION_PLAN_ISSUE
    return FailureReason.RUNTIME_ERROR


class EvaluationAgent(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__("evaluation_agent", directive)

    async def run(
        self,
        test_result: AgentResult,
        mode: str = "inspection",
        pipeline: Optional[ProcessingPipeline] = None,
        inspection_plan: Optional[InspectionPlan] = None,
        success_criteria: Optional[dict] = None,
        directive: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.monotonic()

        if test_result.status != "success":
            return AgentResult(
                status="error",
                data={},
                error_message=test_result.error_message or "upstream test agent failed",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        if mode == "align":
            return self._evaluate_align(test_result, t0)

        return self._evaluate_inspection(test_result, pipeline, inspection_plan, t0)

    # ── inspection mode ────────────────────────────────────────────────────────

    def _evaluate_inspection(
        self,
        test_result: AgentResult,
        pipeline: Optional[ProcessingPipeline],
        inspection_plan: Optional[InspectionPlan],
        t0: float,
    ) -> AgentResult:
        item_results: list[dict] = test_result.data.get("item_results", [])
        block_ids = _pipeline_block_ids(pipeline)

        plan_map: dict[int, InspectionItem] = {}
        if inspection_plan is not None:
            plan_map = {item.item_id: item for item in inspection_plan.items}

        item_evaluations: list[dict] = []
        failure_summary: dict[str, int] = {}

        for ir in item_results:
            item_id = ir.get("item_id")
            passed = bool(ir.get("passed", False))
            skipped = bool(ir.get("skipped", False))
            plan_item = plan_map.get(item_id)

            if passed and not skipped:
                failure_reason = None
                details = "passed"
            elif skipped:
                reason = _classify_skipped(plan_item)
                failure_reason = reason.value
                details = f"skipped: {reason.value}"
                failure_summary[reason.value] = failure_summary.get(reason.value, 0) + 1
            else:
                reason = _classify_failed(ir, plan_item, block_ids)
                failure_reason = reason.value
                acc = ir.get("accuracy", 0.0)
                details = f"failed: {reason.value} (accuracy={float(acc):.3f})"
                failure_summary[reason.value] = failure_summary.get(reason.value, 0) + 1

            item_evaluations.append({
                "item_id": item_id,
                "passed": passed and not skipped,
                "failure_reason": failure_reason,
                "details": details,
            })

        total = len(item_evaluations)
        passed_cnt = sum(1 for e in item_evaluations if e["passed"])
        overall_passed = (passed_cnt == total) and (total > 0)

        return AgentResult(
            status="success",
            data={
                "item_evaluations": item_evaluations,
                "overall_passed": overall_passed,
                "total_items": total,
                "passed_items": passed_cnt,
                "failed_items": total - passed_cnt,
                "failure_summary": failure_summary,
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )

    # ── align mode ─────────────────────────────────────────────────────────────

    def _evaluate_align(
        self,
        test_result: AgentResult,
        t0: float,
    ) -> AgentResult:
        data = test_result.data
        overall_passed = bool(data.get("overall_passed", False))
        success_rate = float(data.get("overall_success_rate", 0.0))
        per_image: list[dict] = data.get("per_image_results", [])

        overall_failure_reason: Optional[str] = None
        if not overall_passed:
            if success_rate < _BAD_FIT_ACCURACY:
                overall_failure_reason = FailureReason.PIPELINE_BAD_FIT.value
            else:
                overall_failure_reason = FailureReason.PIPELINE_BAD_PARAMS.value

        item_evaluations: list[dict] = []
        for img_r in per_image:
            img_passed = bool(img_r.get("success", False))
            item_evaluations.append({
                "item_id": img_r.get("image_index"),
                "passed": img_passed,
                "failure_reason": overall_failure_reason if not img_passed else None,
                "details": (
                    f"error_px={float(img_r.get('error_px', 0.0)):.3f}, "
                    f"method={img_r.get('method_used', 'unknown')}"
                ),
            })

        total = len(item_evaluations)
        passed_cnt = sum(1 for e in item_evaluations if e["passed"])
        failed_cnt = total - passed_cnt

        failure_summary: dict[str, int] = {}
        if overall_failure_reason and failed_cnt > 0:
            failure_summary[overall_failure_reason] = failed_cnt

        return AgentResult(
            status="success",
            data={
                "item_evaluations": item_evaluations,
                "overall_passed": overall_passed,
                "failure_reason": overall_failure_reason,
                "total_items": total,
                "passed_items": passed_cnt,
                "failed_items": failed_cnt,
                "failure_summary": failure_summary,
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )
