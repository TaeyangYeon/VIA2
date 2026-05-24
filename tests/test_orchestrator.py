"""Tests for Orchestrator — Step 33. All sub-agents are mocked."""
import asyncio
import unittest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch, call

import numpy as np
import pytest

from agents.models import (
    AgentDirectives,
    AgentResult,
    AlgorithmCategory,
    Blueprint,
    BlueprintEdge,
    BlueprintNode,
    FailureReason,
    ImageDiagnosis,
    InspectionItem,
    InspectionPlan,
    ProcessingPipeline,
    PipelineBlock,
    SceneContext,
)
from backend.services.ai_adapter.base import BaseAIAdapter


# ── helpers ───────────────────────────────────────────────────────────────────

def _img(h: int = 10, w: int = 10) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _default_diagnosis() -> ImageDiagnosis:
    return ImageDiagnosis(
        contrast=0.3, noise_level=0.1, edge_density=0.2,
        lighting_uniformity=0.1, illumination_type="uniform",
        noise_frequency="low_freq", reflection_level=0.0,
        surface_type="metal", depth_complexity=0.1,
        has_shadow_region=False, blob_feasibility=0.5,
        blob_count_estimate=2, color_discriminability=0.3,
        dominant_channel_ratio=0.5, structural_regularity=0.5,
        pattern_repetition=0.3, optimal_color_space="gray",
        threshold_candidate=128.0, edge_sharpness=10.0,
    )


def _make_pipeline(pid: str = "pipe_01") -> ProcessingPipeline:
    return ProcessingPipeline(
        pipeline_id=pid,
        blocks=[PipelineBlock(block_id="grayscale", block_type="color_space")],
    )


def _make_inspection_plan() -> InspectionPlan:
    return InspectionPlan(
        items=[InspectionItem(
            item_id=1, name="Test Item", category="BLOB",
            success_criteria={"min_accuracy": 0.8},
        )],
        inspection_purpose="test purpose",
    )


def _make_blueprint() -> Blueprint:
    return Blueprint(
        nodes=[
            BlueprintNode(node_id="pre_grayscale", node_type="preprocessing", label="grayscale"),
            BlueprintNode(node_id="insp_1", node_type="inspection", label="Test Item"),
            BlueprintNode(node_id="decision", node_type="decision", label="Pass / Fail"),
        ],
        edges=[
            BlueprintEdge(source_id="pre_grayscale", target_id="insp_1"),
            BlueprintEdge(source_id="insp_1", target_id="decision"),
        ],
        svg_content="<svg></svg>",
        algorithm_description="test description",
    )


def _spec_result(mode: str = "inspection", criteria: dict | None = None) -> AgentResult:
    return AgentResult(status="success", data={
        "mode": mode,
        "goal": "test goal",
        "success_criteria": criteria or {"min_accuracy": 0.9},
    })


def _eval_passed() -> AgentResult:
    return AgentResult(status="success", data={
        "item_evaluations": [{"item_id": 1, "passed": True, "failure_reason": None, "details": "passed"}],
        "overall_passed": True,
        "total_items": 1, "passed_items": 1, "failed_items": 0,
        "failure_summary": {},
    })


def _eval_failed(reason: str = "pipeline_bad_fit") -> AgentResult:
    return AgentResult(status="success", data={
        "item_evaluations": [{"item_id": 1, "passed": False, "failure_reason": reason, "details": "failed"}],
        "overall_passed": False,
        "total_items": 1, "passed_items": 0, "failed_items": 1,
        "failure_summary": {reason: 1},
    })


def _feedback_result(reason: str = "pipeline_bad_fit", strategy: str = "replace_pipeline") -> AgentResult:
    return AgentResult(status="success", data={
        "strategy": strategy,
        "severity": "high",
        "primary_failure_reason": reason,
        "context": {
            "iteration": 1,
            "tried_strategies": [strategy],
            "failed_pipelines": ["pipe_01"],
            "constraints": [],
            "history": [],
        },
        "hints": [],
        "should_continue": True,
        "vision_judge_suggestion": None,
    })


def _decision_result() -> AgentResult:
    return AgentResult(status="success", data={
        "verdict": "deep_learning",
        "confidence": 0.8,
        "reasoning": "test reasoning",
        "recommendation": "use deep learning",
        "dinov2_variability": 0.5,
        "internvl_analysis": None,
        "vision_judge_avg_score": None,
    })


def _make_orchestrator(adapter=None, max_iterations: int = 3,
                       directives: AgentDirectives | None = None):
    """Create Orchestrator (imports deferred to avoid import errors before impl exists)."""
    from agents.orchestrator import Orchestrator
    adapter = adapter or MagicMock(spec=BaseAIAdapter)
    return Orchestrator(adapter, "http://mock:8000",
                        model="test-model",
                        max_iterations=max_iterations,
                        directives=directives)


def _wire_happy_inspection(orc, pipeline=None, plan=None, blueprint=None,
                            eval_result=None):
    """Replace all sub-agent run() methods with mocks for a successful inspection flow."""
    pipeline = pipeline or _make_pipeline()
    plan = plan or _make_inspection_plan()
    blueprint = blueprint or _make_blueprint()

    orc._spec_agent.run = AsyncMock(return_value=_spec_result("inspection"))
    orc._image_analysis_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"diagnosis": _default_diagnosis()}))
    orc._depth_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"depth_map": None, "depth_stats": {}}))
    orc._material_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"surface_type": "metal", "material_map": {}}))
    orc._roi_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"mode": "manual", "roi": {"x1": 0, "y1": 0, "x2": 5, "y2": 5}}))
    orc._pipeline_composer.run = AsyncMock(return_value=AgentResult(
        status="success", data={"pipelines": [pipeline], "num_candidates": 1,
                                "matching_blocks_summary": {}}))
    orc._pipeline_selector.run = AsyncMock(return_value=AgentResult(
        status="success", data={"selected_pipeline": pipeline, "combined_score": 0.8,
                                "quality_score": {"overall_score": 0.8},
                                "judgement": {"visibility_score": 0.8,
                                              "separability_score": 0.8,
                                              "measurability_score": 0.8,
                                              "overall_score": 0.8},
                                "all_candidates": []}))
    orc._algorithm_selector.run = AsyncMock(return_value=AgentResult(
        status="success", data={"category": "blob", "reason": "test",
                                "scores": {}, "decision_path": []}))
    orc._inspection_plan_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"plan": asdict(plan), "raw_response": "[]"}))
    orc._blueprint_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"blueprint": asdict(blueprint), "svg": "<svg></svg>",
                                "description": "test", "node_count": 3, "edge_count": 2}))
    orc._test_agent_inspection.run = AsyncMock(return_value=AgentResult(
        status="success", data={"item_results": [
            {"item_id": 1, "name": "Test Item", "category": "BLOB",
             "accuracy": 0.95, "fp_rate": 0.05, "fn_rate": 0.05,
             "passed": True, "skipped": False, "details": {}}
        ], "overall_accuracy": 0.95, "overall_passed": True,
           "execution_order": [1], "total_items": 1,
           "passed_items": 1, "skipped_items": 0, "failed_items": 0}))
    orc._evaluation_agent.run = AsyncMock(return_value=eval_result or _eval_passed())
    orc._feedback_controller.run = AsyncMock(return_value=_feedback_result())
    orc._decision_agent.run = AsyncMock(return_value=_decision_result())
    return orc


