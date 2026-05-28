"""E2E tests for directive propagation and influence — Step 47.

Verifies:
1. AgentDirectives reach the correct agents at construction time
2. Directives influence runtime behavior (strict/lenient thresholds, clahe forcing)
3. Empty directives produce default agent self-judgment behavior
4. Directives flow correctly end-to-end through the orchestrator run()

All local agents run for real; remote AI agents are mocked.
"""
import asyncio
import unittest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

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
from tests.fixtures.sample_images.generate import make_ng_images, make_ok_images


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_adapter():
    return MagicMock(spec=BaseAIAdapter)


def _make_orchestrator(
    max_iterations: int = 3,
    directives: AgentDirectives | None = None,
):
    from agents.orchestrator import Orchestrator
    return Orchestrator(
        _make_adapter(),
        "http://mock-colab:8000",
        model="test-model",
        max_iterations=max_iterations,
        directives=directives or AgentDirectives(),
    )


def _lenient_plan_dict(min_accuracy: float = 0.01) -> dict:
    item = InspectionItem(
        item_id=1, name="Blob Check", category="BLOB",
        depends_on=[], safety_role=False,
        success_criteria={"min_accuracy": min_accuracy, "max_fp_rate": 1.0, "max_fn_rate": 1.0},
    )
    plan = InspectionPlan(items=[item], inspection_purpose="directive test")
    return asdict(plan)


def _blueprint_dict() -> dict:
    bp = Blueprint(
        nodes=[
            BlueprintNode("pre_gs", "preprocessing", "grayscale"),
            BlueprintNode("insp_1", "inspection", "Blob Check"),
            BlueprintNode("dec", "decision", "Pass / Fail"),
        ],
        edges=[
            BlueprintEdge("pre_gs", "insp_1"),
            BlueprintEdge("insp_1", "dec"),
        ],
        svg_content="<svg/>",
        algorithm_description="directive test algorithm",
    )
    return asdict(bp)


def _wire_mocks(
    orc,
    spec_mode: str = "inspection",
    eval_result: AgentResult | None = None,
    plan_min_accuracy: float = 0.01,
):
    orc._spec_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "mode": spec_mode,
            "goal": "directive e2e test",
            "success_criteria": {"min_accuracy": 0.01, "max_fp_rate": 1.0, "max_fn_rate": 1.0},
        },
    ))
    orc._depth_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={"depth_map": None, "depth_stats": {"depth_complexity": 0.0, "has_shadow_region": False}},
    ))
    orc._material_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={"surface_type": "plastic", "material_map": None},
    ))
    orc._vision_judge.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "judgement": {
                "visibility_score": 0.8, "separability_score": 0.8,
                "measurability_score": 0.8, "overall_score": 0.8,
                "problems": [], "next_suggestion": "",
            }
        },
    ))
    orc._inspection_plan_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={"plan": _lenient_plan_dict(plan_min_accuracy), "raw_response": "[]"},
    ))
    bp = _blueprint_dict()
    orc._blueprint_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "blueprint": bp,
            "svg": bp["svg_content"],
            "description": "directive test",
            "node_count": len(bp["nodes"]),
            "edge_count": len(bp["edges"]),
        },
    ))
    orc._decision_agent.run = AsyncMock(return_value=AgentResult(
        status="success",
        data={
            "verdict": "deep_learning",
            "reasoning": "directive test: max iterations",
            "dinov2_variability": None,
            "internvl_analysis": None,
            "vision_judge_avg_score": None,
            "recommendation": "deep learning",
            "confidence": 0.8,
        },
    ))
    if eval_result is not None:
        orc._evaluation_agent.run = AsyncMock(return_value=eval_result)
    return orc


def _run_inspection(orc, roi=None):
    return asyncio.run(orc.run(
        user_text="directive test inspection",
        images=make_ok_images(count=2),
        ng_images=make_ng_images(count=2, n_circles=5),
        roi=roi or {"x1": 5, "y1": 5, "x2": 95, "y2": 95},
    ))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Directive Propagation at Construction Time
# ─────────────────────────────────────────────────────────────────────────────

