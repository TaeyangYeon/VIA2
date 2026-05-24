"""Orchestrator — connects all VIA2 agents into a single pipeline with retry logic."""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Optional

import numpy as np

from agents.algorithm_selector import AlgorithmSelector
from agents.blueprint_agent import BlueprintAgent
from agents.decision_agent import DecisionAgent
from agents.depth_agent import DepthAgent
from agents.evaluation_agent import EvaluationAgent
from agents.feedback_controller import FeedbackController
from agents.image_analysis_agent import ImageAnalysisAgent
from agents.inspection_plan_agent import InspectionPlanAgent
from agents.material_agent import MaterialAgent
from agents.models import (
    AgentDirectives,
    AgentResult,
    AlgorithmCategory,
    Blueprint,
    BlueprintEdge,
    BlueprintNode,
    InspectionItem,
    InspectionPlan,
    ProcessingPipeline,
    SceneContext,
)
from agents.parameter_searcher import ParameterSearcher
from agents.parameter_sheet import ParameterSheetGenerator
from agents.pipeline_composer import PipelineComposer
from agents.pipeline_selection import PipelineSelector
from agents.roi_agent import ROIAgent
from agents.scene_context import build_scene_context
from agents.spec_agent import SpecAgent
from agents.test_agent_align import TestAgentAlign
from agents.test_agent_inspection import TestAgentInspection
from agents.vision_judge_agent import VisionJudgeAgent
from backend.services.ai_adapter.base import BaseAIAdapter
from backend.services.logger import get_agent_logger


# Stage order for retry logic (compose=0, select=1, algorithm=2, plan=3, test=4)
_STAGE_ORDER = ["compose", "select", "algorithm", "plan", "test"]

# Maps failure_reason value → retry start stage
_FAILURE_TO_STAGE: dict[str, str] = {
    "pipeline_bad_fit": "compose",
    "pipeline_bad_params": "select",
    "algorithm_wrong_category": "compose",
    "runtime_error": "select",
    "inspection_plan_issue": "plan",
    "spec_issue": "compose",
}


def _stage_index(stage: str) -> int:
    try:
        return _STAGE_ORDER.index(stage)
    except ValueError:
        return 0


def _validate_success_criteria(criteria: dict) -> Optional[str]:
    """Return error message if any criterion is out of [0, 1], else None."""
    for key in ("min_accuracy", "max_fp_rate", "max_fn_rate"):
        val = criteria.get(key)
        if val is not None:
            v = float(val)
            if v > 1.0 or v < 0.0:
                return f"success_criteria.{key} must be in [0, 1], got {v}"
    return None


def _reconstruct_inspection_plan(plan_dict: dict) -> InspectionPlan:
    items = [
        InspectionItem(
            item_id=item["item_id"],
            name=item["name"],
            category=item.get("category", ""),
            depends_on=item.get("depends_on", []),
            safety_role=item.get("safety_role", False),
            success_criteria=item.get("success_criteria", {}),
        )
        for item in plan_dict.get("items", [])
    ]
    return InspectionPlan(
        items=items,
        inspection_purpose=plan_dict.get("inspection_purpose", ""),
    )


def _reconstruct_blueprint(blueprint_dict: dict) -> Blueprint:
    nodes = [
        BlueprintNode(
            node_id=n["node_id"],
            node_type=n["node_type"],
            label=n["label"],
            params=n.get("params", {}),
        )
        for n in blueprint_dict.get("nodes", [])
    ]
    edges = [
        BlueprintEdge(
            source_id=e["source_id"],
            target_id=e["target_id"],
            label=e.get("label", ""),
        )
        for e in blueprint_dict.get("edges", [])
    ]
    return Blueprint(
        nodes=nodes,
        edges=edges,
        svg_content=blueprint_dict.get("svg_content", ""),
        algorithm_description=blueprint_dict.get("algorithm_description", ""),
    )


