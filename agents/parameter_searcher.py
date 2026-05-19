"""Parameter searcher — finds optimal parameters for a ProcessingPipeline via OpenCV evaluation."""
import itertools
import logging
import random
import time
from dataclasses import asdict
from typing import Optional

import cv2
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, PipelineBlock, ProcessingPipeline
from agents.pipeline_blocks import BLOCK_REGISTRY
from agents.processing_quality_evaluator import ProcessingQualityEvaluator

logger = logging.getLogger(__name__)


def _ensure_gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def _ensure_bgr(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img


def _apply_block(img: np.ndarray, block_id: str, params: dict) -> np.ndarray:
    """Apply one block to an image using specific (non-list) param values."""

    # ── color space ───────────────────────────────────────────────────────────
    if block_id == "grayscale":
        return _ensure_gray(img)
    if block_id == "hsv_s":
        return cv2.split(cv2.cvtColor(_ensure_bgr(img), cv2.COLOR_BGR2HSV))[1]
    if block_id == "hsv_v":
        return cv2.split(cv2.cvtColor(_ensure_bgr(img), cv2.COLOR_BGR2HSV))[2]
    if block_id == "lab_l":
        return cv2.split(cv2.cvtColor(_ensure_bgr(img), cv2.COLOR_BGR2LAB))[0]
    if block_id == "ycrcb_cr":
        return cv2.split(cv2.cvtColor(_ensure_bgr(img), cv2.COLOR_BGR2YCrCb))[1]

    # ── denoise ───────────────────────────────────────────────────────────────
    if block_id in ("gaussian_fine", "gaussian_mid"):
        ksize = int(params.get("kernel_size", 3)) | 1  # ensure odd
        sigma = float(params.get("sigma", 1.0))
        return cv2.GaussianBlur(img, (ksize, ksize), sigma)

    if block_id == "bilateral":
        gray = _ensure_gray(img)
        d = int(params.get("d", 5))
        sc = float(params.get("sigma_color", 75))
        ss = float(params.get("sigma_space", 75))
        return cv2.bilateralFilter(gray, d, sc, ss)

    if block_id == "median":
        ksize = int(params.get("kernel_size", 3)) | 1
        return cv2.medianBlur(img, ksize)

    if block_id == "nlmeans":
        gray = _ensure_gray(img)
        h = float(params.get("h", 10))
        tw = int(params.get("template_window_size", 7))
        sw = int(params.get("search_window_size", 21))
        return cv2.fastNlMeansDenoising(gray, h=h, templateWindowSize=tw, searchWindowSize=sw)

    if block_id == "clahe":
        gray = _ensure_gray(img)
        clip = float(params.get("clip_limit", 2.0))
        tgs = params.get("tile_grid_size", (8, 8))
        tgs = tuple(int(x) for x in tgs)
        return cv2.createCLAHE(clipLimit=clip, tileGridSize=tgs).apply(gray)

    # ── threshold ─────────────────────────────────────────────────────────────
    if block_id == "otsu":
        gray = _ensure_gray(img)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    if block_id == "adaptive_mean":
        gray = _ensure_gray(img)
        bs = max(3, int(params.get("block_size", 11)) | 1)
        c = int(params.get("c", 5))
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, bs, c)

    if block_id == "adaptive_gauss":
        gray = _ensure_gray(img)
        bs = max(3, int(params.get("block_size", 11)) | 1)
        c = int(params.get("c", 5))
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, bs, c)

    if block_id == "dynamic_threshold":
        gray = _ensure_gray(img)
        offset = int(params.get("offset", 0))
        thresh_val = int(np.clip(float(np.mean(gray)) + offset, 0, 255))
        _, result = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        return result

    # ── morphology ────────────────────────────────────────────────────────────
    if block_id in ("erosion", "dilation", "opening", "closing", "tophat", "blackhat", "morph_gradient"):
        gray = _ensure_gray(img)
        ksize = max(1, int(params.get("kernel_size", 3)) | 1)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
        iterations = int(params.get("iterations", 1))
        if block_id == "erosion":
            return cv2.erode(gray, kernel, iterations=iterations)
        if block_id == "dilation":
            return cv2.dilate(gray, kernel, iterations=iterations)
        op_map = {
            "opening": cv2.MORPH_OPEN,
            "closing": cv2.MORPH_CLOSE,
            "tophat": cv2.MORPH_TOPHAT,
            "blackhat": cv2.MORPH_BLACKHAT,
            "morph_gradient": cv2.MORPH_GRADIENT,
        }
        return cv2.morphologyEx(gray, op_map[block_id], kernel)

    # ── edge ──────────────────────────────────────────────────────────────────
    if block_id == "canny":
        gray = _ensure_gray(img)
        lo = int(params.get("low_threshold", 50))
        hi = int(params.get("high_threshold", 150))
        return cv2.Canny(gray, lo, hi)

    if block_id == "sobel":
        gray = _ensure_gray(img)
        ksize = max(1, int(params.get("ksize", 3)) | 1)
        sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
        sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
        return np.clip(np.sqrt(sx ** 2 + sy ** 2), 0, 255).astype(np.uint8)

    if block_id == "laplacian":
        gray = _ensure_gray(img)
        ksize = max(1, int(params.get("ksize", 3)) | 1)
        lap = cv2.Laplacian(gray, cv2.CV_64F, ksize=ksize)
        return np.clip(np.abs(lap), 0, 255).astype(np.uint8)

    if block_id == "scharr":
        gray = _ensure_gray(img)
        sx = cv2.Scharr(gray, cv2.CV_64F, 1, 0)
        sy = cv2.Scharr(gray, cv2.CV_64F, 0, 1)
        return np.clip(np.sqrt(sx ** 2 + sy ** 2), 0, 255).astype(np.uint8)

    # Unknown block: pass through
    return img


