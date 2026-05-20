"""TestAgentInspection — executes inspection items against OK/NG images with per-item metrics.

Implements topological execution order, 5 inspection categories (BLOB, EDGE_DETECTION,
COLOR_FILTER, TEMPLATE_MATCHING, GEOMETRIC), and per-item accuracy/fp_rate/fn_rate metrics.
Pure OpenCV + NumPy — no LLM or network calls.
"""
import time
from collections import deque
from typing import Optional

import cv2
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, InspectionItem, InspectionPlan, ProcessingPipeline
from agents.parameter_searcher import _apply_block


def _ensure_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def _topological_sort(items: list[InspectionItem]) -> list[int]:
    """Kahn's algorithm — raises ValueError on circular dependency, ignores missing deps."""
    id_set = {item.item_id for item in items}
    in_degree: dict[int, int] = {item.item_id: 0 for item in items}
    adj: dict[int, list[int]] = {item.item_id: [] for item in items}

    for item in items:
        for dep_id in item.depends_on:
            if dep_id not in id_set:
                continue  # missing dependency — skip with implicit warning
            adj[dep_id].append(item.item_id)
            in_degree[item.item_id] += 1

    queue: deque[int] = deque(
        item_id for item_id, deg in in_degree.items() if deg == 0
    )
    order: list[int] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in sorted(adj[node]):  # sorted for determinism
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(items):
        raise ValueError("Circular dependency detected in inspection plan")

    return order


def _apply_pipeline(
    pipeline: ProcessingPipeline,
    image: np.ndarray,
    roi: Optional[dict],
) -> np.ndarray:
    """Apply ROI crop, then run all pipeline blocks in sequence."""
    work = image
    if roi is not None:
        x1 = int(roi.get("x1", 0))
        y1 = int(roi.get("y1", 0))
        x2 = int(roi.get("x2", image.shape[1]))
        y2 = int(roi.get("y2", image.shape[0]))
        work = image[y1:y2, x1:x2]
    current = work.copy()
    for block in pipeline.blocks:
        current = _apply_block(current, block.block_id, block.params)
    return current


def _count_blobs(img: np.ndarray) -> int:
    """Count blobs via thresholding + contour detection."""
    gray = _ensure_gray(img)
    if float(gray.std()) < 1.0:
        return 0  # uniform image — no blobs
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return len(contours)


def _calculate_metrics(
    ok_defect_flags: list[bool],
    ng_defect_flags: list[bool],
) -> tuple[float, float, float]:
    n_ok = len(ok_defect_flags)
    n_ng = len(ng_defect_flags)
    fp = sum(ok_defect_flags)
    fn = sum(not f for f in ng_defect_flags)
    tp = n_ng - fn
    tn = n_ok - fp
    accuracy = (tp + tn) / (n_ok + n_ng)
    fp_rate = fp / n_ok
    fn_rate = fn / n_ng
    return accuracy, fp_rate, fn_rate


def _item_passed(
    item: InspectionItem,
    accuracy: float,
    fp_rate: float,
    fn_rate: float,
    directive: str,
) -> bool:
    d_lower = directive.lower()
    adjust = 0.1 if "strict" in d_lower else (-0.1 if "lenient" in d_lower else 0.0)

    criteria = item.success_criteria
    min_acc = float(criteria.get("min_accuracy", 0.8)) + adjust
    max_fp = float(criteria.get("max_fp_rate", 1.0)) - adjust
    max_fn = float(criteria.get("max_fn_rate", 1.0)) - adjust

    if accuracy < min_acc:
        return False
    if fp_rate > max(0.0, max_fp):
        return False
    if fn_rate > max(0.0, max_fn):
        return False
    return True