def _wire_happy_align(orc, pipeline=None):
    """Replace sub-agent run() methods for a successful align flow."""
    pipeline = pipeline or _make_pipeline()

    orc._spec_agent.run = AsyncMock(return_value=_spec_result("align"))
    orc._image_analysis_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"diagnosis": _default_diagnosis()}))
    orc._depth_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"depth_map": None, "depth_stats": {}}))
    orc._material_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"surface_type": "metal", "material_map": {}}))
    orc._roi_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"mode": "manual", "roi": {"x1": 0, "y1": 0, "x2": 5, "y2": 5}}))
    orc._pipeline_composer.run = AsyncMock(return_value=AgentResult(
        status="success", data={"pipelines": [pipeline], "num_candidates": 1,
                                "matching_blocks_summary": {}}))
    orc._pipeline_selector.run = AsyncMock(return_value=AgentResult(
        status="success", data={"selected_pipeline": pipeline, "combined_score": 0.8,
                                "quality_score": {"overall_score": 0.8},
                                "judgement": {"visibility_score": 0.8,
                                              "separability_score": 0.8,
                                              "measurability_score": 0.8,
                                              "overall_score": 0.8},
                                "all_candidates": []}))
    orc._algorithm_selector.run = AsyncMock(return_value=AgentResult(
        status="success", data={"category": "blob", "reason": "test",
                                "scores": {}, "decision_path": []}))
    orc._inspection_plan_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"plan": asdict(_make_inspection_plan()), "raw_response": "[]"}))
    orc._blueprint_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"blueprint": asdict(_make_blueprint()), "svg": "<svg></svg>",
                                "description": "test", "node_count": 3, "edge_count": 2}))
    orc._test_agent_inspection.run = AsyncMock(return_value=AgentResult(
        status="success", data={"item_results": [], "overall_passed": True,
                                "overall_accuracy": 1.0, "execution_order": [],
                                "total_items": 0, "passed_items": 0,
                                "skipped_items": 0, "failed_items": 0}))
    orc._test_agent_align.run = AsyncMock(return_value=AgentResult(
        status="success", data={"per_image_results": [
            {"image_index": 0, "detected_x": 5.0, "detected_y": 5.0,
             "ground_truth_x": 5.0, "ground_truth_y": 5.0,
             "error_px": 0.0, "method_used": "template",
             "match_score": 0.9, "success": True}
        ], "overall_success_rate": 1.0, "overall_mean_error": 0.0,
           "overall_max_error": 0.0, "overall_passed": True,
           "method_stats": {"template": 1, "edge": 0, "caliper": 0},
           "error_threshold": 5.0, "total_images": 1}))
    orc._evaluation_agent.run = AsyncMock(return_value=AgentResult(
        status="success", data={"item_evaluations": [
            {"item_id": 0, "passed": True, "failure_reason": None,
             "details": "error_px=0.000, method=template"}
        ], "overall_passed": True, "failure_reason": None,
           "total_items": 1, "passed_items": 1, "failed_items": 0,
           "failure_summary": {}}))
    orc._feedback_controller.run = AsyncMock(return_value=_feedback_result())
    orc._decision_agent.run = AsyncMock(return_value=_decision_result())
    return orc


