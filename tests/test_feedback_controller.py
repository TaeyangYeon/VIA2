"""Tests for FeedbackController — Step 31."""
import asyncio
import json

import pytest

from agents.feedback_controller import FeedbackController, FeedbackContext
from agents.models import (
    AgentResult,
    FailureReason,
    JudgementResult,
    ProcessingPipeline,
    PipelineBlock,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def make_eval_result(failure_reasons: list, overall_passed: bool = False) -> AgentResult:
    """Build a minimal EvaluationAgent output for given failure reasons (str or None)."""
    item_evaluations = []
    failure_summary: dict = {}
    for i, fr in enumerate(failure_reasons):
        passed = fr is None
        item_evaluations.append({
            "item_id": i + 1,
            "passed": passed,
            "failure_reason": fr,
            "details": "passed" if passed else f"failed: {fr}",
        })
        if fr is not None:
            failure_summary[fr] = failure_summary.get(fr, 0) + 1

    return AgentResult(
        status="success",
        data={
            "item_evaluations": item_evaluations,
            "overall_passed": overall_passed,
            "total_items": len(failure_reasons),
            "passed_items": sum(1 for fr in failure_reasons if fr is None),
            "failed_items": sum(1 for fr in failure_reasons if fr is not None),
            "failure_summary": failure_summary,
        },
    )


def make_pipeline(pipeline_id: str, block_ids: list = None) -> ProcessingPipeline:
    block_ids = block_ids or ["blur", "threshold"]
    return ProcessingPipeline(
        pipeline_id=pipeline_id,
        blocks=[PipelineBlock(block_id=bid, block_type=bid) for bid in block_ids],
    )


def make_judgement(suggestion: str = "try increasing contrast") -> JudgementResult:
    return JudgementResult(
        visibility_score=0.6,
        separability_score=0.5,
        measurability_score=0.7,
        overall_score=0.6,
        next_suggestion=suggestion,
    )


# ── instantiation ─────────────────────────────────────────────────────────────

class TestInstantiation:
    def test_name(self):
        fc = FeedbackController()
        assert fc.name == "feedback_controller"

    def test_default_directive(self):
        fc = FeedbackController()
        assert fc.directive == ""

    def test_custom_directive(self):
        fc = FeedbackController(directive="be strict")
        assert fc.directive == "be strict"

    def test_initial_context_type(self):
        fc = FeedbackController()
        assert isinstance(fc.context, FeedbackContext)

    def test_initial_context_iteration_zero(self):
        fc = FeedbackController()
        assert fc.context.iteration == 0

    def test_initial_context_empty_history(self):
        fc = FeedbackController()
        assert fc.context.history == []

    def test_initial_context_empty_tried_strategies(self):
        fc = FeedbackController()
        assert fc.context.tried_strategies == set()

    def test_initial_context_empty_failed_pipelines(self):
        fc = FeedbackController()
        assert fc.context.failed_pipelines == []

    def test_initial_context_empty_constraints(self):
        fc = FeedbackController()
        assert fc.context.constraints == []


# ── strategy mapping — all 6 failure reasons ─────────────────────────────────

class TestStrategyMapping:
    def test_pipeline_bad_fit_strategy(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["strategy"] == "replace_pipeline"

    def test_pipeline_bad_fit_severity(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["severity"] == "high"

    def test_pipeline_bad_fit_primary_reason(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["primary_failure_reason"] == FailureReason.PIPELINE_BAD_FIT.value

    def test_pipeline_bad_params_strategy(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_PARAMS.value])))
        assert result.data["strategy"] == "retry_params"

    def test_pipeline_bad_params_severity(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_PARAMS.value])))
        assert result.data["severity"] == "low"

    def test_algorithm_wrong_category_strategy(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.ALGORITHM_WRONG_CATEGORY.value])))
        assert result.data["strategy"] == "change_category"

    def test_algorithm_wrong_category_severity(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.ALGORITHM_WRONG_CATEGORY.value])))
        assert result.data["severity"] == "high"

    def test_runtime_error_strategy(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert result.data["strategy"] == "retry_pipeline"

    def test_runtime_error_severity(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert result.data["severity"] == "medium"

    def test_inspection_plan_issue_strategy(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.INSPECTION_PLAN_ISSUE.value])))
        assert result.data["strategy"] == "revise_plan"

    def test_inspection_plan_issue_severity(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.INSPECTION_PLAN_ISSUE.value])))
        assert result.data["severity"] == "medium"

    def test_spec_issue_strategy(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.SPEC_ISSUE.value])))
        assert result.data["strategy"] == "relax_spec"

    def test_spec_issue_severity(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.SPEC_ISSUE.value])))
        assert result.data["severity"] == "low"


# ── dominant strategy selection ───────────────────────────────────────────────

class TestDominantStrategy:
    def test_high_beats_low(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.PIPELINE_BAD_FIT.value,
            FailureReason.SPEC_ISSUE.value,
        ])))
        assert result.data["strategy"] == "replace_pipeline"

    def test_high_beats_medium(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.RUNTIME_ERROR.value,
            FailureReason.ALGORITHM_WRONG_CATEGORY.value,
        ])))
        assert result.data["strategy"] == "change_category"

    def test_pipeline_bad_fit_beats_algorithm_wrong_category(self):
        """PIPELINE_BAD_FIT has priority over ALGORITHM_WRONG_CATEGORY (both high)."""
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.ALGORITHM_WRONG_CATEGORY.value,
            FailureReason.PIPELINE_BAD_FIT.value,
        ])))
        assert result.data["strategy"] == "replace_pipeline"

    def test_medium_beats_low(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.PIPELINE_BAD_PARAMS.value,
            FailureReason.INSPECTION_PLAN_ISSUE.value,
        ])))
        assert result.data["strategy"] == "revise_plan"

    def test_runtime_error_beats_inspection_plan_issue(self):
        """RUNTIME_ERROR has priority over INSPECTION_PLAN_ISSUE (both medium)."""
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.INSPECTION_PLAN_ISSUE.value,
            FailureReason.RUNTIME_ERROR.value,
        ])))
        assert result.data["strategy"] == "retry_pipeline"

    def test_pipeline_bad_params_beats_spec_issue(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.SPEC_ISSUE.value,
            FailureReason.PIPELINE_BAD_PARAMS.value,
        ])))
        assert result.data["strategy"] == "retry_params"

    def test_all_reasons_combined_dominant_is_pipeline_bad_fit(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([
            FailureReason.SPEC_ISSUE.value,
            FailureReason.PIPELINE_BAD_PARAMS.value,
            FailureReason.INSPECTION_PLAN_ISSUE.value,
            FailureReason.RUNTIME_ERROR.value,
            FailureReason.ALGORITHM_WRONG_CATEGORY.value,
            FailureReason.PIPELINE_BAD_FIT.value,
        ])))
        assert result.data["strategy"] == "replace_pipeline"


# ── vision judge integration ───────────────────────────────────────────────────

class TestVisionJudgeIntegration:
    def test_next_suggestion_captured(self):
        fc = FeedbackController()
        jresult = make_judgement("increase kernel size")
        result = asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_PARAMS.value]),
            vision_judge_result=jresult,
        ))
        assert result.data["vision_judge_suggestion"] == "increase kernel size"

    def test_no_vision_judge_suggestion_is_none(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["vision_judge_suggestion"] is None

    def test_vision_judge_suggestion_in_history(self):
        fc = FeedbackController()
        jresult = make_judgement("use morphological close")
        asyncio.run(fc.run(
            make_eval_result([FailureReason.RUNTIME_ERROR.value]),
            vision_judge_result=jresult,
        ))
        assert fc.context.history[0]["vision_judge_suggestion"] == "use morphological close"

    def test_vision_judge_empty_suggestion(self):
        fc = FeedbackController()
        jresult = make_judgement("")
        result = asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            vision_judge_result=jresult,
        ))
        # Empty string treated as None or empty string — either way present in data
        assert "vision_judge_suggestion" in result.data


# ── context accumulation ──────────────────────────────────────────────────────

class TestContextAccumulation:
    def test_iteration_increments_each_run(self):
        fc = FeedbackController()
        for _ in range(3):
            asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_PARAMS.value])))
        assert fc.context.iteration == 3

    def test_history_grows_with_each_run(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert len(fc.context.history) == 2

    def test_history_entry_has_iteration(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert fc.context.history[0]["iteration"] == 1

    def test_history_entry_has_failure_reason(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert fc.context.history[0]["failure_reason"] == FailureReason.PIPELINE_BAD_FIT.value

    def test_history_entry_has_strategy(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert fc.context.history[0]["strategy"] == "replace_pipeline"

    def test_tried_strategies_tracked_after_two_runs(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert "replace_pipeline" in fc.context.tried_strategies
        assert "retry_pipeline" in fc.context.tried_strategies

    def test_tried_strategies_no_duplicates(self):
        """Repeatedly hitting same reason should not grow tried_strategies beyond 1."""
        fc = FeedbackController()
        for _ in range(5):
            asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert fc.context.tried_strategies == {"replace_pipeline"}

    def test_context_in_result_matches_internal_context(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["context"]["iteration"] == fc.context.iteration


# ── pipeline tracking ─────────────────────────────────────────────────────────

class TestPipelineTracking:
    def test_failed_pipeline_added(self):
        fc = FeedbackController()
        asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("pipe_001"),
        ))
        assert "pipe_001" in fc.context.failed_pipelines

    def test_failed_pipelines_grows_with_different_pipelines(self):
        fc = FeedbackController()
        asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("pipe_001"),
        ))
        asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("pipe_002"),
        ))
        assert len(fc.context.failed_pipelines) == 2

    def test_no_duplicate_pipeline(self):
        fc = FeedbackController()
        p = make_pipeline("pipe_dup")
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]), pipeline=p))
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]), pipeline=p))
        assert fc.context.failed_pipelines.count("pipe_dup") == 1

    def test_no_pipeline_provided_leaves_empty(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert fc.context.failed_pipelines == []

    def test_pipeline_in_result_context(self):
        fc = FeedbackController()
        asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("pipe_abc"),
        ))
        assert "pipe_abc" in fc.context.to_dict()["failed_pipelines"]


# ── constraint generation ─────────────────────────────────────────────────────