def _param_combos_for_block(block: PipelineBlock) -> list[dict]:
    """Return list of specific-value param dicts for a single block."""
    block_def = BLOCK_REGISTRY.get(block.block_id)
    search_params = block_def.params if block_def is not None else block.params

    if not search_params:
        return [{}]

    param_names = list(search_params.keys())
    param_value_lists = [search_params[k] for k in param_names]

    return [
        dict(zip(param_names, combo))
        for combo in itertools.product(*param_value_lists)
    ]


class ParameterSearcher(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__("parameter_searcher", directive)
        self._evaluator = ProcessingQualityEvaluator()

    async def run(
        self,
        pipeline: ProcessingPipeline,
        image: np.ndarray,
        roi: Optional[dict] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.monotonic()

        if not pipeline.blocks:
            return AgentResult(
                status="error",
                data={},
                error_message="Pipeline has no blocks",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        h, w = image.shape[:2]
        if h < 3 or w < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="Image too small for parameter search",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        directive_lower = self.directive.lower()
        if "fast" in directive_lower:
            max_evals = 30
        elif "thorough" in directive_lower:
            max_evals = 300
        else:
            max_evals = 100

        per_block_combos = [_param_combos_for_block(b) for b in pipeline.blocks]

        total = 1
        for combos in per_block_combos:
            total *= len(combos)

        all_combinations: list[tuple] = list(itertools.product(*per_block_combos))

        if len(all_combinations) > max_evals:
            random.seed(42)
            all_combinations = random.sample(all_combinations, max_evals)

        # Crop to ROI for evaluation (full image is used for block application)
        eval_image = image
        if roi is not None:
            x = int(roi.get("x", 0))
            y = int(roi.get("y", 0))
            w_roi = int(roi.get("width", image.shape[1]))
            h_roi = int(roi.get("height", image.shape[0]))
            eval_image = image[y: y + h_roi, x: x + w_roi]

        evaluated = 0
        best_score = -1.0
        best_combo: Optional[tuple] = None
        best_quality = None

        for combo in all_combinations:
            try:
                current = eval_image.copy()
                for block, block_params in zip(pipeline.blocks, combo):
                    current = _apply_block(current, block.block_id, block_params)
                quality = self._evaluator.evaluate(eval_image, current)
                evaluated += 1
                if quality.overall_score > best_score:
                    best_score = quality.overall_score
                    best_combo = combo
                    best_quality = quality
            except Exception as exc:
                logger.warning("Skipping combination due to error: %s", exc)

        if best_combo is None:
            return AgentResult(
                status="error",
                data={},
                error_message="All parameter combinations failed",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        optimized_blocks = [
            PipelineBlock(
                block_id=block.block_id,
                block_type=block.block_type,
                params=dict(params),
            )
            for block, params in zip(pipeline.blocks, best_combo)
        ]

        optimized_pipeline = ProcessingPipeline(
            pipeline_id=pipeline.pipeline_id,
            blocks=optimized_blocks,
            quality_score=best_score,
            judge_score=pipeline.judge_score,
            description=pipeline.description,
        )

        return AgentResult(
            status="success",
            data={
                "optimized_pipeline": optimized_pipeline,
                "quality_score": asdict(best_quality),
                "search_summary": {
                    "total_combinations": total,
                    "evaluated": evaluated,
                    "best_score": best_score,
                },
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )
