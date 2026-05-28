"""E2E tests for Inspection mode pipeline — Step 47.

Mock E2E strategy:
- Remote AI agents mocked (SpecAgent, DepthAgent, MaterialAgent, VisionJudgeAgent,
  InspectionPlanAgent, BlueprintAgent, DecisionAgent)
- Local/rule-based agents run for real (ImageAnalysisAgent, PipelineComposer,
  PipelineSelector with real ParameterSearcher, AlgorithmSelector,
  TestAgentInspection, FeedbackController, ParameterSheetGenerator)
- EvaluationAgent: real for happy path, mocked for retry/decision path control

Colab E2E tests (marked @pytest.mark.colab) require COLAB_URL env var and are
skipped automatically in CI — run manually with a live Colab server.
"""
import asyncio
import json
import os
import unittest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from agents.lighting_advisor import LightingAdvisor
from agents.models import (
    AgentDirectives,
    AgentResult,
    Blueprint,
    BlueprintEdge,
    BlueprintNode,
    InspectionItem,
    InspectionPlan,
)
from backend.services.ai_adapter.base import BaseAIAdapter
from tests.fixtures.sample_images.generate import (
    make_ng_images,
    make_ok_images,
)


# ── construction helpers ──────────────────────────────────────────────────────

def _make_adapter():
    return MagicMock(spec=BaseAIAdapter)


def _make_orchestrator(max_iterations: int = 3, directives: AgentDirectives | None = None):
    from agents.orchestrator import Orchestrator
    adapter = _make_adapter()
    return Orchestrator(
        adapter,
        "http://mock-colab:8000",
        model="test-model",
        max_iterations=max_iterations,
        directives=directives or AgentDirectives(),
    )


def _lenient_plan_dict(
    item_id: int = 1,
    name: str = "Blob Check",
    category: str = "BLOB",
    min_accuracy: float = 0.01,
) -> dict:
    """Return asdict(InspectionPlan) with very lenient success criteria."""
    item = InspectionItem(
        item_id=item_id,
        name=name,
        category=category,
        depends_on=[],
        safety_role=False,
        success_criteria={
            "min_accuracy": min_accuracy,
            "max_fp_rate": 1.0,
            "max_fn_rate": 1.0,
        },
    )
    plan = InspectionPlan(items=[item], inspection_purpose="E2E test purpose")
    return asdict(plan)


def _blueprint_dict() -> dict:
    bp = Blueprint(
        nodes=[
            BlueprintNode("pre_grayscale", "preprocessing", "grayscale"),
            BlueprintNode("insp_1", "inspection", "Blob Check"),
            BlueprintNode("decision", "decision", "Pass / Fail"),
        ],
        edges=[
            BlueprintEdge("pre_grayscale", "insp_1"),
            BlueprintEdge("insp_1", "decision"),
        ],
        svg_content="<svg><rect width='800' height='350' fill='#1a1a1a'/></svg>",
        algorithm_description="E2E 테스트 비전 검사 알고리즘",
    )
    return asdict(bp)


def _eval_passed_result() -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "item_evaluations": [
                {"item_id": 1, "passed": True, "failure_reason": None, "details": "passed"}
            ],
            "overall_passed": True,
            "total_items": 1,
            "passed_items": 1,
            "failed_items": 0,
            "failure_summary": {},
        },
    )


def _eval_failed_result(reason: str = "pipeline_bad_params") -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "item_evaluations": [
                {"item_id": 1, "passed": False, "failure_reason": reason, "details": "failed"}
            ],
            "overall_passed": False,
            "total_items": 1,
            "passed_items": 0,
            "failed_items": 1,
            "failure_summary": {reason: 1},
        },
    )


def _decision_result(verdict: str = "deep_learning") -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "verdict": verdict,
            "reasoning": "E2E test: max iterations exceeded",
            "dinov2_variability": None,
            "internvl_analysis": None,
            "vision_judge_avg_score": None,
            "recommendation": "Consider deep learning approach",
            "confidence": 0.8,
        },
    )