class TestConstraintGeneration:
    def test_replace_pipeline_adds_constraint(self):
        fc = FeedbackController()
        asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("p1", ["canny", "sobel"]),
        ))
        assert len(fc.context.constraints) > 0

    def test_retry_params_adds_constraint(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_PARAMS.value])))
        assert len(fc.context.constraints) > 0

    def test_change_category_adds_constraint(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.ALGORITHM_WRONG_CATEGORY.value])))
        assert len(fc.context.constraints) > 0

    def test_runtime_error_adds_constraint(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert len(fc.context.constraints) > 0

    def test_inspection_plan_issue_adds_constraint(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.INSPECTION_PLAN_ISSUE.value])))
        assert len(fc.context.constraints) > 0

    def test_spec_issue_adds_constraint(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.SPEC_ISSUE.value])))
        assert len(fc.context.constraints) > 0

    def test_constraints_accumulate_across_runs(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        count_after_first = len(fc.context.constraints)
        asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert len(fc.context.constraints) > count_after_first

    def test_hints_are_nonempty_strings(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert len(result.data["hints"]) > 0
        assert all(isinstance(h, str) and len(h) > 0 for h in result.data["hints"])

    def test_hints_present_for_all_six_reasons(self):
        reasons = [r.value for r in FailureReason]
        for reason in reasons:
            fc = FeedbackController()
            result = asyncio.run(fc.run(make_eval_result([reason])))
            assert len(result.data["hints"]) > 0, f"No hints for {reason}"

    def test_replace_pipeline_hint_mentions_pipeline(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("p_edge", ["canny"]),
        ))
        combined = " ".join(result.data["hints"]).lower()
        assert "pipeline" in combined


# ── should_continue flag ──────────────────────────────────────────────────────

class TestShouldContinue:
    def test_true_when_untried_strategies_exist(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["should_continue"] is True

    def test_false_when_all_six_strategies_exhausted(self):
        fc = FeedbackController()
        all_reasons = [
            FailureReason.PIPELINE_BAD_FIT.value,
            FailureReason.PIPELINE_BAD_PARAMS.value,
            FailureReason.ALGORITHM_WRONG_CATEGORY.value,
            FailureReason.RUNTIME_ERROR.value,
            FailureReason.INSPECTION_PLAN_ISSUE.value,
            FailureReason.SPEC_ISSUE.value,
        ]
        for reason in all_reasons:
            result = asyncio.run(fc.run(make_eval_result([reason])))
        assert result.data["should_continue"] is False

    def test_true_after_five_strategies(self):
        fc = FeedbackController()
        five_reasons = [
            FailureReason.PIPELINE_BAD_FIT.value,
            FailureReason.PIPELINE_BAD_PARAMS.value,
            FailureReason.ALGORITHM_WRONG_CATEGORY.value,
            FailureReason.RUNTIME_ERROR.value,
            FailureReason.INSPECTION_PLAN_ISSUE.value,
        ]
        for reason in five_reasons:
            result = asyncio.run(fc.run(make_eval_result([reason])))
        assert result.data["should_continue"] is True

    def test_should_continue_is_bool(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        assert isinstance(result.data["should_continue"], bool)


# ── reset ─────────────────────────────────────────────────────────────────────

class TestReset:
    def test_reset_clears_iteration(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        asyncio.run(fc.run(make_eval_result([FailureReason.RUNTIME_ERROR.value])))
        fc.reset()
        assert fc.context.iteration == 0

    def test_reset_clears_history(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        fc.reset()
        assert fc.context.history == []

    def test_reset_clears_tried_strategies(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        fc.reset()
        assert fc.context.tried_strategies == set()

    def test_reset_clears_constraints(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        fc.reset()
        assert fc.context.constraints == []

    def test_reset_clears_failed_pipelines(self):
        fc = FeedbackController()
        asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            pipeline=make_pipeline("pipe_to_reset"),
        ))
        fc.reset()
        assert fc.context.failed_pipelines == []

    def test_run_after_reset_iteration_starts_at_one(self):
        fc = FeedbackController()
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        fc.reset()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.data["context"]["iteration"] == 1

    def test_reset_does_not_affect_name_or_directive(self):
        fc = FeedbackController(directive="keep me")
        asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        fc.reset()
        assert fc.name == "feedback_controller"
        assert fc.directive == "keep me"


# ── directive handling ─────────────────────────────────────────────────────────

class TestDirectiveHandling:
    def test_constructor_directive_stored(self):
        fc = FeedbackController(directive="constructor directive")
        assert fc.directive == "constructor directive"

    def test_runtime_directive_accepted(self):
        fc = FeedbackController(directive="default")
        result = asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            directive="runtime override",
        ))
        assert result.status == "success"

    def test_none_directive_uses_constructor(self):
        fc = FeedbackController(directive="keep this")
        result = asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            directive=None,
        ))
        assert result.status == "success"

    def test_empty_directive_accepted(self):
        fc = FeedbackController(directive="")
        result = asyncio.run(fc.run(
            make_eval_result([FailureReason.PIPELINE_BAD_FIT.value]),
            directive="",
        ))
        assert result.status == "success"


# ── error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_upstream_error_status_propagated(self):
        fc = FeedbackController()
        error_result = AgentResult(
            status="error",
            data={},
            error_message="upstream pipeline agent failed",
        )
        result = asyncio.run(fc.run(error_result))
        assert result.status == "error"

    def test_upstream_error_message_preserved(self):
        fc = FeedbackController()
        error_result = AgentResult(
            status="error",
            data={},
            error_message="upstream pipeline agent failed",
        )
        result = asyncio.run(fc.run(error_result))
        assert result.error_message is not None
        assert len(result.error_message) > 0

    def test_upstream_error_does_not_increment_iteration(self):
        fc = FeedbackController()
        error_result = AgentResult(status="error", data={}, error_message="fail")
        asyncio.run(fc.run(error_result))
        assert fc.context.iteration == 0

    def test_empty_item_evaluations_returns_success(self):
        fc = FeedbackController()
        empty_result = AgentResult(
            status="success",
            data={
                "item_evaluations": [],
                "overall_passed": True,
                "failure_summary": {},
            },
        )
        result = asyncio.run(fc.run(empty_result))
        assert result.status == "success"

    def test_empty_item_evaluations_should_continue_true(self):
        fc = FeedbackController()
        empty_result = AgentResult(
            status="success",
            data={
                "item_evaluations": [],
                "overall_passed": True,
                "failure_summary": {},
            },
        )
        result = asyncio.run(fc.run(empty_result))
        assert result.data["should_continue"] is True

    def test_all_items_passed_returns_success(self):
        fc = FeedbackController()
        all_passed = make_eval_result([None, None, None], overall_passed=True)
        result = asyncio.run(fc.run(all_passed))
        assert result.status == "success"

    def test_all_items_passed_no_primary_failure_reason(self):
        fc = FeedbackController()
        all_passed = make_eval_result([None, None], overall_passed=True)
        result = asyncio.run(fc.run(all_passed))
        assert result.data["primary_failure_reason"] is None

    def test_no_error_message_on_success(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.error_message is None


# ── AgentResult structure ─────────────────────────────────────────────────────

class TestAgentResultStructure:
    def test_status_success_on_valid_input(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.status == "success"

    def test_data_has_strategy_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "strategy" in result.data

    def test_data_has_severity_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "severity" in result.data

    def test_data_has_primary_failure_reason_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "primary_failure_reason" in result.data

    def test_data_has_context_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "context" in result.data

    def test_data_has_hints_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "hints" in result.data

    def test_hints_is_list(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert isinstance(result.data["hints"], list)

    def test_data_has_should_continue_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "should_continue" in result.data

    def test_data_has_vision_judge_suggestion_key(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert "vision_judge_suggestion" in result.data

    def test_context_is_json_serializable(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        json.dumps(result.data["context"])  # must not raise

    def test_execution_time_ms_non_negative(self):
        fc = FeedbackController()
        result = asyncio.run(fc.run(make_eval_result([FailureReason.PIPELINE_BAD_FIT.value])))
        assert result.execution_time_ms >= 0.0

    def test_severity_values_are_valid(self):
        valid_severities = {"high", "medium", "low", None}
        for reason in FailureReason:
            fc = FeedbackController()
            result = asyncio.run(fc.run(make_eval_result([reason.value])))
            assert result.data["severity"] in valid_severities


# ── FeedbackContext.to_dict ───────────────────────────────────────────────────

class TestFeedbackContextToDict:
    def test_to_dict_converts_set_to_list(self):
        ctx = FeedbackContext()
        ctx.tried_strategies.add("replace_pipeline")
        ctx.tried_strategies.add("retry_params")
        d = ctx.to_dict()
        assert isinstance(d["tried_strategies"], list)
        assert set(d["tried_strategies"]) == {"replace_pipeline", "retry_params"}

    def test_to_dict_has_all_fields(self):
        ctx = FeedbackContext()
        d = ctx.to_dict()
        for key in ("iteration", "history", "tried_strategies", "failed_pipelines", "constraints"):
            assert key in d

    def test_to_dict_json_serializable(self):
        ctx = FeedbackContext()
        ctx.tried_strategies.add("replace_pipeline")
        ctx.constraints.append("exclude edge-only pipeline")
        json.dumps(ctx.to_dict())

    def test_to_dict_does_not_expose_live_set(self):
        """Mutating returned dict should not affect internal state."""
        ctx = FeedbackContext()
        ctx.tried_strategies.add("replace_pipeline")
        d = ctx.to_dict()
        d["tried_strategies"].append("injected")
        assert "injected" not in ctx.tried_strategies
