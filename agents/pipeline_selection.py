"""PipelineSelector — evaluates candidate pipelines and picks the best one."""
import time
from typing import Optional

import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, ProcessingPipeline
from agents.parameter_searcher import ParameterSearcher, _apply_block
from agents.vision_judge_agent import VisionJudgeAgent


class PipelineSelector(BaseAgent):
    def __init__(
        self,
        parameter_searcher: ParameterSearcher,
        vision_judge: VisionJudgeAgent,
        directive: str = "",
    ) -> None:
        super().__init__("pipeline_selection", directive)
        self._parameter_searcher = parameter_searcher
        self._vision_judge = vision_judge

    async def run(
        self,
        pipelines: list[ProcessingPipeline],
        image: np.ndarray,
        purpose: str,
        roi: Optional[dict] = None,
        directive: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.monotonic()

        if not pipelines:
            return AgentResult(
                status="error",
                data={},
                error_message="No candidate pipelines provided",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        h, w = image.shape[:2]
        if h < 3 or w < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="Image too small for pipeline selection",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        if not purpose:
            return AgentResult(
                status="error",
                data={},
                error_message="Purpose is required for pipeline selection",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        effective_directive = directive if directive is not None else self.directive

        all_candidates: list[dict] = []
        best_pipeline: Optional[ProcessingPipeline] = None
        best_index: int = -1
        best_combined_score: float = -1.0
        best_quality_score: Optional[dict] = None
        best_judgement: Optional[dict] = None

        for i, pipeline in enumerate(pipelines):
            try:
                search_result = await self._parameter_searcher.run(
                    pipeline=pipeline,
                    image=image,
                    roi=roi,
                    directive=effective_directive,
                )
                if search_result.status != "success":
                    all_candidates.append({
                        "pipeline_id": pipeline.pipeline_id,
                        "combined_score": 0.0,
                        "quality_score": 0.0,
                        "judgement_score": 0.0,
                        "status": "skipped",
                    })
                    continue

                optimized_pipeline: ProcessingPipeline = search_result.data["optimized_pipeline"]
                quality_score: dict = search_result.data["quality_score"]
                quality_overall: float = float(quality_score["overall_score"])

                processed_image = self._execute_pipeline(optimized_pipeline, image, roi)

                judge_result = await self._vision_judge.run(
                    original_image=image,
                    processed_image=processed_image,
                    purpose=purpose,
                    directive=effective_directive,
                )
                if judge_result.status != "success":
                    all_candidates.append({
                        "pipeline_id": pipeline.pipeline_id,
                        "combined_score": 0.0,
                        "quality_score": quality_overall,
                        "judgement_score": 0.0,
                        "status": "skipped",
                    })
                    continue

                judgement: dict = judge_result.data["judgement"]
                judgement_overall = (
                    float(judgement["visibility_score"])
                    + float(judgement["separability_score"])
                    + float(judgement["measurability_score"])
                ) / 3.0

                combined_score = 0.4 * quality_overall + 0.6 * judgement_overall

                all_candidates.append({
                    "pipeline_id": pipeline.pipeline_id,
                    "combined_score": combined_score,
                    "quality_score": quality_overall,
                    "judgement_score": judgement_overall,
                    "status": "success",
                })

                if combined_score > best_combined_score:
                    best_combined_score = combined_score
                    best_pipeline = optimized_pipeline
                    best_index = i
                    best_quality_score = quality_score
                    best_judgement = judgement

            except Exception as exc:
                self._log("warning", f"Candidate {i} failed: {exc}")
                all_candidates.append({
                    "pipeline_id": pipeline.pipeline_id,
                    "combined_score": 0.0,
                    "quality_score": 0.0,
                    "judgement_score": 0.0,
                    "status": "skipped",
                })

        if best_pipeline is None:
            return AgentResult(
                status="error",
                data={},
                error_message="All candidate pipelines failed evaluation",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        return AgentResult(
            status="success",
            data={
                "selected_pipeline": best_pipeline,
                "selected_index": best_index,
                "combined_score": best_combined_score,
                "quality_score": best_quality_score,
                "judgement": best_judgement,
                "all_candidates": all_candidates,
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )

    def _execute_pipeline(
        self,
        pipeline: ProcessingPipeline,
        image: np.ndarray,
        roi: Optional[dict],
    ) -> np.ndarray:
        work_image = image
        if roi is not None:
            x1 = int(roi.get("x1", 0))
            y1 = int(roi.get("y1", 0))
            x2 = int(roi.get("x2", image.shape[1]))
            y2 = int(roi.get("y2", image.shape[0]))
            work_image = image[y1:y2, x1:x2]

        current = work_image.copy()
        for block in pipeline.blocks:
            current = _apply_block(current, block.block_id, block.params)
        return current