class TestDirectivePropagationAtBuild(unittest.TestCase):
    """Verify each directive is stored on the correct sub-agent at build time."""

    def _orc_with(self, **directive_kwargs):
        return _make_orchestrator(directives=AgentDirectives(**directive_kwargs))

    def test_spec_directive_stored_in_spec_agent(self):
        orc = self._orc_with(spec="use strict spec criteria")
        self.assertEqual(orc._spec_agent.directive, "use strict spec criteria")

    def test_image_analysis_directive_stored(self):
        orc = self._orc_with(image_analysis="focus on edge features")
        self.assertEqual(orc._image_analysis_agent.directive, "focus on edge features")

    def test_depth_directive_stored(self):
        orc = self._orc_with(depth="high resolution depth")
        self.assertEqual(orc._depth_agent.directive, "high resolution depth")

    def test_material_directive_stored(self):
        orc = self._orc_with(material="metal surfaces only")
        self.assertEqual(orc._material_agent.directive, "metal surfaces only")

    def test_pipeline_composer_directive_stored(self):
        orc = self._orc_with(pipeline_composer="force clahe")
        self.assertEqual(orc._pipeline_composer.directive, "force clahe")

    def test_vision_judge_directive_stored(self):
        orc = self._orc_with(vision_judge="strict quality scoring")
        self.assertEqual(orc._vision_judge.directive, "strict quality scoring")

    def test_inspection_plan_directive_stored(self):
        orc = self._orc_with(inspection_plan="detailed 5-step plan")
        self.assertEqual(orc._inspection_plan_agent.directive, "detailed 5-step plan")

    def test_test_directive_stored_in_inspection_agent(self):
        orc = self._orc_with(test="strict")
        self.assertEqual(orc._test_agent_inspection.directive, "strict")

    def test_test_directive_stored_in_align_agent(self):
        orc = self._orc_with(test="lenient")
        self.assertEqual(orc._test_agent_align.directive, "lenient")

    def test_test_directive_stored_in_both_test_agents(self):
        orc = self._orc_with(test="strict mode enabled")
        self.assertEqual(orc._test_agent_inspection.directive, "strict mode enabled")
        self.assertEqual(orc._test_agent_align.directive, "strict mode enabled")

    def test_empty_directives_produce_empty_strings(self):
        orc = _make_orchestrator()
        self.assertEqual(orc._spec_agent.directive, "")
        self.assertEqual(orc._image_analysis_agent.directive, "")
        self.assertEqual(orc._test_agent_inspection.directive, "")
        self.assertEqual(orc._test_agent_align.directive, "")

    def test_multiple_directives_are_independent(self):
        orc = self._orc_with(
            spec="strict spec",
            image_analysis="focus edges",
            test="lenient",
        )
        self.assertEqual(orc._spec_agent.directive, "strict spec")
        self.assertEqual(orc._image_analysis_agent.directive, "focus edges")
        self.assertEqual(orc._test_agent_inspection.directive, "lenient")
        self.assertEqual(orc._test_agent_align.directive, "lenient")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Directive Influence on Runtime Behavior
# ─────────────────────────────────────────────────────────────────────────────

