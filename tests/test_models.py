"""Tests for agents/models.py and agents/base_agent.py (Step 12)."""
import asyncio
import inspect
from dataclasses import fields
from typing import Any, Optional

import pytest


# ─── AgentResult ─────────────────────────────────────────────────────────────

class TestAgentResult:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import AgentResult
        r = AgentResult(status="success", data={"key": "val"})
        assert r.status == "success"
        assert r.data == {"key": "val"}

    def test_default_error_message_is_none(self):
        from agents.models import AgentResult
        r = AgentResult(status="success", data={})
        assert r.error_message is None

    def test_default_execution_time_ms_is_zero(self):
        from agents.models import AgentResult
        r = AgentResult(status="success", data={})
        assert r.execution_time_ms == 0.0

    def test_can_set_error_message(self):
        from agents.models import AgentResult
        r = AgentResult(status="failure", data={}, error_message="oops")
        assert r.error_message == "oops"

    def test_can_set_execution_time(self):
        from agents.models import AgentResult
        r = AgentResult(status="success", data={}, execution_time_ms=42.5)
        assert r.execution_time_ms == 42.5

    def test_accepts_success_failure_error_statuses(self):
        from agents.models import AgentResult
        for status in ("success", "failure", "error"):
            r = AgentResult(status=status, data={})
            assert r.status == status

    def test_data_field_is_dict(self):
        from agents.models import AgentResult
        r = AgentResult(status="success", data={"a": 1})
        assert isinstance(r.data, dict)


# ─── ImageDiagnosis ───────────────────────────────────────────────────────────

class TestImageDiagnosis:
    def _make(self):
        from agents.models import ImageDiagnosis
        return ImageDiagnosis(
            contrast=0.5,
            noise_level=0.1,
            edge_density=0.3,
            lighting_uniformity=0.8,
            illumination_type="diffuse",
            noise_frequency="low",
            reflection_level=0.2,
            surface_type="metal",
            depth_complexity=0.4,
            has_shadow_region=False,
            blob_feasibility=0.7,
            blob_count_estimate=5,
            color_discriminability=0.6,
            dominant_channel_ratio=0.5,
            structural_regularity=0.3,
            pattern_repetition=0.2,
            optimal_color_space="BGR",
            threshold_candidate=128.0,
            edge_sharpness=0.9,
        )

    def test_can_instantiate(self):
        d = self._make()
        assert d.contrast == 0.5

    def test_has_all_required_fields(self):
        from agents.models import ImageDiagnosis
        field_names = {f.name for f in fields(ImageDiagnosis)}
        expected = {
            "contrast", "noise_level", "edge_density", "lighting_uniformity",
            "illumination_type", "noise_frequency", "reflection_level",
            "surface_type", "depth_complexity", "has_shadow_region",
            "blob_feasibility", "blob_count_estimate", "color_discriminability",
            "dominant_channel_ratio", "structural_regularity", "pattern_repetition",
            "optimal_color_space", "threshold_candidate", "edge_sharpness",
        }
        assert expected.issubset(field_names)

    def test_has_shadow_region_is_bool(self):
        d = self._make()
        assert isinstance(d.has_shadow_region, bool)

    def test_blob_count_estimate_is_int(self):
        d = self._make()
        assert isinstance(d.blob_count_estimate, int)

    def test_float_fields_are_float(self):
        d = self._make()
        assert isinstance(d.contrast, float)
        assert isinstance(d.noise_level, float)
        assert isinstance(d.edge_density, float)


# ─── InspectionItem ───────────────────────────────────────────────────────────

class TestInspectionItem:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import InspectionItem
        item = InspectionItem(item_id=1, name="scratch", category="defect")
        assert item.item_id == 1
        assert item.name == "scratch"
        assert item.category == "defect"

    def test_depends_on_defaults_to_empty_list(self):
        from agents.models import InspectionItem
        item = InspectionItem(item_id=1, name="x", category="y")
        assert item.depends_on == []

    def test_safety_role_defaults_to_false(self):
        from agents.models import InspectionItem
        item = InspectionItem(item_id=1, name="x", category="y")
        assert item.safety_role is False

    def test_success_criteria_defaults_to_empty_dict(self):
        from agents.models import InspectionItem
        item = InspectionItem(item_id=1, name="x", category="y")
        assert item.success_criteria == {}

    def test_depends_on_lists_are_independent(self):
        from agents.models import InspectionItem
        a = InspectionItem(item_id=1, name="a", category="c")
        b = InspectionItem(item_id=2, name="b", category="c")
        a.depends_on.append(99)
        assert b.depends_on == []

    def test_can_set_depends_on(self):
        from agents.models import InspectionItem
        item = InspectionItem(item_id=1, name="x", category="y", depends_on=[2, 3])
        assert item.depends_on == [2, 3]


# ─── InspectionPlan ───────────────────────────────────────────────────────────

class TestInspectionPlan:
    def test_can_instantiate_with_items_and_purpose(self):
        from agents.models import InspectionItem, InspectionPlan
        items = [InspectionItem(item_id=1, name="x", category="y")]
        plan = InspectionPlan(items=items, inspection_purpose="quality check")
        assert plan.inspection_purpose == "quality check"

    def test_post_init_sets_total_items(self):
        from agents.models import InspectionItem, InspectionPlan
        items = [
            InspectionItem(item_id=1, name="a", category="c"),
            InspectionItem(item_id=2, name="b", category="c"),
            InspectionItem(item_id=3, name="d", category="c"),
        ]
        plan = InspectionPlan(items=items, inspection_purpose="test")
        assert plan.total_items == 3

    def test_post_init_with_empty_items_sets_zero(self):
        from agents.models import InspectionPlan
        plan = InspectionPlan(items=[], inspection_purpose="empty")
        assert plan.total_items == 0

    def test_total_items_default_is_overridden_by_post_init(self):
        from agents.models import InspectionItem, InspectionPlan
        items = [InspectionItem(item_id=i, name=str(i), category="c") for i in range(5)]
        plan = InspectionPlan(items=items, inspection_purpose="x")
        assert plan.total_items == 5


# ─── JudgementResult ─────────────────────────────────────────────────────────

class TestJudgementResult:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import JudgementResult
        j = JudgementResult(
            visibility_score=0.8,
            separability_score=0.7,
            measurability_score=0.9,
            overall_score=0.8,
        )
        assert j.visibility_score == 0.8
        assert j.overall_score == 0.8

    def test_problems_defaults_to_empty_list(self):
        from agents.models import JudgementResult
        j = JudgementResult(
            visibility_score=0.5, separability_score=0.5,
            measurability_score=0.5, overall_score=0.5,
        )
        assert j.problems == []

    def test_next_suggestion_defaults_to_empty_string(self):
        from agents.models import JudgementResult
        j = JudgementResult(
            visibility_score=0.5, separability_score=0.5,
            measurability_score=0.5, overall_score=0.5,
        )
        assert j.next_suggestion == ""

    def test_problems_lists_are_independent(self):
        from agents.models import JudgementResult
        a = JudgementResult(visibility_score=0, separability_score=0, measurability_score=0, overall_score=0)
        b = JudgementResult(visibility_score=0, separability_score=0, measurability_score=0, overall_score=0)
        a.problems.append("issue")
        assert b.problems == []


# ─── AgentDirectives ─────────────────────────────────────────────────────────

class TestAgentDirectives:
    def test_can_instantiate_with_no_args(self):
        from agents.models import AgentDirectives
        d = AgentDirectives()
        assert d.orchestrator == ""
        assert d.spec == ""
        assert d.image_analysis == ""
        assert d.depth == ""
        assert d.material == ""
        assert d.pipeline_composer == ""
        assert d.vision_judge == ""
        assert d.inspection_plan == ""
        assert d.test == ""

    def test_all_nine_fields_exist(self):
        from agents.models import AgentDirectives
        field_names = {f.name for f in fields(AgentDirectives)}
        expected = {
            "orchestrator", "spec", "image_analysis", "depth", "material",
            "pipeline_composer", "vision_judge", "inspection_plan", "test",
        }
        assert expected == field_names

    def test_can_set_individual_fields(self):
        from agents.models import AgentDirectives
        d = AgentDirectives(spec="Analyze the image carefully")
        assert d.spec == "Analyze the image carefully"
        assert d.orchestrator == ""


# ─── PipelineBlock ────────────────────────────────────────────────────────────

class TestPipelineBlock:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import PipelineBlock
        b = PipelineBlock(block_id="b1", block_type="threshold")
        assert b.block_id == "b1"
        assert b.block_type == "threshold"

    def test_params_defaults_to_empty_dict(self):
        from agents.models import PipelineBlock
        b = PipelineBlock(block_id="b1", block_type="blur")
        assert b.params == {}

    def test_params_dicts_are_independent(self):
        from agents.models import PipelineBlock
        a = PipelineBlock(block_id="a", block_type="x")
        b = PipelineBlock(block_id="b", block_type="x")
        a.params["key"] = "val"
        assert b.params == {}


# ─── ProcessingPipeline ───────────────────────────────────────────────────────

class TestProcessingPipeline:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import ProcessingPipeline
        p = ProcessingPipeline(pipeline_id="p1", blocks=[])
        assert p.pipeline_id == "p1"
        assert p.blocks == []

    def test_quality_score_defaults_to_zero(self):
        from agents.models import ProcessingPipeline
        p = ProcessingPipeline(pipeline_id="p1", blocks=[])
        assert p.quality_score == 0.0

    def test_judge_score_defaults_to_zero(self):
        from agents.models import ProcessingPipeline
        p = ProcessingPipeline(pipeline_id="p1", blocks=[])
        assert p.judge_score == 0.0

    def test_description_defaults_to_empty_string(self):
        from agents.models import ProcessingPipeline
        p = ProcessingPipeline(pipeline_id="p1", blocks=[])
        assert p.description == ""

    def test_contains_pipeline_blocks(self):
        from agents.models import PipelineBlock, ProcessingPipeline
        blocks = [
            PipelineBlock(block_id="b1", block_type="threshold"),
            PipelineBlock(block_id="b2", block_type="blur"),
        ]
        p = ProcessingPipeline(pipeline_id="p1", blocks=blocks)
        assert len(p.blocks) == 2
        assert p.blocks[0].block_id == "b1"


# ─── BlueprintNode ────────────────────────────────────────────────────────────

class TestBlueprintNode:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import BlueprintNode
        n = BlueprintNode(node_id="n1", node_type="preprocessing", label="Blur")
        assert n.node_id == "n1"
        assert n.node_type == "preprocessing"
        assert n.label == "Blur"

    def test_params_defaults_to_empty_dict(self):
        from agents.models import BlueprintNode
        n = BlueprintNode(node_id="n1", node_type="feature", label="Edges")
        assert n.params == {}

    def test_valid_node_types(self):
        from agents.models import BlueprintNode
        for ntype in ("preprocessing", "feature", "inspection", "decision"):
            n = BlueprintNode(node_id="x", node_type=ntype, label="L")
            assert n.node_type == ntype


# ─── BlueprintEdge ────────────────────────────────────────────────────────────

class TestBlueprintEdge:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import BlueprintEdge
        e = BlueprintEdge(source_id="n1", target_id="n2")
        assert e.source_id == "n1"
        assert e.target_id == "n2"

    def test_label_defaults_to_empty_string(self):
        from agents.models import BlueprintEdge
        e = BlueprintEdge(source_id="n1", target_id="n2")
        assert e.label == ""


# ─── Blueprint ────────────────────────────────────────────────────────────────

class TestBlueprint:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import Blueprint
        b = Blueprint(nodes=[], edges=[])
        assert b.nodes == []
        assert b.edges == []

    def test_svg_content_defaults_to_empty_string(self):
        from agents.models import Blueprint
        b = Blueprint(nodes=[], edges=[])
        assert b.svg_content == ""

    def test_algorithm_description_defaults_to_empty_string(self):
        from agents.models import Blueprint
        b = Blueprint(nodes=[], edges=[])
        assert b.algorithm_description == ""

    def test_parameter_sheet_defaults_to_empty_dict(self):
        from agents.models import Blueprint
        b = Blueprint(nodes=[], edges=[])
        assert b.parameter_sheet == {}

    def test_contains_nodes_and_edges(self):
        from agents.models import Blueprint, BlueprintEdge, BlueprintNode
        nodes = [BlueprintNode(node_id="n1", node_type="preprocessing", label="Blur")]
        edges = [BlueprintEdge(source_id="n1", target_id="n2")]
        b = Blueprint(nodes=nodes, edges=edges)
        assert len(b.nodes) == 1
        assert len(b.edges) == 1

    def test_parameter_sheet_dicts_are_independent(self):
        from agents.models import Blueprint
        a = Blueprint(nodes=[], edges=[])
        b_obj = Blueprint(nodes=[], edges=[])
        a.parameter_sheet["key"] = "val"
        assert b_obj.parameter_sheet == {}


# ─── SceneContext ─────────────────────────────────────────────────────────────

class TestSceneContext:
    def _make_diagnosis(self):
        from agents.models import ImageDiagnosis
        return ImageDiagnosis(
            contrast=0.5, noise_level=0.1, edge_density=0.3,
            lighting_uniformity=0.8, illumination_type="diffuse",
            noise_frequency="low", reflection_level=0.2,
            surface_type="metal", depth_complexity=0.4,
            has_shadow_region=False, blob_feasibility=0.7,
            blob_count_estimate=5, color_discriminability=0.6,
            dominant_channel_ratio=0.5, structural_regularity=0.3,
            pattern_repetition=0.2, optimal_color_space="BGR",
            threshold_candidate=128.0, edge_sharpness=0.9,
        )

    def test_can_instantiate_with_required_fields(self):
        from agents.models import SceneContext
        ctx = SceneContext(image_diagnosis=self._make_diagnosis(), depth_map=None, material_map=None)
        assert ctx.depth_map is None
        assert ctx.material_map is None

    def test_holds_image_diagnosis_reference(self):
        from agents.models import SceneContext
        diag = self._make_diagnosis()
        ctx = SceneContext(image_diagnosis=diag, depth_map=None, material_map=None)
        assert ctx.image_diagnosis is diag
        assert ctx.image_diagnosis.contrast == 0.5

    def test_roi_defaults_to_none(self):
        from agents.models import SceneContext
        ctx = SceneContext(image_diagnosis=self._make_diagnosis(), depth_map=None, material_map=None)
        assert ctx.roi is None

    def test_spec_defaults_to_empty_dict(self):
        from agents.models import SceneContext
        ctx = SceneContext(image_diagnosis=self._make_diagnosis(), depth_map=None, material_map=None)
        assert ctx.spec == {}

    def test_can_set_roi_dict(self):
        from agents.models import SceneContext
        ctx = SceneContext(
            image_diagnosis=self._make_diagnosis(),
            depth_map=None,
            material_map=None,
            roi={"x1": 0, "y1": 0, "x2": 100, "y2": 100},
        )
        assert ctx.roi == {"x1": 0, "y1": 0, "x2": 100, "y2": 100}

    def test_depth_map_accepts_any(self):
        from agents.models import SceneContext
        fake_array = [[1, 2], [3, 4]]
        ctx = SceneContext(image_diagnosis=self._make_diagnosis(), depth_map=fake_array, material_map=None)
        assert ctx.depth_map == fake_array


# ─── AlgorithmCategory enum ───────────────────────────────────────────────────

class TestAlgorithmCategory:
    def test_members_exist(self):
        from agents.models import AlgorithmCategory
        assert hasattr(AlgorithmCategory, "BLOB")
        assert hasattr(AlgorithmCategory, "COLOR_FILTER")
        assert hasattr(AlgorithmCategory, "EDGE_DETECTION")
        assert hasattr(AlgorithmCategory, "TEMPLATE_MATCHING")
        assert hasattr(AlgorithmCategory, "GEOMETRIC")

    def test_is_enum(self):
        import enum
        from agents.models import AlgorithmCategory
        assert issubclass(AlgorithmCategory, enum.Enum)

    def test_has_five_members(self):
        from agents.models import AlgorithmCategory
        assert len(AlgorithmCategory) == 5

    def test_members_have_values(self):
        from agents.models import AlgorithmCategory
        for member in AlgorithmCategory:
            assert member.value is not None


# ─── FailureReason enum ───────────────────────────────────────────────────────

class TestFailureReason:
    def test_members_exist(self):
        from agents.models import FailureReason
        assert hasattr(FailureReason, "PIPELINE_BAD_FIT")
        assert hasattr(FailureReason, "PIPELINE_BAD_PARAMS")
        assert hasattr(FailureReason, "ALGORITHM_WRONG_CATEGORY")
        assert hasattr(FailureReason, "RUNTIME_ERROR")
        assert hasattr(FailureReason, "INSPECTION_PLAN_ISSUE")
        assert hasattr(FailureReason, "SPEC_ISSUE")

    def test_is_enum(self):
        import enum
        from agents.models import FailureReason
        assert issubclass(FailureReason, enum.Enum)

    def test_has_six_members(self):
        from agents.models import FailureReason
        assert len(FailureReason) == 6


# ─── EvaluationResult ────────────────────────────────────────────────────────

class TestEvaluationResult:
    def test_can_instantiate_with_passed_true(self):
        from agents.models import EvaluationResult
        e = EvaluationResult(passed=True)
        assert e.passed is True

    def test_failure_reason_defaults_to_none(self):
        from agents.models import EvaluationResult
        e = EvaluationResult(passed=False)
        assert e.failure_reason is None

    def test_metrics_defaults_to_empty_dict(self):
        from agents.models import EvaluationResult
        e = EvaluationResult(passed=True)
        assert e.metrics == {}

    def test_details_defaults_to_empty_string(self):
        from agents.models import EvaluationResult
        e = EvaluationResult(passed=True)
        assert e.details == ""

    def test_can_set_failure_reason(self):
        from agents.models import EvaluationResult, FailureReason
        e = EvaluationResult(passed=False, failure_reason=FailureReason.RUNTIME_ERROR)
        assert e.failure_reason == FailureReason.RUNTIME_ERROR

    def test_metrics_dicts_are_independent(self):
        from agents.models import EvaluationResult
        a = EvaluationResult(passed=True)
        b = EvaluationResult(passed=True)
        a.metrics["k"] = 1
        assert b.metrics == {}


# ─── DecisionVerdict enum ─────────────────────────────────────────────────────

class TestDecisionVerdict:
    def test_members_exist(self):
        from agents.models import DecisionVerdict
        assert hasattr(DecisionVerdict, "RULE_BASED")
        assert hasattr(DecisionVerdict, "EDGE_LEARNING")
        assert hasattr(DecisionVerdict, "DEEP_LEARNING")
        assert hasattr(DecisionVerdict, "HARDWARE_IMPROVEMENT")

    def test_is_enum(self):
        import enum
        from agents.models import DecisionVerdict
        assert issubclass(DecisionVerdict, enum.Enum)

    def test_has_four_members(self):
        from agents.models import DecisionVerdict
        assert len(DecisionVerdict) == 4


# ─── DecisionResult ───────────────────────────────────────────────────────────

class TestDecisionResult:
    def test_can_instantiate_with_required_fields(self):
        from agents.models import DecisionResult, DecisionVerdict
        r = DecisionResult(
            verdict=DecisionVerdict.RULE_BASED,
            confidence=0.9,
            reasoning="Sufficient edge density",
        )
        assert r.verdict == DecisionVerdict.RULE_BASED
        assert r.confidence == 0.9
        assert r.reasoning == "Sufficient edge density"

    def test_feature_variability_defaults_to_zero(self):
        from agents.models import DecisionResult, DecisionVerdict
        r = DecisionResult(verdict=DecisionVerdict.DEEP_LEARNING, confidence=0.5, reasoning="x")
        assert r.feature_variability == 0.0

    def test_suggestions_defaults_to_empty_list(self):
        from agents.models import DecisionResult, DecisionVerdict
        r = DecisionResult(verdict=DecisionVerdict.DEEP_LEARNING, confidence=0.5, reasoning="x")
        assert r.suggestions == []

    def test_suggestions_lists_are_independent(self):
        from agents.models import DecisionResult, DecisionVerdict
        a = DecisionResult(verdict=DecisionVerdict.RULE_BASED, confidence=0.5, reasoning="x")
        b = DecisionResult(verdict=DecisionVerdict.RULE_BASED, confidence=0.5, reasoning="x")
        a.suggestions.append("upgrade")
        assert b.suggestions == []


# ─── BaseAgent ────────────────────────────────────────────────────────────────

class TestBaseAgent:
    def test_base_agent_is_abstract_and_cannot_be_instantiated(self):
        from agents.base_agent import BaseAgent
        with pytest.raises(TypeError):
            BaseAgent(name="test")  # type: ignore

    def test_run_is_abstract_method(self):
        from agents.base_agent import BaseAgent
        assert inspect.isabstract(BaseAgent)
        abstract_methods = BaseAgent.__abstractmethods__
        assert "run" in abstract_methods

    def test_subclass_must_implement_run(self):
        from agents.base_agent import BaseAgent

        class IncompleteAgent(BaseAgent):
            pass

        with pytest.raises(TypeError):
            IncompleteAgent(name="incomplete")  # type: ignore

    def test_concrete_subclass_can_be_instantiated(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="dummy")
        assert agent.name == "dummy"

    def test_name_is_stored(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="my_agent")
        assert agent.name == "my_agent"

    def test_directive_defaults_to_empty_string(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="x")
        assert agent.directive == ""

    def test_directive_can_be_set(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="x", directive="focus on defects")
        assert agent.directive == "focus on defects"

    def test_has_logger_property(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="test_logger")
        assert agent.logger is not None

    def test_logger_is_bound_to_agent_name(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="bound_test")
        logger = agent.logger
        # structlog BoundLogger has _context with bound values
        ctx = logger._context if hasattr(logger, "_context") else {}
        assert ctx.get("agent_name") == "bound_test"

    def test_run_method_is_coroutine(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={"result": "ok"})

        agent = DummyAgent(name="coro_test")
        coro = agent.run()
        assert inspect.iscoroutine(coro)
        asyncio.run(coro)

    def test_run_returns_agent_result(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={"done": True})

        agent = DummyAgent(name="result_test")
        result = asyncio.run(agent.run())
        assert isinstance(result, AgentResult)
        assert result.status == "success"

    def test_log_helper_method_exists(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="log_test")
        assert hasattr(agent, "_log")
        assert callable(agent._log)

    def test_log_helper_delegates_without_raising(self):
        from agents.base_agent import BaseAgent
        from agents.models import AgentResult

        class DummyAgent(BaseAgent):
            async def run(self, **kwargs) -> AgentResult:
                return AgentResult(status="success", data={})

        agent = DummyAgent(name="log_call")
        # Should not raise
        agent._log("info", "test message", extra_key="extra_val")