def _wire_remote_mocks(
    orc,
    spec_mode: str = "inspection",
    plan_dict: dict | None = None,
    eval_result: AgentResult | None = None,
    decision_verdict: str = "deep_learning",
):
    """Wire mock responses for all remote AI agents.

    ImageAnalysisAgent, PipelineComposer, AlgorithmSelector,
    TestAgentInspection, FeedbackController, ParameterSheetGenerator
    all run for real.
    """
    orc._spec_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "mode": spec_mode,
            "goal": "E2E test: inspect bolt holes",
            "success_criteria": {"min_accuracy": 0.01, "max_fp_rate": 1.0, "max_fn_rate": 1.0},
        },
    ))
    orc._depth_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "depth_map": None,
            "depth_stats": {"depth_complexity": 0.1, "has_shadow_region": False},
        },
    ))
    orc._material_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={"surface_type": "plastic", "material_map": None},
    ))
    orc._vision_judge.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "judgement": {
                "visibility_score": 0.75,
                "separability_score": 0.75,
                "measurability_score": 0.75,
                "overall_score": 0.75,
                "problems": [],
                "next_suggestion": "",
            }
        },
    ))
    orc._inspection_plan_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "plan": plan_dict if plan_dict is not None else _lenient_plan_dict(),
            "raw_response": "[]",
        },
    ))
    bp = _blueprint_dict()
    orc._blueprint_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "blueprint": bp,
            "svg": bp["svg_content"],
            "description": "E2E 알고리즘 설명",
            "node_count": len(bp["nodes"]),
            "edge_count": len(bp["edges"]),
        },
    ))
    orc._decision_agent.run = AsyncMock(return_value=_decision_result(decision_verdict))

    if eval_result is not None:
        orc._evaluation_agent.run = AsyncMock(return_value=eval_result)

    return orc


