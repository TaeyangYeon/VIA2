"""TestAgentAlign — runs alignment coordinate detection on OK images.

Implements Template → Edge → Caliper fallback chain with per-image metrics.
Pure OpenCV + NumPy — no LLM or network calls.
"""
import time
from typing import Optional

import cv2
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, ProcessingPipeline
from agents.parameter_searcher import _apply_block


def _ensure_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def _apply_pipeline_to_roi(
    pipeline: ProcessingPipeline,
    image: np.ndarray,
    roi: dict,
) -> np.ndarray:
    x1 = int(roi["x1"])
    y1 = int(roi["y1"])
    x2 = int(roi["x2"])
    y2 = int(roi["y2"])
    region = image[y1:y2, x1:x2].copy()
    for block in pipeline.blocks:
        region = _apply_block(region, block.block_id, block.params)
    return region


def _build_template(proc_roi: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Return (template_gray, tmpl_w, tmpl_h) from center 50% of proc_roi."""
    gray = _ensure_gray(proc_roi)
    rh, rw = gray.shape[:2]
    tmpl_h = max(1, rh // 2)
    tmpl_w = max(1, rw // 2)
    cy, cx = rh // 2, rw // 2
    y0 = cy - tmpl_h // 2
    x0 = cx - tmpl_w // 2
    tmpl = gray[y0: y0 + tmpl_h, x0: x0 + tmpl_w]
    if tmpl.size == 0 or tmpl.shape[0] >= rh or tmpl.shape[1] >= rw:
        # Fallback: top-left third
        tmpl_h = max(1, rh // 3)
        tmpl_w = max(1, rw // 3)
        tmpl = gray[:tmpl_h, :tmpl_w]
    return tmpl, tmpl.shape[1], tmpl.shape[0]


def _detect_template(
    proc_roi: np.ndarray,
    template: np.ndarray,
) -> tuple[float, float, float]:
    """Returns (x_in_roi, y_in_roi, score). score < 0 means failed."""
    search = _ensure_gray(proc_roi)
    tmpl = _ensure_gray(template)
    th, tw = tmpl.shape[:2]
    sh, sw = search.shape[:2]
    if sh < th or sw < tw:
        return 0.0, 0.0, -1.0
    res = cv2.matchTemplate(search, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    x = float(max_loc[0]) + tw / 2.0
    y = float(max_loc[1]) + th / 2.0
    return x, y, float(max(0.0, max_val))


def _detect_edge(proc_roi: np.ndarray) -> tuple[float, float, int]:
    """Returns (x_in_roi, y_in_roi, edge_point_count)."""
    gray = _ensure_gray(proc_roi)
    edges = cv2.Canny(gray, 50, 150)
    ys, xs = np.nonzero(edges)
    count = int(len(xs))
    if count < 2:
        return 0.0, 0.0, count
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=10, minLineLength=5, maxLineGap=5
    )
    if lines is not None and len(lines) >= 2:
        pts = lines.reshape(-1, 4)
        all_x = np.concatenate([pts[:, 0], pts[:, 2]]).astype(float)
        all_y = np.concatenate([pts[:, 1], pts[:, 3]]).astype(float)
        return float(np.mean(all_x)), float(np.mean(all_y)), count
    return float(np.mean(xs)), float(np.mean(ys)), count


def _detect_caliper(proc_roi: np.ndarray) -> tuple[float, float]:
    """Scans middle row/column for steepest gradient pairs, returns center."""
    gray = _ensure_gray(proc_roi)
    h, w = gray.shape[:2]

    def _center_from_profile(profile: np.ndarray) -> float:
        n = len(profile)
        if n < 2:
            return float(n) / 2.0
        grad = np.abs(np.diff(profile.astype(float)))
        if grad.max() < 1.0:
            return float(n) / 2.0
        top2 = np.argsort(grad)[-2:]
        peaks = sorted(top2.tolist())
        return (peaks[0] + peaks[1]) / 2.0 if len(peaks) == 2 else float(peaks[0])

    cx = _center_from_profile(gray[h // 2, :])
    cy = _center_from_profile(gray[:, w // 2])
    return cx, cy


class TestAgentAlign(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__("test_agent_align", directive)

    async def run(
        self,
        pipeline: ProcessingPipeline,
        ok_images: list,
        roi: Optional[dict] = None,
        error_threshold: float = 5.0,
        directive: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.monotonic()
        effective = directive if directive is not None else self.directive

        if not ok_images:
            return AgentResult(
                status="error",
                data={},
                error_message="No OK images provided",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )
        if roi is None:
            return AgentResult(
                status="error",
                data={},
                error_message="ROI is required for align mode",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )
        roi_w = int(roi["x2"]) - int(roi["x1"])
        roi_h = int(roi["y2"]) - int(roi["y1"])
        if roi_w < 3 or roi_h < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="ROI too small for alignment",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        d_lower = effective.lower()
        if "strict" in d_lower:
            error_threshold *= 0.5
        elif "lenient" in d_lower:
            error_threshold *= 2.0

        x1, y1, x2, y2 = int(roi["x1"]), int(roi["y1"]), int(roi["x2"]), int(roi["y2"])
        gt_x = (x1 + x2) / 2.0
        gt_y = (y1 + y2) / 2.0

        processed_rois = [_apply_pipeline_to_roi(pipeline, img, roi) for img in ok_images]

        template, tmpl_w, tmpl_h = _build_template(processed_rois[0])

        per_image_results = []
        method_stats = {"template": 0, "edge": 0, "caliper": 0}

        for i, proc_roi in enumerate(processed_rois):
            det_x, det_y, method, match_score = self._detect_position(
                proc_roi, template, tmpl_w, tmpl_h
            )
            det_x_full = float(np.clip(x1 + det_x, x1, x2))
            det_y_full = float(np.clip(y1 + det_y, y1, y2))
            err = float(np.sqrt((det_x_full - gt_x) ** 2 + (det_y_full - gt_y) ** 2))
            method_stats[method] += 1
            per_image_results.append({
                "image_index": i,
                "detected_x": det_x_full,
                "detected_y": det_y_full,
                "ground_truth_x": gt_x,
                "ground_truth_y": gt_y,
                "error_px": err,
                "method_used": method,
                "match_score": match_score,
                "success": err < error_threshold,
            })

        errors = [r["error_px"] for r in per_image_results]
        success_rate = sum(1 for r in per_image_results if r["success"]) / len(per_image_results)

        return AgentResult(
            status="success",
            data={
                "per_image_results": per_image_results,
                "overall_success_rate": success_rate,
                "overall_mean_error": float(np.mean(errors)),
                "overall_max_error": float(np.max(errors)),
                "overall_passed": success_rate >= 0.8,
                "method_stats": method_stats,
                "error_threshold": error_threshold,
                "total_images": len(per_image_results),
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )

    def _detect_position(
        self,
        proc_roi: np.ndarray,
        template: np.ndarray,
        tmpl_w: int,
        tmpl_h: int,
    ) -> tuple[float, float, str, Optional[float]]:
        """Returns (x_in_roi, y_in_roi, method_name, match_score_or_None)."""
        x, y, score = _detect_template(proc_roi, template)
        if score >= 0.5:
            return x, y, "template", score

        ex, ey, count = _detect_edge(proc_roi)
        if count >= 2:
            return ex, ey, "edge", None

        cx, cy = _detect_caliper(proc_roi)
        return cx, cy, "caliper", None