class TestDirectiveInfluenceOnBehavior(unittest.TestCase):
    """Verify directives change actual agent behavior at runtime."""

    def test_strict_directive_tightens_test_threshold(self):
        """'strict' directive increases min_accuracy by 0.1 in TestAgentInspection."""
        from agents.test_agent_inspection import _item_passed
        from agents.models import InspectionItem

        item = InspectionItem(
            item_id=1, name="Test", category="BLOB",
            success_criteria={"min_accuracy": 0.8, "max_fp_rate": 1.0, "max_fn_rate": 1.0},
        )
        # With strict: min_acc = 0.8 + 0.1 = 0.9 → accuracy=0.85 fails
        result_strict = _item_passed(item, accuracy=0.85, fp_rate=0.0, fn_rate=0.0,
                                     directive="strict")
        self.assertFalse(result_strict)

        # Without strict: min_acc = 0.8 → accuracy=0.85 passes
        result_default = _item_passed(item, accuracy=0.85, fp_rate=0.0, fn_rate=0.0,
                                      directive="")
        self.assertTrue(result_default)

    def test_lenient_directive_relaxes_test_threshold(self):
        """'lenient' directive decreases min_accuracy by 0.1 in TestAgentInspection."""
        from agents.test_agent_inspection import _item_passed
        from agents.models import InspectionItem

        item = InspectionItem(
            item_id=1, name="Test", category="BLOB",
            success_criteria={"min_accuracy": 0.8, "max_fp_rate": 0.2, "max_fn_rate": 0.2},
        )
        # With lenient: min_acc = 0.7 → accuracy=0.75 passes
        result_lenient = _item_passed(item, accuracy=0.75, fp_rate=0.0, fn_rate=0.0,
                                      directive="lenient")
        self.assertTrue(result_lenient)

        # Without lenient: min_acc = 0.8 → accuracy=0.75 fails
        result_default = _item_passed(item, accuracy=0.75, fp_rate=0.0, fn_rate=0.0,
                                      directive="")
        self.assertFalse(result_default)

    def test_strict_directive_tightens_align_error_threshold(self):
        """'strict' directive reduces error_threshold by 50% in TestAgentAlign."""
        from agents.test_agent_align import TestAgentAlign
        from agents.models import ProcessingPipeline, PipelineBlock

        pipeline = ProcessingPipeline(
            pipeline_id="pipe_01",
            blocks=[PipelineBlock(block_id="grayscale", block_type="color_space")],
        )
        agent = TestAgentAlign(directive="strict")
        result = asyncio.run(agent.run(
            pipeline=pipeline,
            ok_images=make_ok_images(count=2, h=120, w=120),
            roi={"x1": 20, "y1": 20, "x2": 100, "y2": 100},
            error_threshold=5.0,  # default; strict halves it to 2.5
        ))
        self.assertEqual(result.status, "success")
        # With stricter threshold (2.5 px), success rate may be lower
        self.assertIn("overall_success_rate", result.data)

    def test_clahe_directive_forces_clahe_in_pipeline_composer(self):
        """'force clahe' directive adds CLAHE block to composed pipelines."""
        from agents.pipeline_composer import PipelineComposer
        from agents.models import SceneContext, ImageDiagnosis

        diagnosis = ImageDiagnosis(
            contrast=0.1, noise_level=0.05, edge_density=0.1,
            lighting_uniformity=0.5, illumination_type="uneven",
            noise_frequency="low_freq", reflection_level=0.0,
            surface_type="", depth_complexity=0.0,
            has_shadow_region=False, blob_feasibility=0.3,
            blob_count_estimate=0, color_discriminability=0.0,
            dominant_channel_ratio=1.0, structural_regularity=0.3,
            pattern_repetition=0.1, optimal_color_space="gray",
            threshold_candidate=128.0, edge_sharpness=5.0,
        )
        scene_ctx = SceneContext(
            image_diagnosis=diagnosis, depth_map=None, material_map=None,
        )
        composer_clahe = PipelineComposer(directive="force clahe")
        result = asyncio.run(composer_clahe.run(scene_context=scene_ctx))
        self.assertEqual(result.status, "success")
        pipelines = result.data["pipelines"]
        # With force_clahe=True, at least one pipeline should include CLAHE block
        all_block_ids = [
            block.block_id
            for p in pipelines
            for block in p.blocks
        ]
        self.assertIn("clahe", all_block_ids)

    def test_pipeline_composer_without_directive_no_forced_clahe(self):
        """Without 'clahe' directive and uniform image, clahe not forced."""
        from agents.pipeline_composer import PipelineComposer
        from agents.models import SceneContext, ImageDiagnosis

        diagnosis = ImageDiagnosis(
            contrast=0.1, noise_level=0.05, edge_density=0.1,
            lighting_uniformity=0.1,  # low → needs_clahe=False
            illumination_type="uniform",
            noise_frequency="low_freq", reflection_level=0.0,
            surface_type="", depth_complexity=0.0,
            has_shadow_region=False, blob_feasibility=0.3,
            blob_count_estimate=0, color_discriminability=0.0,
            dominant_channel_ratio=1.0, structural_regularity=0.3,
            pattern_repetition=0.1, optimal_color_space="gray",
            threshold_candidate=128.0, edge_sharpness=5.0,
        )
        scene_ctx = SceneContext(
            image_diagnosis=diagnosis, depth_map=None, material_map=None,
        )
        composer_no_directive = PipelineComposer(directive="")
        result = asyncio.run(composer_no_directive.run(scene_context=scene_ctx))
        self.assertEqual(result.status, "success")
        all_block_ids = [
            block.block_id
            for p in result.data["pipelines"]
            for block in p.blocks
        ]
        # Without forced clahe and low lighting_uniformity, clahe should not be forced
        self.assertNotIn("clahe", all_block_ids)

    def test_spec_directive_passed_as_kwarg_to_spec_agent_run(self):
        """When orchestrator runs, SpecAgent.run receives the directive kwarg."""
        orc = _make_orchestrator(directives=AgentDirectives(spec="use korean output"))
        _wire_mocks(orc)

        _run_inspection(orc)

        call_kwargs = orc._spec_agent.run.call_args.kwargs
        self.assertEqual(call_kwargs.get("directive"), "use korean output")

    def test_inspection_plan_directive_passed_at_run_time(self):
        """InspectionPlanAgent.run receives directive kwarg from orchestrator."""
        orc = _make_orchestrator(
            directives=AgentDirectives(inspection_plan="generate 5 inspection items")
        )
        _wire_mocks(orc)
        _run_inspection(orc)

        call_kwargs = orc._inspection_plan_agent.run.call_args.kwargs
        self.assertEqual(call_kwargs.get("directive"), "generate 5 inspection items")

    def test_vision_judge_directive_passed_at_run_time(self):
        """PipelineSelector receives vision_judge directive (passed as directive kwarg)."""
        orc = _make_orchestrator(
            directives=AgentDirectives(vision_judge="prioritize separability")
        )
        _wire_mocks(orc)
        _run_inspection(orc)

        # vision_judge directive flows through PipelineSelector.run() as `directive`
        # The selector calls vision_judge.run() with the effective_directive
        vj_call_kwargs = orc._vision_judge.run.call_args.kwargs
        self.assertEqual(vj_call_kwargs.get("directive"), "prioritize separability")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Empty Directives = Agent Self-Judgment
# ─────────────────────────────────────────────────────────────────────────────

class TestDirectiveDefaults(unittest.TestCase):
    """Without directives, all agents use their own internal default logic."""

    def test_orchestrator_without_directives_runs_ok(self):
        orc = _make_orchestrator()
        _wire_mocks(orc)
        result = _run_inspection(orc)
        self.assertEqual(result.status, "success")

    def test_empty_directives_all_agents_have_empty_strings(self):
        orc = _make_orchestrator(directives=AgentDirectives())
        self.assertEqual(orc._spec_agent.directive, "")
        self.assertEqual(orc._image_analysis_agent.directive, "")
        self.assertEqual(orc._depth_agent.directive, "")
        self.assertEqual(orc._material_agent.directive, "")
        self.assertEqual(orc._pipeline_composer.directive, "")
        self.assertEqual(orc._vision_judge.directive, "")
        self.assertEqual(orc._inspection_plan_agent.directive, "")
        self.assertEqual(orc._test_agent_inspection.directive, "")
        self.assertEqual(orc._test_agent_align.directive, "")

    def test_none_directives_behave_same_as_empty(self):
        orc_none = _make_orchestrator(directives=None)
        orc_empty = _make_orchestrator(directives=AgentDirectives())
        self.assertEqual(orc_none._spec_agent.directive, orc_empty._spec_agent.directive)
        self.assertEqual(
            orc_none._test_agent_inspection.directive,
            orc_empty._test_agent_inspection.directive,
        )

    def test_default_test_agent_uses_default_threshold(self):
        """Without 'strict'/'lenient' directive, test uses default min_accuracy."""
        from agents.test_agent_inspection import _item_passed
        from agents.models import InspectionItem

        item = InspectionItem(
            item_id=1, name="Default", category="BLOB",
            success_criteria={"min_accuracy": 0.8},
        )
        result = _item_passed(item, accuracy=0.8, fp_rate=0.0, fn_rate=0.0, directive="")
        self.assertTrue(result)

        result_below = _item_passed(item, accuracy=0.79, fp_rate=0.0, fn_rate=0.0, directive="")
        self.assertFalse(result_below)

    def test_partial_directives_leave_others_as_defaults(self):
        """Setting only one directive leaves all others as empty string."""
        orc = _make_orchestrator(directives=AgentDirectives(spec="strict spec only"))
        self.assertEqual(orc._spec_agent.directive, "strict spec only")
        self.assertEqual(orc._image_analysis_agent.directive, "")
        self.assertEqual(orc._test_agent_inspection.directive, "")
        self.assertEqual(orc._pipeline_composer.directive, "")

    def test_orchestrator_result_data_complete_without_directives(self):
        """All expected output fields present even with no directives."""
        orc = _make_orchestrator()
        _wire_mocks(orc)
        result = _run_inspection(orc)
        self.assertEqual(result.status, "success")
        for key in ("mode", "spec", "scene_context", "pipeline",
                    "algorithm_category", "inspection_plan", "blueprint",
                    "parameter_sheets", "test_result", "evaluation",
                    "iterations_used"):
            self.assertIn(key, result.data, f"Missing key: {key}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Different Directives Produce Different Orchestrator Behavior
# ─────────────────────────────────────────────────────────────────────────────

class TestDirectiveDifferentBehavior(unittest.TestCase):
    """Verify that different directive values produce observably different behaviors."""

    def test_different_spec_directives_passed_to_spec_agent(self):
        """Two orchestrators with different spec directives pass different values."""
        orc_a = _make_orchestrator(directives=AgentDirectives(spec="directive A"))
        orc_b = _make_orchestrator(directives=AgentDirectives(spec="directive B"))
        _wire_mocks(orc_a)
        _wire_mocks(orc_b)

        _run_inspection(orc_a)
        _run_inspection(orc_b)

        kwargs_a = orc_a._spec_agent.run.call_args.kwargs
        kwargs_b = orc_b._spec_agent.run.call_args.kwargs
        self.assertNotEqual(kwargs_a.get("directive"), kwargs_b.get("directive"))

    def test_different_inspection_plan_directives(self):
        """Two orchestrators with different inspection_plan directives pass different values."""
        orc_a = _make_orchestrator(directives=AgentDirectives(inspection_plan="3 items only"))
        orc_b = _make_orchestrator(directives=AgentDirectives(inspection_plan="10 items detailed"))
        _wire_mocks(orc_a)
        _wire_mocks(orc_b)

        _run_inspection(orc_a)
        _run_inspection(orc_b)

        kwargs_a = orc_a._inspection_plan_agent.run.call_args.kwargs
        kwargs_b = orc_b._inspection_plan_agent.run.call_args.kwargs
        self.assertNotEqual(kwargs_a.get("directive"), kwargs_b.get("directive"))

    def test_pipeline_composer_clahe_vs_no_clahe(self):
        """clahe directive changes which blocks appear in composed pipelines."""
        from agents.pipeline_composer import PipelineComposer
        from agents.models import SceneContext, ImageDiagnosis

        diagnosis = ImageDiagnosis(
            contrast=0.1, noise_level=0.05, edge_density=0.05,
            lighting_uniformity=0.1,  # below 0.25 → needs_clahe=False naturally
            illumination_type="uniform", noise_frequency="low_freq",
            reflection_level=0.0, surface_type="", depth_complexity=0.0,
            has_shadow_region=False, blob_feasibility=0.2,
            blob_count_estimate=0, color_discriminability=0.0,
            dominant_channel_ratio=1.0, structural_regularity=0.3,
            pattern_repetition=0.1, optimal_color_space="gray",
            threshold_candidate=128.0, edge_sharpness=5.0,
        )
        scene = SceneContext(image_diagnosis=diagnosis, depth_map=None, material_map=None)

        result_no_clahe = asyncio.run(
            PipelineComposer(directive="").run(scene_context=scene)
        )
        result_clahe = asyncio.run(
            PipelineComposer(directive="force clahe please").run(scene_context=scene)
        )

        block_ids_no_clahe = {
            block.block_id
            for p in result_no_clahe.data["pipelines"]
            for block in p.blocks
        }
        block_ids_clahe = {
            block.block_id
            for p in result_clahe.data["pipelines"]
            for block in p.blocks
        }

        self.assertNotIn("clahe", block_ids_no_clahe)
        self.assertIn("clahe", block_ids_clahe)


if __name__ == "__main__":
    unittest.main()