class TestAgentInspection(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__("test_agent_inspection", directive)

    async def run(
        self,
        inspection_plan: InspectionPlan,
        pipeline: ProcessingPipeline,
        ok_images: list,
        ng_images: list,
        roi: Optional[dict] = None,
        directive: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.monotonic()
        effective = directive if directive is not None else self.directive

        if not inspection_plan.items:
            return AgentResult(
                status="error",
                data={},
                error_message="Inspection plan has no items",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )
        if not ok_images:
            return AgentResult(
                status="error",
                data={},
                error_message="No OK images provided",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )
        if not ng_images:
            return AgentResult(
                status="error",
                data={},
                error_message="No NG images provided",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        try:
            exec_order = _topological_sort(inspection_plan.items)
        except ValueError as exc:
            return AgentResult(
                status="error",
                data={},
                error_message=str(exc),
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        ok_proc = [_apply_pipeline(pipeline, img, roi) for img in ok_images]
        ng_proc = [_apply_pipeline(pipeline, img, roi) for img in ng_images]

        id_to_item = {item.item_id: item for item in inspection_plan.items}
        results: dict[int, dict] = {}
        failed_ids: set[int] = set()
        skipped_ids: set[int] = set()

        for item_id in exec_order:
            item = id_to_item[item_id]
            dep_failed = any(
                dep in failed_ids or dep in skipped_ids
                for dep in item.depends_on
                if dep in id_to_item
            )

            if dep_failed:
                skipped_ids.add(item_id)
                results[item_id] = {
                    "item_id": item_id,
                    "name": item.name,
                    "category": item.category,
                    "accuracy": 0.0,
                    "fp_rate": 0.0,
                    "fn_rate": 0.0,
                    "passed": False,
                    "skipped": True,
                    "details": {},
                }
                continue

            ok_flags, ng_flags, details = self._execute_item(
                item, ok_proc, ng_proc, effective
            )
            accuracy, fp_rate, fn_rate = _calculate_metrics(ok_flags, ng_flags)
            passed = _item_passed(item, accuracy, fp_rate, fn_rate, effective)
            if not passed:
                failed_ids.add(item_id)

            results[item_id] = {
                "item_id": item_id,
                "name": item.name,
                "category": item.category,
                "accuracy": accuracy,
                "fp_rate": fp_rate,
                "fn_rate": fn_rate,
                "passed": passed,
                "skipped": False,
                "details": details,
            }

        results_list = [results[iid] for iid in exec_order]
        non_skipped = [r for r in results_list if not r["skipped"]]
        overall_accuracy = (
            sum(r["accuracy"] for r in non_skipped) / len(non_skipped)
            if non_skipped else 0.0
        )
        overall_passed = all(r["passed"] for r in non_skipped) if non_skipped else False
        passed_cnt = sum(1 for r in results_list if r["passed"] and not r["skipped"])
        skipped_cnt = sum(1 for r in results_list if r["skipped"])
        failed_cnt = sum(1 for r in results_list if not r["passed"] and not r["skipped"])

        return AgentResult(
            status="success",
            data={
                "item_results": results_list,
                "overall_accuracy": overall_accuracy,
                "overall_passed": overall_passed,
                "execution_order": exec_order,
                "total_items": len(results_list),
                "passed_items": passed_cnt,
                "skipped_items": skipped_cnt,
                "failed_items": failed_cnt,
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )

    # ── Category dispatching ───────────────────────────────────────────────────

    def _execute_item(
        self,
        item: InspectionItem,
        ok_proc: list[np.ndarray],
        ng_proc: list[np.ndarray],
        directive: str,
    ) -> tuple[list[bool], list[bool], dict]:
        cat = item.category.upper()
        if cat in ("BLOB", "COUNT"):
            return self._run_blob(item, ok_proc, ng_proc)
        if cat == "COLOR_FILTER":
            return self._run_color_filter(item, ok_proc, ng_proc)
        if cat == "EDGE_DETECTION":
            return self._run_edge_detection(item, ok_proc, ng_proc)
        if cat == "TEMPLATE_MATCHING":
            return self._run_template_matching(item, ok_proc, ng_proc)
        if cat == "GEOMETRIC":
            return self._run_geometric(item, ok_proc, ng_proc)
        # Unknown category — fall back to blob
        return self._run_blob(item, ok_proc, ng_proc)

    # ── BLOB / COUNT ───────────────────────────────────────────────────────────

    def _run_blob(
        self,
        item: InspectionItem,
        ok_proc: list[np.ndarray],
        ng_proc: list[np.ndarray],
    ) -> tuple[list[bool], list[bool], dict]:
        ok_counts = [_count_blobs(img) for img in ok_proc]
        ng_counts = [_count_blobs(img) for img in ng_proc]

        if "expected_count" in item.success_criteria:
            expected = float(item.success_criteria["expected_count"])
            thr = 0.5
        else:
            expected = float(np.median(ok_counts)) if ok_counts else 0.0
            thr = max(1.0, abs(expected) * 0.5 + 1.0)

        ok_flags = [abs(c - expected) > thr for c in ok_counts]
        ng_flags = [abs(c - expected) > thr for c in ng_counts]

        details = {
            "blob_counts": ok_counts + ng_counts,
            "ok_blob_counts": ok_counts,
            "ng_blob_counts": ng_counts,
            "baseline": expected,
            "threshold": thr,
        }
        return ok_flags, ng_flags, details

    # ── COLOR_FILTER ───────────────────────────────────────────────────────────

    def _run_color_filter(
        self,
        item: InspectionItem,
        ok_proc: list[np.ndarray],
        ng_proc: list[np.ndarray],
    ) -> tuple[list[bool], list[bool], dict]:
        def channel_score(img: np.ndarray) -> float:
            if img.ndim == 3:
                b, g, r = cv2.split(img)
                return float(np.mean(r)) - float(np.mean(b))
            return 0.0

        ok_scores = [channel_score(img) for img in ok_proc]
        ng_scores = [channel_score(img) for img in ng_proc]
        baseline = float(np.mean(ok_scores)) if ok_scores else 0.0
        std = float(np.std(ok_scores)) if len(ok_scores) > 1 else 0.0
        thr = max(std * 2.0, 20.0)

        ok_flags = [abs(s - baseline) > thr for s in ok_scores]
        ng_flags = [abs(s - baseline) > thr for s in ng_scores]

        details = {
            "channel_scores": ok_scores + ng_scores,
            "ok_channel_scores": ok_scores,
            "ng_channel_scores": ng_scores,
            "baseline": baseline,
            "threshold": thr,
        }
        return ok_flags, ng_flags, details

    # ── EDGE_DETECTION ─────────────────────────────────────────────────────────

    def _run_edge_detection(
        self,
        item: InspectionItem,
        ok_proc: list[np.ndarray],
        ng_proc: list[np.ndarray],
    ) -> tuple[list[bool], list[bool], dict]:
        def edge_density(img: np.ndarray) -> float:
            gray = _ensure_gray(img)
            edges = cv2.Canny(gray, 50, 150)
            return float(np.mean(edges)) / 255.0

        ok_scores = [edge_density(img) for img in ok_proc]
        ng_scores = [edge_density(img) for img in ng_proc]
        baseline = float(np.mean(ok_scores)) if ok_scores else 0.0
        std = float(np.std(ok_scores)) if len(ok_scores) > 1 else 0.0
        thr = max(std * 2.0, 0.02)

        ok_flags = [abs(s - baseline) > thr for s in ok_scores]
        ng_flags = [abs(s - baseline) > thr for s in ng_scores]

        details = {
            "edge_scores": ok_scores + ng_scores,
            "ok_edge_scores": ok_scores,
            "ng_edge_scores": ng_scores,
            "baseline": baseline,
            "threshold": thr,
        }
        return ok_flags, ng_flags, details

    # ── TEMPLATE_MATCHING ──────────────────────────────────────────────────────

    def _run_template_matching(
        self,
        item: InspectionItem,
        ok_proc: list[np.ndarray],
        ng_proc: list[np.ndarray],
    ) -> tuple[list[bool], list[bool], dict]:
        if not ok_proc:
            return [], [], {"match_scores": [], "ok_match_scores": [], "ng_match_scores": []}

        ref = _ensure_gray(ok_proc[0])
        h, w = ref.shape[:2]
        th = max(10, h // 4)
        tw = max(10, w // 4)
        cy, cx = h // 2, w // 2
        template = ref[cy - th // 2: cy + th // 2, cx - tw // 2: cx + tw // 2]

        if template.size == 0:
            n_ok = len(ok_proc)
            n_ng = len(ng_proc)
            return (
                [False] * n_ok,
                [False] * n_ng,
                {"match_scores": [], "ok_match_scores": [], "ng_match_scores": []},
            )

        def match_score(img: np.ndarray) -> float:
            gray = _ensure_gray(img)
            if gray.shape[0] < template.shape[0] or gray.shape[1] < template.shape[1]:
                return 0.0
            res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            val = float(np.max(res))
            return max(0.0, val)

        ok_scores = [match_score(img) for img in ok_proc]
        ng_scores = [match_score(img) for img in ng_proc]

        ok_mean = float(np.mean(ok_scores)) if ok_scores else 0.0
        thr = ok_mean * 0.9

        # Defect = image does NOT match the OK template well
        ok_flags = [s < thr for s in ok_scores]
        ng_flags = [s < thr for s in ng_scores]

        details = {
            "match_scores": ok_scores + ng_scores,
            "ok_match_scores": ok_scores,
            "ng_match_scores": ng_scores,
            "threshold": thr,
        }
        return ok_flags, ng_flags, details

    # ── GEOMETRIC ──────────────────────────────────────────────────────────────

    def _run_geometric(
        self,
        item: InspectionItem,
        ok_proc: list[np.ndarray],
        ng_proc: list[np.ndarray],
    ) -> tuple[list[bool], list[bool], dict]:
        def circularity(img: np.ndarray) -> float:
            gray = _ensure_gray(img)
            if float(gray.std()) < 1.0:
                return 1.0  # uniform — treat as perfect
            _, thresh = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                return 1.0
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            perimeter = cv2.arcLength(c, True)
            if perimeter < 1e-6:
                return 1.0
            return float(4.0 * np.pi * area / (perimeter ** 2))

        ok_scores = [circularity(img) for img in ok_proc]
        ng_scores = [circularity(img) for img in ng_proc]
        baseline = float(np.mean(ok_scores)) if ok_scores else 1.0
        std = float(np.std(ok_scores)) if len(ok_scores) > 1 else 0.0
        thr = max(std * 2.0, 0.1)

        ok_flags = [abs(s - baseline) > thr for s in ok_scores]
        ng_flags = [abs(s - baseline) > thr for s in ng_scores]

        details = {
            "geometric_scores": ok_scores + ng_scores,
            "ok_geometric_scores": ok_scores,
            "ng_geometric_scores": ng_scores,
            "baseline": baseline,
            "threshold": thr,
        }
        return ok_flags, ng_flags, details