# ─────────────────────────────────────────────────────────────────────────────
# 1. Instantiation
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorInstantiation(unittest.TestCase):
    def setUp(self):
        from agents.orchestrator import Orchestrator
        self.Orchestrator = Orchestrator

    def _make(self, **kwargs):
        adapter = MagicMock(spec=BaseAIAdapter)
        return self.Orchestrator(adapter, "http://test:8000", **kwargs)

    def test_default_model(self):
        orc = self._make()
        self.assertEqual(orc._model, "qwen2.5-coder:7b")

    def test_default_max_iterations(self):
        orc = self._make()
        self.assertEqual(orc._max_iterations, 3)

    def test_default_directives_is_empty(self):
        orc = self._make()
        self.assertIsInstance(orc._directives, AgentDirectives)
        self.assertEqual(orc._directives.spec, "")

    def test_custom_model_and_iterations(self):
        orc = self._make(model="custom:13b", max_iterations=5)
        self.assertEqual(orc._model, "custom:13b")
        self.assertEqual(orc._max_iterations, 5)

    def test_remote_url_stored(self):
        adapter = MagicMock(spec=BaseAIAdapter)
        orc = self.Orchestrator(adapter, "http://colab:9999")
        self.assertEqual(orc._remote_url, "http://colab:9999")

    def test_directives_stored(self):
        d = AgentDirectives(spec="use korean", inspection_plan="be thorough")
        orc = self._make(directives=d)
        self.assertEqual(orc._directives.spec, "use korean")
        self.assertEqual(orc._directives.inspection_plan, "be thorough")

    def test_sub_agents_created(self):
        from agents.spec_agent import SpecAgent
        from agents.image_analysis_agent import ImageAnalysisAgent
        from agents.depth_agent import DepthAgent
        from agents.material_agent import MaterialAgent
        from agents.roi_agent import ROIAgent
        from agents.pipeline_composer import PipelineComposer
        from agents.pipeline_selection import PipelineSelector
        from agents.algorithm_selector import AlgorithmSelector
        from agents.inspection_plan_agent import InspectionPlanAgent
        from agents.blueprint_agent import BlueprintAgent
        from agents.test_agent_inspection import TestAgentInspection
        from agents.test_agent_align import TestAgentAlign
        from agents.evaluation_agent import EvaluationAgent
        from agents.feedback_controller import FeedbackController
        from agents.decision_agent import DecisionAgent
        from agents.parameter_sheet import ParameterSheetGenerator

        orc = self._make()
        self.assertIsInstance(orc._spec_agent, SpecAgent)
        self.assertIsInstance(orc._image_analysis_agent, ImageAnalysisAgent)
        self.assertIsInstance(orc._depth_agent, DepthAgent)
        self.assertIsInstance(orc._material_agent, MaterialAgent)
        self.assertIsInstance(orc._roi_agent, ROIAgent)
        self.assertIsInstance(orc._pipeline_composer, PipelineComposer)
        self.assertIsInstance(orc._pipeline_selector, PipelineSelector)
        self.assertIsInstance(orc._algorithm_selector, AlgorithmSelector)
        self.assertIsInstance(orc._inspection_plan_agent, InspectionPlanAgent)
        self.assertIsInstance(orc._blueprint_agent, BlueprintAgent)
        self.assertIsInstance(orc._test_agent_inspection, TestAgentInspection)
        self.assertIsInstance(orc._test_agent_align, TestAgentAlign)
        self.assertIsInstance(orc._evaluation_agent, EvaluationAgent)
        self.assertIsInstance(orc._feedback_controller, FeedbackController)
        self.assertIsInstance(orc._decision_agent, DecisionAgent)
        self.assertIsInstance(orc._parameter_sheet_gen, ParameterSheetGenerator)

    def test_directives_routed_to_spec_agent(self):
        d = AgentDirectives(spec="strict mode")
        orc = self._make(directives=d)
        self.assertEqual(orc._spec_agent.directive, "strict mode")

    def test_directives_routed_to_image_analysis(self):
        d = AgentDirectives(image_analysis="focus on edges")
        orc = self._make(directives=d)
        self.assertEqual(orc._image_analysis_agent.directive, "focus on edges")

    def test_directives_routed_to_test_agents(self):
        d = AgentDirectives(test="lenient")
        orc = self._make(directives=d)
        self.assertEqual(orc._test_agent_inspection.directive, "lenient")
        self.assertEqual(orc._test_agent_align.directive, "lenient")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Input Validation
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorInputValidation(unittest.TestCase):
    def setUp(self):
        self.orc = _make_orchestrator()

    def _run(self, **kwargs):
        return asyncio.run(self.orc.run(**kwargs))

    def test_empty_user_text_returns_error(self):
        r = self._run(user_text="", images=[_img()])
        self.assertEqual(r.status, "error")
        self.assertIn("user_text", r.error_message)

    def test_empty_images_returns_error(self):
        r = self._run(user_text="inspect bolts", images=[])
        self.assertEqual(r.status, "error")
        self.assertIn("images", r.error_message)

    def test_invalid_min_accuracy_above_one(self):
        r = self._run(
            user_text="inspect", images=[_img()],
            success_criteria={"min_accuracy": 1.5},
        )
        self.assertEqual(r.status, "error")
        self.assertIn("min_accuracy", r.error_message)

    def test_invalid_min_accuracy_below_zero(self):
        r = self._run(
            user_text="inspect", images=[_img()],
            success_criteria={"min_accuracy": -0.1},
        )
        self.assertEqual(r.status, "error")
        self.assertIn("min_accuracy", r.error_message)

    def test_invalid_max_fp_rate_above_one(self):
        r = self._run(
            user_text="inspect", images=[_img()],
            success_criteria={"max_fp_rate": 1.2},
        )
        self.assertEqual(r.status, "error")
        self.assertIn("max_fp_rate", r.error_message)

    def test_valid_success_criteria_passes_validation(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        r = asyncio.run(orc.run(
            user_text="inspect bolts",
            images=[_img()],
            ng_images=[_img()],
            success_criteria={"min_accuracy": 0.85},
        ))
        self.assertEqual(r.status, "success")

    def test_missing_ng_images_in_inspection_mode(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        # ng_images=None, mode=inspection → error after SpecAgent
        r = asyncio.run(orc.run(
            user_text="inspect bolts",
            images=[_img()],
            ng_images=None,
        ))
        self.assertEqual(r.status, "error")
        self.assertIn("ng_images", r.error_message)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Happy Path — Inspection Mode
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorHappyPathInspection(unittest.TestCase):
    def setUp(self):
        self.orc = _make_orchestrator()
        _wire_happy_inspection(self.orc)
        self.result = asyncio.run(self.orc.run(
            user_text="inspect bolt holes",
            images=[_img()],
            ng_images=[_img()],
        ))

    def test_status_success(self):
        self.assertEqual(self.result.status, "success")

    def test_mode_in_data(self):
        self.assertEqual(self.result.data["mode"], "inspection")

    def test_spec_in_data(self):
        self.assertIn("spec", self.result.data)
        self.assertEqual(self.result.data["spec"]["mode"], "inspection")

    def test_scene_context_in_data(self):
        self.assertIn("scene_context", self.result.data)

    def test_pipeline_in_data(self):
        self.assertIn("pipeline", self.result.data)
        self.assertIsNotNone(self.result.data["pipeline"])

    def test_algorithm_category_in_data(self):
        self.assertEqual(self.result.data["algorithm_category"], "blob")

    def test_inspection_plan_in_data(self):
        self.assertIn("inspection_plan", self.result.data)
        self.assertIsNotNone(self.result.data["inspection_plan"])

    def test_blueprint_in_data(self):
        self.assertIn("blueprint", self.result.data)
        self.assertIsNotNone(self.result.data["blueprint"])

    def test_parameter_sheets_in_data(self):
        self.assertIn("parameter_sheets", self.result.data)
        self.assertIsInstance(self.result.data["parameter_sheets"], list)

    def test_test_result_in_data(self):
        self.assertIn("test_result", self.result.data)

    def test_evaluation_in_data(self):
        self.assertIn("evaluation", self.result.data)

    def test_iterations_used_is_one(self):
        self.assertEqual(self.result.data["iterations_used"], 1)

    def test_decision_not_in_data_on_first_pass(self):
        self.assertNotIn("decision", self.result.data)

    def test_all_agents_called_once(self):
        self.orc._spec_agent.run.assert_called_once()
        self.orc._image_analysis_agent.run.assert_called_once()
        self.orc._depth_agent.run.assert_called_once()
        self.orc._material_agent.run.assert_called_once()
        self.orc._roi_agent.run.assert_called_once()
        self.orc._pipeline_composer.run.assert_called_once()
        self.orc._pipeline_selector.run.assert_called_once()
        self.orc._algorithm_selector.run.assert_called_once()
        self.orc._inspection_plan_agent.run.assert_called_once()
        self.orc._blueprint_agent.run.assert_called_once()
        self.orc._test_agent_inspection.run.assert_called_once()
        self.orc._evaluation_agent.run.assert_called_once()
        self.orc._feedback_controller.run.assert_not_called()
        self.orc._decision_agent.run.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Happy Path — Align Mode
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorHappyPathAlign(unittest.TestCase):
    def setUp(self):
        self.orc = _make_orchestrator()
        _wire_happy_align(self.orc)
        self.result = asyncio.run(self.orc.run(
            user_text="align camera",
            images=[_img()],
            roi={"x1": 0, "y1": 0, "x2": 5, "y2": 5},
        ))

    def test_status_success(self):
        self.assertEqual(self.result.status, "success")

    def test_mode_is_align(self):
        self.assertEqual(self.result.data["mode"], "align")

    def test_no_ng_images_required(self):
        # no ng_images param → still succeeds
        self.assertEqual(self.result.status, "success")

    def test_inspection_plan_is_none(self):
        self.assertIsNone(self.result.data["inspection_plan"])

    def test_blueprint_is_none(self):
        self.assertIsNone(self.result.data["blueprint"])

    def test_test_agent_align_called(self):
        self.orc._test_agent_align.run.assert_called_once()

    def test_test_agent_inspection_not_called(self):
        self.orc._test_agent_inspection.run.assert_not_called()

    def test_inspection_plan_agent_not_called(self):
        self.orc._inspection_plan_agent.run.assert_not_called()

    def test_blueprint_agent_not_called(self):
        self.orc._blueprint_agent.run.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Agent Error Propagation
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorAgentErrors(unittest.TestCase):
    def _run_with_spec_error(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        orc._spec_agent.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="LLM timeout"))
        return asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))

    def test_spec_agent_error_propagated(self):
        r = self._run_with_spec_error()
        self.assertEqual(r.status, "error")
        self.assertIn("SpecAgent", r.error_message)

    def test_pipeline_composer_error_propagated(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        orc._pipeline_composer.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="no blocks found"))
        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "error")
        self.assertIn("PipelineComposer", r.error_message)

    def test_pipeline_selector_error_propagated(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        orc._pipeline_selector.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="all pipelines failed"))
        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "error")
        self.assertIn("PipelineSelector", r.error_message)

    def test_inspection_plan_agent_error_propagated(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        orc._inspection_plan_agent.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="empty plan"))
        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "error")
        self.assertIn("InspectionPlanAgent", r.error_message)

    def test_algorithm_selector_error_propagated(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        orc._algorithm_selector.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="no scene context"))
        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "error")
        self.assertIn("AlgorithmSelector", r.error_message)

    def test_blueprint_agent_error_propagated(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        orc._blueprint_agent.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="no pipeline blocks"))
        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "error")
        self.assertIn("BlueprintAgent", r.error_message)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Retry Loop Mechanics
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorRetryMechanics(unittest.TestCase):
    def test_retry_increments_iterations_used(self):
        """Two iterations needed when first fails."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed("pipeline_bad_fit"),
            _eval_passed(),
        ])
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result("pipeline_bad_fit"))

        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "success")
        self.assertEqual(r.data["iterations_used"], 2)

    def test_feedback_controller_called_on_failure(self):
        orc = _make_orchestrator(max_iterations=3)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed("pipeline_bad_fit"),
            _eval_passed(),
        ])
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result("pipeline_bad_fit"))

        asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        orc._feedback_controller.run.assert_called_once()

    def test_no_feedback_when_first_pass(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        orc._feedback_controller.run.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Retry Paths — one test per failure_reason
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorRetryPaths(unittest.TestCase):
    def _two_iter_test(self, failure_reason: str):
        """Run two iterations: first fails with given reason, second passes."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed(failure_reason),
            _eval_passed(),
        ])
        strategy_map = {
            "pipeline_bad_fit": "replace_pipeline",
            "pipeline_bad_params": "retry_params",
            "algorithm_wrong_category": "change_category",
            "runtime_error": "retry_pipeline",
            "inspection_plan_issue": "revise_plan",
            "spec_issue": "relax_spec",
        }
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result(failure_reason, strategy_map.get(failure_reason, "replace_pipeline")))
        return orc, asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))

    def test_pipeline_bad_fit_retries_compose(self):
        """pipeline_bad_fit → PipelineComposer called twice."""
        orc, r = self._two_iter_test("pipeline_bad_fit")
        self.assertEqual(r.status, "success")
        self.assertEqual(orc._pipeline_composer.run.call_count, 2)
        self.assertEqual(orc._pipeline_selector.run.call_count, 2)

    def test_pipeline_bad_params_retries_select(self):
        """pipeline_bad_params → PipelineSelector called twice, Composer once."""
        orc, r = self._two_iter_test("pipeline_bad_params")
        self.assertEqual(r.status, "success")
        self.assertEqual(orc._pipeline_composer.run.call_count, 1)
        self.assertEqual(orc._pipeline_selector.run.call_count, 2)

    def test_algorithm_wrong_category_retries_compose(self):
        """algorithm_wrong_category → PipelineComposer called twice."""
        orc, r = self._two_iter_test("algorithm_wrong_category")
        self.assertEqual(r.status, "success")
        self.assertEqual(orc._pipeline_composer.run.call_count, 2)

    def test_runtime_error_retries_select(self):
        """runtime_error → PipelineSelector called twice, Composer once."""
        orc, r = self._two_iter_test("runtime_error")
        self.assertEqual(r.status, "success")
        self.assertEqual(orc._pipeline_composer.run.call_count, 1)
        self.assertEqual(orc._pipeline_selector.run.call_count, 2)

    def test_inspection_plan_issue_retries_plan(self):
        """inspection_plan_issue → InspectionPlanAgent called twice, Composer/Selector once."""
        orc, r = self._two_iter_test("inspection_plan_issue")
        self.assertEqual(r.status, "success")
        self.assertEqual(orc._pipeline_composer.run.call_count, 1)
        self.assertEqual(orc._pipeline_selector.run.call_count, 1)
        self.assertEqual(orc._inspection_plan_agent.run.call_count, 2)

    def test_spec_issue_relaxes_criteria_and_retries_compose(self):
        """spec_issue → PipelineComposer called twice (criteria relaxed)."""
        orc, r = self._two_iter_test("spec_issue")
        self.assertEqual(r.status, "success")
        self.assertEqual(orc._pipeline_composer.run.call_count, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Max Iterations → DecisionAgent
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorMaxIterations(unittest.TestCase):
    def test_decision_agent_called_when_max_exceeded(self):
        orc = _make_orchestrator(max_iterations=2)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(return_value=_eval_failed("pipeline_bad_fit"))
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result("pipeline_bad_fit"))

        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))

        orc._decision_agent.run.assert_called_once()
        self.assertIn("decision", r.data)

    def test_result_still_success_when_decision_made(self):
        orc = _make_orchestrator(max_iterations=1)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(return_value=_eval_failed("pipeline_bad_fit"))
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result("pipeline_bad_fit"))

        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.status, "success")

    def test_decision_data_included_in_result(self):
        orc = _make_orchestrator(max_iterations=1)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(return_value=_eval_failed("pipeline_bad_fit"))
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result("pipeline_bad_fit"))

        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertIn("verdict", r.data["decision"])

    def test_decision_agent_not_called_when_passes_before_max(self):
        orc = _make_orchestrator(max_iterations=3)
        _wire_happy_inspection(orc)
        asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        orc._decision_agent.run.assert_not_called()

    def test_iterations_used_equals_max_on_exhaustion(self):
        orc = _make_orchestrator(max_iterations=2)
        _wire_happy_inspection(orc)
        orc._evaluation_agent.run = AsyncMock(return_value=_eval_failed("pipeline_bad_fit"))
        orc._feedback_controller.run = AsyncMock(
            return_value=_feedback_result("pipeline_bad_fit"))

        r = asyncio.run(orc.run(user_text="test", images=[_img()], ng_images=[_img()]))
        self.assertEqual(r.data["iterations_used"], 2)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Directive Routing
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorDirectiveRouting(unittest.TestCase):
    def test_spec_directive_passed_to_spec_agent(self):
        d = AgentDirectives(spec="use strict criteria")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._spec_agent.directive, "use strict criteria")

    def test_image_analysis_directive_passed(self):
        d = AgentDirectives(image_analysis="focus on surface")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._image_analysis_agent.directive, "focus on surface")

    def test_depth_directive_passed(self):
        d = AgentDirectives(depth="high resolution")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._depth_agent.directive, "high resolution")

    def test_material_directive_passed(self):
        d = AgentDirectives(material="metal surfaces only")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._material_agent.directive, "metal surfaces only")

    def test_pipeline_composer_directive_passed(self):
        d = AgentDirectives(pipeline_composer="force clahe")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._pipeline_composer.directive, "force clahe")

    def test_vision_judge_directive_passed(self):
        d = AgentDirectives(vision_judge="strict scoring")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._vision_judge.directive, "strict scoring")

    def test_inspection_plan_directive_passed(self):
        d = AgentDirectives(inspection_plan="detailed plan")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._inspection_plan_agent.directive, "detailed plan")

    def test_test_directive_passed_to_both_test_agents(self):
        d = AgentDirectives(test="strict")
        orc = _make_orchestrator(directives=d)
        self.assertEqual(orc._test_agent_inspection.directive, "strict")
        self.assertEqual(orc._test_agent_align.directive, "strict")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Success Criteria Override
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorSuccessCriteria(unittest.TestCase):
    def test_user_criteria_override_spec_criteria(self):
        """User-provided success_criteria are used even if SpecAgent returns different ones."""
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        # SpecAgent returns min_accuracy=0.9, user passes 0.85
        user_criteria = {"min_accuracy": 0.85}

        eval_called_with = []

        async def capture_eval(**kwargs):
            eval_called_with.append(kwargs.get("success_criteria"))
            return _eval_passed()

        orc._evaluation_agent.run = AsyncMock(side_effect=capture_eval)

        asyncio.run(orc.run(
            user_text="inspect",
            images=[_img()],
            ng_images=[_img()],
            success_criteria=user_criteria,
        ))
        # The evaluation agent should have been called
        self.assertTrue(len(eval_called_with) > 0)

    def test_spec_criteria_used_when_no_user_override(self):
        """SpecAgent success_criteria used when user does not provide any."""
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        # SpecAgent returns {"min_accuracy": 0.9}
        r = asyncio.run(orc.run(
            user_text="inspect",
            images=[_img()],
            ng_images=[_img()],
        ))
        self.assertEqual(r.status, "success")