class Orchestrator:
    """Coordinates all VIA2 agents into a single automated vision pipeline."""

    def __init__(
        self,
        adapter: BaseAIAdapter,
        remote_url: str,
        model: str = "qwen2.5-coder:7b",
        max_iterations: int = 3,
        directives: AgentDirectives | None = None,
    ) -> None:
        self._adapter = adapter
        self._remote_url = remote_url
        self._model = model
        self._max_iterations = max_iterations
        self._directives = directives or AgentDirectives()
        self._logger = get_agent_logger("orchestrator")

        d = self._directives
        self._spec_agent = SpecAgent(adapter, model, d.spec)
        self._image_analysis_agent = ImageAnalysisAgent(d.image_analysis)
        self._depth_agent = DepthAgent(remote_url, d.depth)
        self._material_agent = MaterialAgent(remote_url, d.material)
        self._roi_agent = ROIAgent(remote_url)
        self._pipeline_composer = PipelineComposer(d.pipeline_composer)
        self._parameter_searcher = ParameterSearcher()
        self._vision_judge = VisionJudgeAgent(remote_url, d.vision_judge)
        self._pipeline_selector = PipelineSelector(
            self._parameter_searcher,
            self._vision_judge,
            d.vision_judge,
        )
        self._algorithm_selector = AlgorithmSelector()
        self._inspection_plan_agent = InspectionPlanAgent(adapter, model, d.inspection_plan)
        self._blueprint_agent = BlueprintAgent(adapter, model)
        self._parameter_sheet_gen = ParameterSheetGenerator()
        self._test_agent_inspection = TestAgentInspection(d.test)
        self._test_agent_align = TestAgentAlign(d.test)
        self._evaluation_agent = EvaluationAgent()
        self._feedback_controller = FeedbackController()
        self._decision_agent = DecisionAgent(remote_url)

    async def run(
        self,
        user_text: str,
        images: list[np.ndarray],
        ng_images: list[np.ndarray] | None = None,
        roi: dict | None = None,
        text_query: str | None = None,
        success_criteria: dict | None = None,
    ) -> AgentResult:
        t0 = time.monotonic()

        # ── Input validation ───────────────────────────────────────────
        if not user_text:
            return AgentResult(status="error", data={},
                               error_message="user_text is required")
        if not images:
            return AgentResult(status="error", data={},
                               error_message="images list is empty")
        if success_criteria is not None:
            err = _validate_success_criteria(success_criteria)
            if err is not None:
                return AgentResult(status="error", data={}, error_message=err)

        image = images[0]
        user_success_criteria = success_criteria

        # ── SpecAgent ──────────────────────────────────────────────────
        self._logger.info("orchestrator_step", step="spec_agent")
        spec_result = await self._spec_agent.run(
            user_text=user_text,
            roi=roi,
            directive=self._directives.spec or None,
        )
        if spec_result.status != "success":
            return AgentResult(
                status="error", data={},
                error_message=f"SpecAgent failed: {spec_result.error_message}",
            )

        mode = spec_result.data.get("mode", "inspection")
        purpose = spec_result.data.get("goal", user_text)

        if user_success_criteria is None:
            success_criteria = spec_result.data.get("success_criteria")
        else:
            success_criteria = user_success_criteria

        # ── Mode-specific validation ───────────────────────────────────
        if mode == "inspection" and not ng_images:
            return AgentResult(
                status="error", data={},
                error_message="inspection mode requires ng_images",
            )

        # ── Vision analysis agents ─────────────────────────────────────
        self._logger.info("orchestrator_step", step="image_analysis")
        img_analysis_result = await self._image_analysis_agent.run(
            image=image, roi=roi)

        self._logger.info("orchestrator_step", step="depth_agent")
        depth_result = await self._depth_agent.run(image=image, roi=roi)

        self._logger.info("orchestrator_step", step="material_agent")
        material_result = await self._material_agent.run(image=image, roi=roi)

        self._logger.info("orchestrator_step", step="roi_agent")
        roi_result = await self._roi_agent.run(
            image=image, roi=roi, text_query=text_query)

        # ── Scene context ──────────────────────────────────────────────
        scene_context = build_scene_context(
            image_analysis_result=img_analysis_result,
            depth_result=depth_result,
            material_result=material_result,
            roi_result=roi_result,
        )
        effective_roi = scene_context.roi or roi

        # ── Retry loop ─────────────────────────────────────────────────
        start_stage = "compose"
        pipelines: list[ProcessingPipeline] | None = None
        selected_pipeline: ProcessingPipeline | None = None
        algorithm_category: AlgorithmCategory | None = None
        inspection_plan: InspectionPlan | None = None
        blueprint_data: dict | None = None
        parameter_sheets: list[dict] | None = None
        test_result: AgentResult | None = None
        eval_result: AgentResult | None = None
        feedback_context: dict | None = None

        for iteration in range(self._max_iterations):
            self._logger.info("orchestrator_iteration",
                              iteration=iteration, start_stage=start_stage)
            idx = _stage_index(start_stage)

            # ── COMPOSE ────────────────────────────────────────────────
            if idx <= _stage_index("compose"):
                composer_result = await self._pipeline_composer.run(
                    scene_context=scene_context)
                if composer_result.status != "success":
                    return AgentResult(
                        status="error", data={},
                        error_message=f"PipelineComposer failed: {composer_result.error_message}",
                    )
                pipelines = composer_result.data["pipelines"]

            # ── SELECT ─────────────────────────────────────────────────
            if idx <= _stage_index("select"):
                selector_result = await self._pipeline_selector.run(
                    pipelines=pipelines,
                    image=image,
                    purpose=purpose,
                    roi=effective_roi,
                    directive=self._directives.vision_judge or None,
                )
                if selector_result.status != "success":
                    return AgentResult(
                        status="error", data={},
                        error_message=f"PipelineSelector failed: {selector_result.error_message}",
                    )
                selected_pipeline = selector_result.data["selected_pipeline"]

            # ── ALGORITHM ──────────────────────────────────────────────
            if idx <= _stage_index("algorithm"):
                algo_result = await self._algorithm_selector.run(
                    scene_context=scene_context)
                if algo_result.status != "success":
                    return AgentResult(
                        status="error", data={},
                        error_message=f"AlgorithmSelector failed: {algo_result.error_message}",
                    )
                algorithm_category = AlgorithmCategory(algo_result.data["category"])

            # ── PLAN (inspection only) ─────────────────────────────────
            if mode == "inspection" and idx <= _stage_index("plan"):
                plan_result = await self._inspection_plan_agent.run(
                    purpose=purpose,
                    scene_context=scene_context,
                    algorithm_category=algorithm_category,
                    directive=self._directives.inspection_plan or None,
                )
                if plan_result.status != "success":
                    return AgentResult(
                        status="error", data={},
                        error_message=f"InspectionPlanAgent failed: {plan_result.error_message}",
                    )
                inspection_plan = _reconstruct_inspection_plan(plan_result.data["plan"])

                blueprint_result = await self._blueprint_agent.run(
                    pipeline=selected_pipeline,
                    inspection_plan=inspection_plan,
                )
                if blueprint_result.status != "success":
                    return AgentResult(
                        status="error", data={},
                        error_message=f"BlueprintAgent failed: {blueprint_result.error_message}",
                    )
                blueprint_data = blueprint_result.data["blueprint"]
                blueprint_obj = _reconstruct_blueprint(blueprint_data)

                sheets = self._parameter_sheet_gen.generate(
                    blueprint=blueprint_obj,
                    pipeline=selected_pipeline,
                    inspection_plan=inspection_plan,
                )
                parameter_sheets = [s.to_dict() for s in sheets]

            # ── TEST ───────────────────────────────────────────────────
            if mode == "inspection":
                test_result = await self._test_agent_inspection.run(
                    inspection_plan=inspection_plan,
                    pipeline=selected_pipeline,
                    ok_images=images,
                    ng_images=ng_images,
                    roi=effective_roi,
                    directive=self._directives.test or None,
                )
            else:
                test_result = await self._test_agent_align.run(
                    pipeline=selected_pipeline,
                    ok_images=images,
                    roi=effective_roi,
                    directive=self._directives.test or None,
                )

            if test_result.status != "success":
                # Synthesise a runtime-error evaluation so FeedbackController can run
                synthetic_eval = AgentResult(
                    status="success",
                    data={
                        "item_evaluations": [{
                            "item_id": 0, "passed": False,
                            "failure_reason": "runtime_error",
                            "details": f"test failed: {test_result.error_message}",
                        }],
                        "overall_passed": False,
                        "failure_summary": {"runtime_error": 1},
                    },
                )
                fb = await self._feedback_controller.run(
                    evaluation_result=synthetic_eval,
                    pipeline=selected_pipeline,
                )
                feedback_context = fb.data.get("context") if fb.status == "success" else None
                start_stage = "select"
                continue

            # ── EVALUATION ─────────────────────────────────────────────
            eval_result = await self._evaluation_agent.run(
                test_result=test_result,
                mode=mode,
                pipeline=selected_pipeline,
                inspection_plan=inspection_plan if mode == "inspection" else None,
                success_criteria=success_criteria,
            )
            if eval_result.status != "success":
                return AgentResult(
                    status="error", data={},
                    error_message=f"EvaluationAgent failed: {eval_result.error_message}",
                )

            if eval_result.data.get("overall_passed"):
                return self._build_result(
                    mode=mode,
                    spec_data=spec_result.data,
                    scene_context=scene_context,
                    selected_pipeline=selected_pipeline,
                    algorithm_category=algorithm_category,
                    inspection_plan=inspection_plan,
                    blueprint_data=blueprint_data,
                    parameter_sheets=parameter_sheets,
                    test_data=test_result.data,
                    eval_data=eval_result.data,
                    iterations_used=iteration + 1,
                    decision=None,
                    t0=t0,
                )

            # ── FEEDBACK ───────────────────────────────────────────────
            fb_result = await self._feedback_controller.run(
                evaluation_result=eval_result,
                pipeline=selected_pipeline,
            )
            if fb_result.status == "success":
                feedback_context = fb_result.data.get("context")
                failure_reason = fb_result.data.get("primary_failure_reason") or ""

                if failure_reason == "spec_issue" and success_criteria:
                    sc = dict(success_criteria)
                    if "min_accuracy" in sc:
                        sc["min_accuracy"] = max(0.0, float(sc["min_accuracy"]) - 0.1)
                    success_criteria = sc
                    self._logger.warning("spec_relaxed", new_criteria=success_criteria)

                start_stage = _FAILURE_TO_STAGE.get(failure_reason, "compose")
            else:
                start_stage = "compose"

        # ── Max iterations exceeded → DecisionAgent ────────────────────
        self._logger.warning("max_iterations_exceeded",
                             max_iterations=self._max_iterations)
        decision_images = ng_images if ng_images else images
        decision_result = await self._decision_agent.run(
            mode=mode,
            ng_images=decision_images,
            evaluation_result=eval_result,
            feedback_context=feedback_context,
        )
        decision_data = (
            decision_result.data if decision_result.status == "success" else None
        )

        return self._build_result(
            mode=mode,
            spec_data=spec_result.data,
            scene_context=scene_context,
            selected_pipeline=selected_pipeline,
            algorithm_category=algorithm_category,
            inspection_plan=inspection_plan,
            blueprint_data=blueprint_data,
            parameter_sheets=parameter_sheets,
            test_data=test_result.data if test_result else {},
            eval_data=eval_result.data if eval_result else {},
            iterations_used=self._max_iterations,
            decision=decision_data,
            t0=t0,
        )

    def _build_result(
        self,
        mode: str,
        spec_data: dict,
        scene_context: SceneContext,
        selected_pipeline: ProcessingPipeline | None,
        algorithm_category: AlgorithmCategory | None,
        inspection_plan: InspectionPlan | None,
        blueprint_data: dict | None,
        parameter_sheets: list[dict] | None,
        test_data: dict,
        eval_data: dict,
        iterations_used: int,
        decision: dict | None,
        t0: float,
    ) -> AgentResult:
        diag = scene_context.image_diagnosis
        scene_summary = {
            "contrast": diag.contrast,
            "surface_type": diag.surface_type,
            "depth_complexity": diag.depth_complexity,
            "optimal_color_space": diag.optimal_color_space,
            "roi": scene_context.roi,
        }

        data: dict = {
            "mode": mode,
            "spec": spec_data,
            "scene_context": scene_summary,
            "pipeline": asdict(selected_pipeline) if selected_pipeline else None,
            "algorithm_category": algorithm_category.value if algorithm_category else None,
            "inspection_plan": asdict(inspection_plan) if inspection_plan else None,
            "blueprint": blueprint_data,
            "parameter_sheets": parameter_sheets,
            "test_result": test_data,
            "evaluation": eval_data,
            "iterations_used": iterations_used,
        }
        if decision is not None:
            data["decision"] = decision

        return AgentResult(
            status="success",
            data=data,
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )
