"""Tests for EvaluationAgent — Step 30."""
import asyncio

import pytest

from agents.evaluation_agent import EvaluationAgent
from agents.base_agent import BaseAgent
from agents.models import (
    AgentResult,
    FailureReason,
    InspectionItem,
    InspectionPlan,
    ProcessingPipeline,
    PipelineBlock,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def make_item_result(
    item_id=1,
    name="test",
    category="BLOB",
    accuracy=0.9,
    fp_rate=0.05,
    fn_rate=0.05,
    passed=True,
    skipped=False,
    details=None,
):
    return {
        "item_id": item_id,
        "name": name,
        "category": category,
        "accuracy": accuracy,
        "fp_rate": fp_rate,
        "fn_rate": fn_rate,
        "passed": passed,
        "skipped": skipped,
        "details": details or {},
    }


def make_inspection_result(item_results, overall_accuracy=0.0, overall_passed=False):
    return AgentResult(
        status="success",
        data={
            "item_results": item_results,
            "overall_accuracy": overall_accuracy,
            "overall_passed": overall_passed,
            "execution_order": [r["item_id"] for r in item_results],
            "total_items": len(item_results),
            "passed_items": sum(1 for r in item_results if r["passed"] and not r["skipped"]),
            "skipped_items": sum(1 for r in item_results if r["skipped"]),
            "failed_items": sum(1 for r in item_results if not r["passed"] and not r["skipped"]),
        },
    )


def make_pipeline(block_ids):
    blocks = [PipelineBlock(block_id=bid, block_type=bid) for bid in block_ids]
    return ProcessingPipeline(pipeline_id="test_pipeline", blocks=blocks)


def make_plan(items):
    return InspectionPlan(items=items, inspection_purpose="test")


def make_align_result(
    success_rate=0.9,
    mean_error=2.0,
    max_error=5.0,
    overall_passed=True,
    error_threshold=5.0,
    n_images=5,
):
    per_image = [
        {
            "image_index": i,
            "detected_x": 100.0,
            "detected_y": 100.0,
            "ground_truth_x": 100.0,
            "ground_truth_y": 100.0,
            "error_px": mean_error,
            "method_used": "template",
            "match_score": 0.8,
            "success": mean_error < error_threshold,
        }
        for i in range(n_images)
    ]
    return AgentResult(
        status="success",
        data={
            "per_image_results": per_image,
            "overall_success_rate": success_rate,
            "overall_mean_error": mean_error,
            "overall_max_error": max_error,
            "overall_passed": overall_passed,
            "method_stats": {"template": n_images, "edge": 0, "caliper": 0},
            "error_threshold": error_threshold,
            "total_images": n_images,
        },
    )


# ── Instantiation ──────────────────────────────────────────────────────────────

class TestEvaluationAgentInstantiation:
    def test_inherits_base_agent(self):
        assert isinstance(EvaluationAgent(), BaseAgent)

    def test_default_name(self):
        assert EvaluationAgent().name == "evaluation_agent"

    def test_default_directive_empty(self):
        assert EvaluationAgent().directive == ""

    def test_custom_directive(self):
        assert EvaluationAgent(directive="strict").directive == "strict"


# ── AgentResult structure ──────────────────────────────────────────────────────

class TestAgentResultStructure:
    def setup_method(self):
        self.agent = EvaluationAgent()
        self.result_in = make_inspection_result(
            [make_item_result(item_id=1, passed=True)],
            overall_accuracy=0.9,
            overall_passed=True,
        )

    def test_returns_agent_result(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert isinstance(r, AgentResult)

    def test_status_success_on_valid_input(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert r.status == "success"

    def test_execution_time_ms_non_negative(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert r.execution_time_ms >= 0.0

    def test_data_has_item_evaluations(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "item_evaluations" in r.data

    def test_data_has_overall_passed(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "overall_passed" in r.data

    def test_data_has_total_items(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "total_items" in r.data

    def test_data_has_passed_items(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "passed_items" in r.data

    def test_data_has_failed_items(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "failed_items" in r.data

    def test_data_has_failure_summary(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "failure_summary" in r.data

    def test_item_evaluation_has_item_id(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "item_id" in r.data["item_evaluations"][0]

    def test_item_evaluation_has_passed(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "passed" in r.data["item_evaluations"][0]

    def test_item_evaluation_has_failure_reason(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "failure_reason" in r.data["item_evaluations"][0]

    def test_item_evaluation_has_details(self):
        r = asyncio.run(self.agent.run(test_result=self.result_in))
        assert "details" in r.data["item_evaluations"][0]


# ── Passed items ───────────────────────────────────────────────────────────────

class TestPassedItems:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_passed_item_has_no_failure_reason(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.9, passed=True)],
            overall_accuracy=0.9,
            overall_passed=True,
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] is None

    def test_passed_item_has_passed_true(self):
        r_in = make_inspection_result([make_item_result(item_id=1, accuracy=0.9, passed=True)])
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["passed"] is True

    def test_all_pass_overall_passed_true(self):
        r_in = make_inspection_result(
            [
                make_item_result(item_id=1, accuracy=0.9, passed=True),
                make_item_result(item_id=2, accuracy=0.85, passed=True),
            ],
            overall_accuracy=0.875,
            overall_passed=True,
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["overall_passed"] is True


# ── PIPELINE_BAD_FIT ───────────────────────────────────────────────────────────

class TestPipelineBadFit:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_accuracy_0_3_is_bad_fit(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.3, fp_rate=0.7, fn_rate=0.7, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_FIT.value

    def test_accuracy_zero_is_bad_fit(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.0, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_FIT.value

    def test_accuracy_0_49_is_bad_fit(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.49, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_FIT.value

    def test_accuracy_0_5_is_not_bad_fit(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.5, fp_rate=0.5, fn_rate=0.5, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] != FailureReason.PIPELINE_BAD_FIT.value


# ── PIPELINE_BAD_PARAMS ────────────────────────────────────────────────────────

class TestPipelineBadParams:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_accuracy_0_65_is_bad_params(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.65, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_PARAMS.value

    def test_accuracy_0_5_boundary_is_bad_params(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.5, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_PARAMS.value

    def test_accuracy_0_79_is_bad_params(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.79, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_PARAMS.value

    def test_high_fp_rate_decent_accuracy_is_bad_params(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.75, fp_rate=0.4, fn_rate=0.05, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_PARAMS.value

    def test_high_fn_rate_decent_accuracy_is_bad_params(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.72, fp_rate=0.05, fn_rate=0.45, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_PARAMS.value

    def test_good_accuracy_but_strict_criteria_is_bad_params(self):
        item = InspectionItem(
            item_id=1, name="check", category="BLOB",
            success_criteria={"min_accuracy": 0.9},
        )
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.85, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.PIPELINE_BAD_PARAMS.value


# ── ALGORITHM_WRONG_CATEGORY ───────────────────────────────────────────────────

class TestAlgorithmWrongCategory:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_edge_item_no_edge_blocks_is_wrong_category(self):
        pipeline = make_pipeline(["otsu", "erosion"])
        item = InspectionItem(item_id=1, name="edge_check", category="EDGE_DETECTION")
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, category="EDGE_DETECTION", accuracy=0.4, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, pipeline=pipeline, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.ALGORITHM_WRONG_CATEGORY.value

    def test_color_filter_item_grayscale_only_pipeline_is_wrong_category(self):
        pipeline = make_pipeline(["grayscale", "canny"])
        item = InspectionItem(item_id=1, name="color_check", category="COLOR_FILTER")
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, category="COLOR_FILTER", accuracy=0.35, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, pipeline=pipeline, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.ALGORITHM_WRONG_CATEGORY.value

    def test_blob_item_edge_only_pipeline_is_wrong_category(self):
        pipeline = make_pipeline(["canny", "sobel"])
        item = InspectionItem(item_id=1, name="blob_check", category="BLOB")
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, category="BLOB", accuracy=0.3, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, pipeline=pipeline, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.ALGORITHM_WRONG_CATEGORY.value

    def test_edge_item_with_edge_block_not_wrong_category(self):
        pipeline = make_pipeline(["grayscale", "canny"])
        item = InspectionItem(item_id=1, name="edge_check", category="EDGE_DETECTION")
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, category="EDGE_DETECTION", accuracy=0.6, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, pipeline=pipeline, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] != FailureReason.ALGORITHM_WRONG_CATEGORY.value


# ── RUNTIME_ERROR ──────────────────────────────────────────────────────────────

class TestRuntimeError:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_skipped_no_depends_on_is_runtime_error(self):
        item = InspectionItem(item_id=1, name="test", category="BLOB", depends_on=[])
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, passed=False, skipped=True)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.RUNTIME_ERROR.value

    def test_skipped_no_plan_is_runtime_error(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, passed=False, skipped=True)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.RUNTIME_ERROR.value


# ── INSPECTION_PLAN_ISSUE ──────────────────────────────────────────────────────

class TestInspectionPlanIssue:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_skipped_item_with_depends_on_is_plan_issue(self):
        items = [
            InspectionItem(item_id=1, name="parent", category="BLOB"),
            InspectionItem(item_id=2, name="child", category="BLOB", depends_on=[1]),
        ]
        plan = make_plan(items)
        r_in = make_inspection_result([
            make_item_result(item_id=1, accuracy=0.3, passed=False, skipped=False),
            make_item_result(item_id=2, passed=False, skipped=True),
        ])
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        ev2 = next(e for e in r.data["item_evaluations"] if e["item_id"] == 2)
        assert ev2["failure_reason"] == FailureReason.INSPECTION_PLAN_ISSUE.value

    def test_parent_failed_item_not_plan_issue(self):
        items = [InspectionItem(item_id=1, name="parent", category="BLOB")]
        plan = make_plan(items)
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.3, passed=False, skipped=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] != FailureReason.INSPECTION_PLAN_ISSUE.value


# ── SPEC_ISSUE ─────────────────────────────────────────────────────────────────

class TestSpecIssue:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_min_accuracy_1_0_is_spec_issue(self):
        item = InspectionItem(
            item_id=1, name="perfect", category="BLOB",
            success_criteria={"min_accuracy": 1.0},
        )
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.85, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.SPEC_ISSUE.value

    def test_min_accuracy_0_99_is_spec_issue(self):
        item = InspectionItem(
            item_id=1, name="near_perfect", category="BLOB",
            success_criteria={"min_accuracy": 0.99},
        )
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.88, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] == FailureReason.SPEC_ISSUE.value

    def test_min_accuracy_0_9_not_spec_issue(self):
        item = InspectionItem(
            item_id=1, name="check", category="BLOB",
            success_criteria={"min_accuracy": 0.9},
        )
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.85, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] != FailureReason.SPEC_ISSUE.value

    def test_passed_item_with_high_criteria_no_failure_reason(self):
        item = InspectionItem(
            item_id=1, name="check", category="BLOB",
            success_criteria={"min_accuracy": 0.99},
        )
        plan = make_plan([item])
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=1.0, passed=True)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["item_evaluations"][0]["failure_reason"] is None


# ── Align mode ─────────────────────────────────────────────────────────────────

class TestAlignModeEvaluation:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_align_mode_success_returns_success_status(self):
        r = asyncio.run(self.agent.run(
            test_result=make_align_result(success_rate=0.9, overall_passed=True),
            mode="align",
        ))
        assert r.status == "success"

    def test_align_mode_passed_true_when_overall_passed(self):
        r = asyncio.run(self.agent.run(
            test_result=make_align_result(success_rate=0.9, overall_passed=True),
            mode="align",
        ))
        assert r.data["overall_passed"] is True

    def test_align_mode_low_success_rate_bad_fit_or_params(self):
        r = asyncio.run(self.agent.run(
            test_result=make_align_result(
                success_rate=0.2, mean_error=20.0, max_error=30.0, overall_passed=False
            ),
            mode="align",
        ))
        assert r.data["overall_passed"] is False
        assert r.data.get("failure_reason") in [
            FailureReason.PIPELINE_BAD_FIT.value,
            FailureReason.PIPELINE_BAD_PARAMS.value,
        ]

    def test_align_mode_medium_success_rate_bad_params(self):
        r = asyncio.run(self.agent.run(
            test_result=make_align_result(
                success_rate=0.6, mean_error=7.0, max_error=12.0, overall_passed=False
            ),
            mode="align",
        ))
        assert r.data.get("failure_reason") == FailureReason.PIPELINE_BAD_PARAMS.value

    def test_align_mode_has_item_evaluations(self):
        r = asyncio.run(self.agent.run(
            test_result=make_align_result(success_rate=0.9, overall_passed=True, n_images=3),
            mode="align",
        ))
        assert "item_evaluations" in r.data
        assert len(r.data["item_evaluations"]) == 3

    def test_align_mode_has_failure_summary(self):
        r = asyncio.run(self.agent.run(
            test_result=make_align_result(success_rate=0.9, overall_passed=True),
            mode="align",
        ))
        assert "failure_summary" in r.data


# ── Mixed results ──────────────────────────────────────────────────────────────

class TestMixedResults:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_mixed_counts_correct(self):
        items = [
            InspectionItem(item_id=1, name="pass", category="BLOB"),
            InspectionItem(item_id=2, name="fail", category="BLOB"),
            InspectionItem(item_id=3, name="skip", category="BLOB", depends_on=[2]),
        ]
        plan = make_plan(items)
        r_in = make_inspection_result([
            make_item_result(item_id=1, accuracy=0.9, passed=True),
            make_item_result(item_id=2, accuracy=0.3, passed=False),
            make_item_result(item_id=3, passed=False, skipped=True),
        ])
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        assert r.data["total_items"] == 3
        assert r.data["passed_items"] == 1
        assert r.data["failed_items"] >= 1

    def test_mixed_failure_summary_populated(self):
        items = [
            InspectionItem(item_id=1, name="pass", category="BLOB"),
            InspectionItem(item_id=2, name="bad_fit", category="BLOB"),
            InspectionItem(item_id=3, name="bad_params", category="BLOB"),
        ]
        plan = make_plan(items)
        r_in = make_inspection_result([
            make_item_result(item_id=1, accuracy=0.9, passed=True),
            make_item_result(item_id=2, accuracy=0.2, passed=False),
            make_item_result(item_id=3, accuracy=0.65, passed=False),
        ])
        r = asyncio.run(self.agent.run(test_result=r_in, inspection_plan=plan))
        summary = r.data["failure_summary"]
        assert summary.get(FailureReason.PIPELINE_BAD_FIT.value, 0) >= 1
        assert summary.get(FailureReason.PIPELINE_BAD_PARAMS.value, 0) >= 1


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_upstream_error_result_returns_error(self):
        err = AgentResult(status="error", data={}, error_message="no images provided")
        r = asyncio.run(self.agent.run(test_result=err))
        assert r.status == "error"

    def test_upstream_error_preserves_message(self):
        err = AgentResult(status="error", data={}, error_message="no images provided")
        r = asyncio.run(self.agent.run(test_result=err))
        assert r.error_message is not None

    def test_empty_item_results_handled(self):
        r_in = make_inspection_result([])
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.status in ("success", "error")
        if r.status == "success":
            assert r.data["total_items"] == 0

    def test_missing_fields_in_item_result_no_crash(self):
        bad = AgentResult(
            status="success",
            data={
                "item_results": [{"item_id": 1, "passed": False, "skipped": False}],
                "overall_accuracy": 0.0,
                "overall_passed": False,
                "total_items": 1,
                "passed_items": 0,
                "skipped_items": 0,
                "failed_items": 1,
            },
        )
        r = asyncio.run(self.agent.run(test_result=bad))
        assert r.status in ("success", "error")


# ── Directive handling ─────────────────────────────────────────────────────────

class TestDirectiveHandling:
    def test_constructor_directive_stored(self):
        assert EvaluationAgent(directive="strict").directive == "strict"

    def test_run_directive_overrides_constructor(self):
        agent = EvaluationAgent(directive="lenient")
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.9, passed=True)],
            overall_accuracy=0.9,
            overall_passed=True,
        )
        r = asyncio.run(agent.run(test_result=r_in, directive="strict"))
        assert r.status == "success"

    def test_none_directive_falls_back_to_constructor(self):
        agent = EvaluationAgent(directive="lenient")
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.9, passed=True)],
            overall_accuracy=0.9,
            overall_passed=True,
        )
        r = asyncio.run(agent.run(test_result=r_in, directive=None))
        assert r.status == "success"

    def test_empty_string_directive_accepted(self):
        agent = EvaluationAgent(directive="strict")
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.9, passed=True)],
            overall_accuracy=0.9,
            overall_passed=True,
        )
        r = asyncio.run(agent.run(test_result=r_in, directive=""))
        assert r.status == "success"


# ── Overall evaluation summary ─────────────────────────────────────────────────

class TestOverallEvaluationSummary:
    def setup_method(self):
        self.agent = EvaluationAgent()

    def test_all_passed_overall_passed_true(self):
        r_in = make_inspection_result(
            [
                make_item_result(item_id=1, accuracy=0.9, passed=True),
                make_item_result(item_id=2, accuracy=0.95, passed=True),
            ],
            overall_accuracy=0.925,
            overall_passed=True,
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["overall_passed"] is True

    def test_any_failed_overall_passed_false(self):
        r_in = make_inspection_result(
            [
                make_item_result(item_id=1, accuracy=0.9, passed=True),
                make_item_result(item_id=2, accuracy=0.3, passed=False),
            ],
            overall_accuracy=0.6,
            overall_passed=False,
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["overall_passed"] is False

    def test_total_items_count(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=i, accuracy=0.9, passed=True) for i in range(5)],
            overall_accuracy=0.9,
            overall_passed=True,
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["total_items"] == 5

    def test_passed_items_count(self):
        r_in = make_inspection_result([
            make_item_result(item_id=1, accuracy=0.9, passed=True),
            make_item_result(item_id=2, accuracy=0.3, passed=False),
            make_item_result(item_id=3, accuracy=0.9, passed=True),
        ])
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert r.data["passed_items"] == 2

    def test_failure_summary_is_dict(self):
        r_in = make_inspection_result(
            [make_item_result(item_id=1, accuracy=0.3, passed=False)]
        )
        r = asyncio.run(self.agent.run(test_result=r_in))
        assert isinstance(r.data["failure_summary"], dict)

    def test_failure_summary_total_matches_failed_evaluations(self):
        r_in = make_inspection_result([
            make_item_result(item_id=1, accuracy=0.3, passed=False),
            make_item_result(item_id=2, accuracy=0.65, passed=False),
        ])
        r = asyncio.run(self.agent.run(test_result=r_in))
        summary = r.data["failure_summary"]
        total_in_summary = sum(summary.values())
        failed_evals = sum(
            1 for e in r.data["item_evaluations"] if e["failure_reason"] is not None
        )
        assert total_in_summary == failed_evals