# ─────────────────────────────────────────────────────────────────────────────
# 11. Edge Cases
# ─────────────────────────────────────────────────────────────────────────────

class TestOrchestratorEdgeCases(unittest.TestCase):
    def test_multiple_images_ok(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        r = asyncio.run(orc.run(
            user_text="inspect",
            images=[_img(), _img(), _img()],
            ng_images=[_img(), _img()],
        ))
        self.assertEqual(r.status, "success")

    def test_roi_passed_to_agents(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        roi = {"x1": 10, "y1": 10, "x2": 50, "y2": 50}
        asyncio.run(orc.run(
            user_text="inspect",
            images=[_img(100, 100)],
            ng_images=[_img(100, 100)],
            roi=roi,
        ))
        call_kwargs = orc._spec_agent.run.call_args.kwargs
        self.assertEqual(call_kwargs.get("roi"), roi)

    def test_text_query_passed_to_roi_agent(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        asyncio.run(orc.run(
            user_text="inspect",
            images=[_img()],
            ng_images=[_img()],
            text_query="find the bolt",
        ))
        call_kwargs = orc._roi_agent.run.call_args.kwargs
        self.assertEqual(call_kwargs.get("text_query"), "find the bolt")

    def test_align_mode_with_ng_images_ignored(self):
        """In align mode, ng_images can be provided but are not required."""
        orc = _make_orchestrator()
        _wire_happy_align(orc)
        r = asyncio.run(orc.run(
            user_text="align",
            images=[_img()],
            ng_images=[_img()],  # provided but mode is align
            roi={"x1": 0, "y1": 0, "x2": 5, "y2": 5},
        ))
        self.assertEqual(r.status, "success")

    def test_execution_time_recorded(self):
        orc = _make_orchestrator()
        _wire_happy_inspection(orc)
        r = asyncio.run(orc.run(
            user_text="inspect",
            images=[_img()],
            ng_images=[_img()],
        ))
        self.assertGreaterEqual(r.execution_time_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