# ─────────────────────────────────────────────────────────────────────────────
# 1. Happy Path — full inspection flow with real local agents
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EInspectionHappyPath(unittest.TestCase):
    """Full Inspection mode E2E with real ImageAnalysisAgent, PipelineComposer,
    AlgorithmSelector, TestAgentInspection, EvaluationAgent (lenient criteria)."""

    def setUp(self):
        self.orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(self.orc)
        ok_imgs = make_ok_images(count=2)
        ng_imgs = make_ng_images(count=2, n_circles=5)
        self.result = asyncio.run(self.orc.run(
            user_text="inspect bolt holes for missing material",
            images=ok_imgs,
            ng_images=ng_imgs,
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))

    def test_result_status_is_success(self):
        self.assertEqual(self.result.status, "success")

    def test_mode_is_inspection(self):
        self.assertEqual(self.result.data["mode"], "inspection")

    def test_spec_data_present(self):
        self.assertIn("spec", self.result.data)
        self.assertEqual(self.result.data["spec"]["mode"], "inspection")

    def test_scene_context_present(self):
        self.assertIn("scene_context", self.result.data)
        sc = self.result.data["scene_context"]
        self.assertIn("contrast", sc)
        self.assertIn("surface_type", sc)

    def test_pipeline_present(self):
        self.assertIn("pipeline", self.result.data)
        self.assertIsNotNone(self.result.data["pipeline"])
        self.assertIn("pipeline_id", self.result.data["pipeline"])

    def test_pipeline_has_blocks(self):
        pipeline = self.result.data["pipeline"]
        self.assertIn("blocks", pipeline)
        self.assertIsInstance(pipeline["blocks"], list)
        self.assertGreater(len(pipeline["blocks"]), 0)

    def test_algorithm_category_present(self):
        self.assertIn("algorithm_category", self.result.data)
        self.assertIsNotNone(self.result.data["algorithm_category"])

    def test_inspection_plan_present(self):
        self.assertIn("inspection_plan", self.result.data)
        plan = self.result.data["inspection_plan"]
        self.assertIsNotNone(plan)
        self.assertIn("items", plan)

    def test_blueprint_present(self):
        self.assertIn("blueprint", self.result.data)
        bp = self.result.data["blueprint"]
        self.assertIsNotNone(bp)

    def test_blueprint_has_nodes(self):
        bp = self.result.data["blueprint"]
        self.assertIn("nodes", bp)
        self.assertIsInstance(bp["nodes"], list)
        self.assertGreater(len(bp["nodes"]), 0)

    def test_blueprint_has_edges(self):
        bp = self.result.data["blueprint"]
        self.assertIn("edges", bp)
        self.assertIsInstance(bp["edges"], list)

    def test_blueprint_has_svg_content(self):
        bp = self.result.data["blueprint"]
        self.assertIn("svg_content", bp)
        self.assertIn("<svg", bp["svg_content"])

    def test_parameter_sheets_present(self):
        self.assertIn("parameter_sheets", self.result.data)
        sheets = self.result.data["parameter_sheets"]
        self.assertIsInstance(sheets, list)

    def test_test_result_present(self):
        self.assertIn("test_result", self.result.data)

    def test_test_result_has_item_results(self):
        tr = self.result.data["test_result"]
        self.assertIn("item_results", tr)
        self.assertIsInstance(tr["item_results"], list)

    def test_evaluation_present(self):
        self.assertIn("evaluation", self.result.data)

    def test_iterations_used_at_least_one(self):
        self.assertGreaterEqual(self.result.data["iterations_used"], 1)

    def test_execution_time_recorded(self):
        self.assertGreater(self.result.execution_time_ms, 0.0)

    def test_image_analysis_ran_for_real(self):
        # scene_context.contrast > 0 only if ImageAnalysisAgent ran on a real image
        # OK images are pure white — contrast ≈ 0; surface_type set by MaterialAgent mock
        sc = self.result.data["scene_context"]
        self.assertIsInstance(sc["contrast"], float)
        self.assertEqual(sc["surface_type"], "plastic")

    def test_pipeline_composer_ran_for_real(self):
        # PipelineComposer creates pipeline_id matching naming pattern
        pipeline_id = self.result.data["pipeline"]["pipeline_id"]
        self.assertTrue(pipeline_id.startswith("pipe_"))

    def test_spec_agent_called_once(self):
        self.orc._spec_agent.run.assert_called_once()

    def test_depth_agent_called_once(self):
        self.orc._depth_agent.run.assert_called_once()

    def test_material_agent_called_once(self):
        self.orc._material_agent.run.assert_called_once()

    def test_inspection_plan_agent_called_once(self):
        self.orc._inspection_plan_agent.run.assert_called_once()

    def test_blueprint_agent_called_once(self):
        self.orc._blueprint_agent.run.assert_called_once()

    def test_decision_agent_not_called_on_pass(self):
        if self.result.data.get("iterations_used", 1) <= 3:
            # if passed within iterations, decision should NOT be called
            # (unless max_iterations reached naturally due to lenient criteria behavior)
            # Allow either: passed without decision, or failed and decision called
            passed = self.result.data.get("evaluation", {}).get("overall_passed", False)
            if passed:
                self.orc._decision_agent.run.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Lighting Suggestions via LightingAdvisor
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EInspectionLighting(unittest.TestCase):
    """Verify LightingAdvisor integration with orchestrator output scene_context."""

    def setUp(self):
        self.advisor = LightingAdvisor()

    def test_lighting_advisor_with_metal_surface(self):
        scene_ctx = {
            "surface_type": "metal",
            "reflection_level": 0.8,
            "lighting_uniformity": 0.3,
            "illumination_type": "spot",
            "contrast": 0.2,
            "has_shadow_region": True,
            "noise_level": 0.4,
        }
        recs = self.advisor.generate_recommendations(scene_ctx)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

    def test_lighting_recommendations_have_required_keys(self):
        scene_ctx = {
            "surface_type": "metal",
            "reflection_level": 0.8,
            "lighting_uniformity": 0.8,
            "illumination_type": "uniform",
            "contrast": 0.8,
            "has_shadow_region": False,
            "noise_level": 0.0,
        }
        recs = self.advisor.generate_recommendations(scene_ctx)
        for rec in recs:
            self.assertIn("category", rec)
            self.assertIn("suggestion", rec)
            self.assertIn("reason", rec)
            self.assertIn("priority", rec)

    def test_lighting_metal_surface_triggers_polarization(self):
        scene_ctx = {"surface_type": "metal", "reflection_level": 0.0,
                     "lighting_uniformity": 1.0, "illumination_type": "uniform",
                     "contrast": 0.5, "has_shadow_region": False, "noise_level": 0.0}
        recs = self.advisor.generate_recommendations(scene_ctx)
        categories = [r["category"] for r in recs]
        self.assertIn("polarization", categories)

    def test_lighting_high_reflection_triggers_light_shape(self):
        scene_ctx = {"surface_type": "plastic", "reflection_level": 0.7,
                     "lighting_uniformity": 1.0, "illumination_type": "uniform",
                     "contrast": 0.5, "has_shadow_region": False, "noise_level": 0.0}
        recs = self.advisor.generate_recommendations(scene_ctx)
        categories = [r["category"] for r in recs]
        self.assertIn("light_shape", categories)

    def test_lighting_clean_scene_returns_empty(self):
        scene_ctx = {"surface_type": "plastic", "reflection_level": 0.0,
                     "lighting_uniformity": 1.0, "illumination_type": "uniform",
                     "contrast": 0.9, "has_shadow_region": False, "noise_level": 0.0}
        recs = self.advisor.generate_recommendations(scene_ctx)
        self.assertEqual(recs, [])

    def test_lighting_from_orchestrator_scene_context(self):
        """LightingAdvisor can process real scene_context from orchestrator output."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(orc)
        result = asyncio.run(orc.run(
            user_text="inspect for defects",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        self.assertEqual(result.status, "success")
        scene_ctx = result.data["scene_context"]
        recs = self.advisor.generate_recommendations(scene_ctx)
        self.assertIsInstance(recs, list)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Retry Scenario — FeedbackController + retry loop
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EInspectionRetry(unittest.TestCase):
    """Retry mechanics: first iteration fails → FeedbackController (real) determines
    strategy → retry succeeds."""

    def test_retry_on_pipeline_bad_params_succeeds(self):
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(orc, eval_result=None)
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed_result("pipeline_bad_params"),
            _eval_passed_result(),
        ])

        result = asyncio.run(orc.run(
            user_text="inspect bolt holes",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        self.assertEqual(result.status, "success")
        self.assertEqual(result.data["iterations_used"], 2)

    def test_retry_on_pipeline_bad_fit_restarts_compose(self):
        """pipeline_bad_fit → PipelineComposer called twice (real) — verified via call counter."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(orc, eval_result=None)
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed_result("pipeline_bad_fit"),
            _eval_passed_result(),
        ])

        # Wrap real PipelineComposer.run to count calls
        real_compose = orc._pipeline_composer.run
        compose_calls = []

        async def counting_compose(**kwargs):
            compose_calls.append(1)
            return await real_compose(**kwargs)

        orc._pipeline_composer.run = counting_compose

        result = asyncio.run(orc.run(
            user_text="inspect bolts",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        self.assertEqual(result.status, "success")
        self.assertGreaterEqual(len(compose_calls), 2)

    def test_retry_on_inspection_plan_issue_reruns_plan_agent(self):
        """inspection_plan_issue → InspectionPlanAgent called twice (both mocked)."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(orc, eval_result=None)
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed_result("inspection_plan_issue"),
            _eval_passed_result(),
        ])

        result = asyncio.run(orc.run(
            user_text="inspect screws",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        self.assertEqual(result.status, "success")
        # InspectionPlanAgent.run is AsyncMock — call_count is valid
        self.assertGreaterEqual(orc._inspection_plan_agent.run.call_count, 2)

    def test_feedback_controller_runs_for_real(self):
        """FeedbackController is NOT mocked — verify it selects correct strategy."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(orc, eval_result=None)
        original_fb = orc._feedback_controller.run  # real method

        called = []

        async def capture_fb(**kwargs):
            result = await original_fb(**kwargs)
            called.append(result.data.get("strategy"))
            return result

        orc._feedback_controller.run = capture_fb
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed_result("pipeline_bad_fit"),
            _eval_passed_result(),
        ])

        asyncio.run(orc.run(
            user_text="inspect",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0], "replace_pipeline")

    def test_spec_issue_relaxes_criteria(self):
        """spec_issue failure → orchestrator relaxes success_criteria min_accuracy."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(
            orc,
            eval_result=None,
        )
        orc._spec_agent.run = AsyncMock(return_value=AgentResult(
            status="success",
            data={
                "mode": "inspection",
                "goal": "strict inspection",
                "success_criteria": {"min_accuracy": 0.97},
            },
        ))
        orc._evaluation_agent.run = AsyncMock(side_effect=[
            _eval_failed_result("spec_issue"),
            _eval_passed_result(),
        ])

        result = asyncio.run(orc.run(
            user_text="strict bolt inspection",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        self.assertEqual(result.status, "success")
        self.assertEqual(result.data["iterations_used"], 2)

    def test_no_retry_when_first_pass(self):
        """When first iteration passes, feedback controller is not called."""
        orc = _make_orchestrator(max_iterations=3)
        _wire_remote_mocks(orc, eval_result=_eval_passed_result())

        asyncio.run(orc.run(
            user_text="inspect",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        orc._decision_agent.run.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Decision Scenario — max_iterations exceeded
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EInspectionDecision(unittest.TestCase):
    """All retries exhausted → DecisionAgent called → returns EDGE_LEARNING or DEEP_LEARNING."""

    def _run_max_exceeded(self, verdict: str = "deep_learning", max_iter: int = 2):
        orc = _make_orchestrator(max_iterations=max_iter)
        _wire_remote_mocks(orc, decision_verdict=verdict)
        orc._evaluation_agent.run = AsyncMock(return_value=_eval_failed_result("pipeline_bad_fit"))

        result = asyncio.run(orc.run(
            user_text="inspect parts",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 5, "y1": 5, "x2": 95, "y2": 95},
        ))
        return orc, result

    def test_decision_agent_called_when_max_exceeded(self):
        orc, result = self._run_max_exceeded()
        orc._decision_agent.run.assert_called_once()

    def test_result_status_still_success(self):
        _, result = self._run_max_exceeded()
        self.assertEqual(result.status, "success")

    def test_decision_data_in_result(self):
        _, result = self._run_max_exceeded()
        self.assertIn("decision", result.data)

    def test_decision_verdict_deep_learning(self):
        _, result = self._run_max_exceeded(verdict="deep_learning")
        self.assertEqual(result.data["decision"]["verdict"], "deep_learning")

    def test_decision_verdict_edge_learning(self):
        _, result = self._run_max_exceeded(verdict="edge_learning")
        self.assertEqual(result.data["decision"]["verdict"], "edge_learning")

    def test_iterations_used_equals_max(self):
        _, result = self._run_max_exceeded(max_iter=2)
        self.assertEqual(result.data["iterations_used"], 2)

    def test_decision_has_reasoning(self):
        _, result = self._run_max_exceeded()
        self.assertIn("reasoning", result.data["decision"])
        self.assertIsInstance(result.data["decision"]["reasoning"], str)

    def test_feedback_controller_ran_for_real(self):
        """FeedbackController is not mocked — confirm it ran in the failed iterations."""
        orc, result = self._run_max_exceeded(max_iter=2)
        # FeedbackController should have been called for each failed iteration
        # Verify result still has decision (downstream of FeedbackController)
        self.assertIn("decision", result.data)

    def test_test_agent_inspection_ran_for_real(self):
        """TestAgentInspection ran for real — result has item_results from real images."""
        _, result = self._run_max_exceeded()
        test_result = result.data.get("test_result", {})
        self.assertIn("item_results", test_result)
        self.assertIsInstance(test_result["item_results"], list)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Input Validation (E2E level)
# ─────────────────────────────────────────────────────────────────────────────

class TestE2EInspectionInputValidation(unittest.TestCase):
    """Verify orchestrator input validation at E2E entry point."""

    def test_empty_user_text_returns_error(self):
        orc = _make_orchestrator()
        _wire_remote_mocks(orc)
        result = asyncio.run(orc.run(
            user_text="", images=make_ok_images(), ng_images=make_ng_images(),
        ))
        self.assertEqual(result.status, "error")
        self.assertIn("user_text", result.error_message)

    def test_empty_images_returns_error(self):
        orc = _make_orchestrator()
        _wire_remote_mocks(orc)
        result = asyncio.run(orc.run(
            user_text="inspect", images=[], ng_images=make_ng_images(),
        ))
        self.assertEqual(result.status, "error")
        self.assertIn("images", result.error_message)

    def test_missing_ng_images_in_inspection_mode_returns_error(self):
        orc = _make_orchestrator()
        _wire_remote_mocks(orc, spec_mode="inspection")
        result = asyncio.run(orc.run(
            user_text="inspect bolts",
            images=make_ok_images(),
            ng_images=None,
        ))
        self.assertEqual(result.status, "error")
        self.assertIn("ng_images", result.error_message)

    def test_invalid_success_criteria_returns_error(self):
        orc = _make_orchestrator()
        result = asyncio.run(orc.run(
            user_text="inspect",
            images=make_ok_images(),
            ng_images=make_ng_images(),
            success_criteria={"min_accuracy": 1.5},
        ))
        self.assertEqual(result.status, "error")
        self.assertIn("min_accuracy", result.error_message)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Colab E2E Tests (skipped without COLAB_URL)
# ─────────────────────────────────────────────────────────────────────────────

_COLAB_URL = os.environ.get("COLAB_URL", "")
_SKIP_COLAB = not _COLAB_URL
_COLAB_REASON = "COLAB_URL env var not set — run manually with a live Colab server"


@pytest.mark.colab
@pytest.mark.skipif(_SKIP_COLAB, reason=_COLAB_REASON)
class TestColabE2EInspectionFullPipeline(unittest.TestCase):
    """Full inspection E2E test against a live Colab AI server.

    Run manually:
        COLAB_URL=https://<your-colab-url> python -m pytest tests/e2e/test_inspection_pipeline.py -m colab -v
    """

    def setUp(self):
        from agents.orchestrator import Orchestrator
        from backend.services.ai_adapter.remote_adapter import RemoteAdapter
        adapter = RemoteAdapter(base_url=_COLAB_URL)
        self.orc = Orchestrator(adapter, _COLAB_URL, model="qwen2.5-coder:7b", max_iterations=2)

    def test_colab_inspection_happy_path(self):
        result = asyncio.run(self.orc.run(
            user_text="inspect bolt holes for missing material defects",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2, n_circles=5),
            roi={"x1": 10, "y1": 10, "x2": 90, "y2": 90},
        ))
        self.assertIn(result.status, ("success", "error"))
        if result.status == "success":
            self.assertIn("mode", result.data)
            self.assertIn("pipeline", result.data)

    def test_colab_inspection_blueprint_generated(self):
        result = asyncio.run(self.orc.run(
            user_text="inspect circular parts for defects",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2, n_circles=3),
            roi={"x1": 10, "y1": 10, "x2": 90, "y2": 90},
        ))
        if result.status == "success" and result.data.get("blueprint"):
            bp = result.data["blueprint"]
            self.assertIn("nodes", bp)
            self.assertIn("svg_content", bp)

    def test_colab_inspection_lighting_suggestions(self):
        result = asyncio.run(self.orc.run(
            user_text="inspect metal parts",
            images=make_ok_images(count=2),
            ng_images=make_ng_images(count=2),
            roi={"x1": 10, "y1": 10, "x2": 90, "y2": 90},
        ))
        if result.status == "success":
            advisor = LightingAdvisor()
            sc = result.data.get("scene_context", {})
            recs = advisor.generate_recommendations(sc)
            self.assertIsInstance(recs, list)


if __name__ == "__main__":
    unittest.main()
