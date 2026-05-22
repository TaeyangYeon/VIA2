"""FeedbackController — rule-based retry strategy controller. No LLM."""
import time
from dataclasses import dataclass, field
from typing import Optional

from agents.models import (
    AgentResult,
    FailureReason,
    JudgementResult,
    ProcessingPipeline,
)

# All possible strategy names — used to determine should_continue
_ALL_STRATEGIES: frozenset[str] = frozenset({
    "replace_pipeline",
    "retry_params",
    "change_category",
    "retry_pipeline",
    "revise_plan",
    "relax_spec",
})

# Priority order: index 0 = highest priority (PIPELINE_BAD_FIT wins all ties)
_SEVERITY_ORDER: list[FailureReason] = [
    FailureReason.PIPELINE_BAD_FIT,          # high
    FailureReason.ALGORITHM_WRONG_CATEGORY,  # high
    FailureReason.RUNTIME_ERROR,             # medium
    FailureReason.INSPECTION_PLAN_ISSUE,     # medium
    FailureReason.PIPELINE_BAD_PARAMS,       # low
    FailureReason.SPEC_ISSUE,                # low
]

# Maps each FailureReason → (strategy_name, severity)
_STRATEGY_MAP: dict[FailureReason, tuple[str, str]] = {
    FailureReason.PIPELINE_BAD_FIT:         ("replace_pipeline", "high"),
    FailureReason.ALGORITHM_WRONG_CATEGORY: ("change_category",  "high"),
    FailureReason.RUNTIME_ERROR:            ("retry_pipeline",   "medium"),
    FailureReason.INSPECTION_PLAN_ISSUE:    ("revise_plan",      "medium"),
    FailureReason.PIPELINE_BAD_PARAMS:      ("retry_params",     "low"),
    FailureReason.SPEC_ISSUE:               ("relax_spec",       "low"),
}


@dataclass
class FeedbackContext:
    iteration: int = 0
    history: list[dict] = field(default_factory=list)
    tried_strategies: set[str] = field(default_factory=set)
    failed_pipelines: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for AgentResult — converts set to list for JSON compatibility."""
        return {
            "iteration": self.iteration,
            "history": list(self.history),
            "tried_strategies": list(self.tried_strategies),
            "failed_pipelines": list(self.failed_pipelines),
            "constraints": list(self.constraints),
        }


def _select_dominant(failure_reasons: list[str]) -> Optional[FailureReason]:
    """Return highest-priority FailureReason from a list of reason value strings."""
    present: set[FailureReason] = set()
    for r in failure_reasons:
        if r is None:
            continue
        try:
            present.add(FailureReason(r))
        except ValueError:
            pass
    for candidate in _SEVERITY_ORDER:
        if candidate in present:
            return candidate
    return None


def _generate_hints(
    reason: FailureReason,
    pipeline: Optional[ProcessingPipeline],
    iteration: int,
) -> list[str]:
    if reason == FailureReason.PIPELINE_BAD_FIT:
        if pipeline is not None:
            block_types = sorted({b.block_type for b in pipeline.blocks})
            return [
                f"Pipeline {pipeline.pipeline_id!r} has poor fit "
                f"(block types: {', '.join(block_types) or 'unknown'}); "
                "replace with a fundamentally different pipeline architecture."
            ]
        return ["Current pipeline has poor fit; replace with a different pipeline architecture."]

    if reason == FailureReason.PIPELINE_BAD_PARAMS:
        return [
            f"Expand or shift parameter search ranges (iteration {iteration}); "
            "try larger kernel sizes or adjusted threshold windows."
        ]

    if reason == FailureReason.ALGORITHM_WRONG_CATEGORY:
        return [
            "Algorithm category mismatch detected; override Algorithm Selector "
            "and choose the next-best category for this inspection type."
        ]

    if reason == FailureReason.RUNTIME_ERROR:
        return [
            "Runtime error during pipeline execution; retry with a different pipeline "
            "variant that avoids the failing block configuration."
        ]

    if reason == FailureReason.INSPECTION_PLAN_ISSUE:
        return [
            "Inspection plan dependency issue detected; re-run Inspection Plan Agent "
            "to resolve dependency ordering before retrying execution."
        ]

    if reason == FailureReason.SPEC_ISSUE:
        return [
            "Specification targets may be unrealistic; warn the user that current "
            "min_accuracy requirements exceed typical pipeline capability."
        ]

    return []


def _generate_constraint(
    reason: FailureReason,
    pipeline: Optional[ProcessingPipeline],
) -> Optional[str]:
    if reason == FailureReason.PIPELINE_BAD_FIT:
        if pipeline is not None:
            block_types = sorted({b.block_type for b in pipeline.blocks})
            return f"exclude pipeline block types: {', '.join(block_types)}"
        return "exclude current pipeline architecture"

    if reason == FailureReason.PIPELINE_BAD_PARAMS:
        return "expand parameter search range or shift distribution"

    if reason == FailureReason.ALGORITHM_WRONG_CATEGORY:
        return "override algorithm category; avoid previously selected category"

    if reason == FailureReason.RUNTIME_ERROR:
        return "avoid pipeline variants that caused runtime errors"

    if reason == FailureReason.INSPECTION_PLAN_ISSUE:
        return "re-generate inspection plan with corrected dependency ordering"

    if reason == FailureReason.SPEC_ISSUE:
        return "relax min_accuracy spec or flag to user as unrealistic"

    return None


class FeedbackController:
    """Rule-based feedback controller. No LLM dependency."""

    def __init__(self, directive: str = "") -> None:
        self.name = "feedback_controller"
        self.directive = directive
        self._context = FeedbackContext()

    async def run(
        self,
        evaluation_result: AgentResult,
        pipeline: Optional[ProcessingPipeline] = None,
        vision_judge_result: Optional[JudgementResult] = None,
        directive: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.monotonic()

        if evaluation_result.status != "success":
            return AgentResult(
                status="error",
                data={},
                error_message=evaluation_result.error_message or "upstream evaluation failed",
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        vision_judge_suggestion: Optional[str] = None
        if vision_judge_result is not None:
            raw_suggestion = vision_judge_result.next_suggestion
            vision_judge_suggestion = raw_suggestion if raw_suggestion else None

        item_evaluations: list[dict] = evaluation_result.data.get("item_evaluations", [])
        failure_reasons: list[str] = [
            e["failure_reason"]
            for e in item_evaluations
            if e.get("failure_reason") is not None
        ]

        dominant = _select_dominant(failure_reasons)

        self._context.iteration += 1

        if pipeline is not None and pipeline.pipeline_id not in self._context.failed_pipelines:
            self._context.failed_pipelines.append(pipeline.pipeline_id)

        if dominant is None:
            self._context.history.append({
                "iteration": self._context.iteration,
                "failure_reason": None,
                "strategy": None,
                "vision_judge_suggestion": vision_judge_suggestion,
            })
            return AgentResult(
                status="success",
                data={
                    "strategy": None,
                    "severity": None,
                    "primary_failure_reason": None,
                    "context": self._context.to_dict(),
                    "hints": [],
                    "should_continue": len(self._context.tried_strategies) < len(_ALL_STRATEGIES),
                    "vision_judge_suggestion": vision_judge_suggestion,
                },
                execution_time_ms=(time.monotonic() - t0) * 1000.0,
            )

        strategy, severity = _STRATEGY_MAP[dominant]
        self._context.tried_strategies.add(strategy)

        hints = _generate_hints(dominant, pipeline, self._context.iteration)
        constraint = _generate_constraint(dominant, pipeline)
        if constraint is not None:
            self._context.constraints.append(constraint)

        self._context.history.append({
            "iteration": self._context.iteration,
            "failure_reason": dominant.value,
            "strategy": strategy,
            "vision_judge_suggestion": vision_judge_suggestion,
        })

        should_continue = len(self._context.tried_strategies) < len(_ALL_STRATEGIES)

        return AgentResult(
            status="success",
            data={
                "strategy": strategy,
                "severity": severity,
                "primary_failure_reason": dominant.value,
                "context": self._context.to_dict(),
                "hints": hints,
                "should_continue": should_continue,
                "vision_judge_suggestion": vision_judge_suggestion,
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )

    def reset(self) -> None:
        """Reset accumulated context (new execution cycle)."""
        self._context = FeedbackContext()

    @property
    def context(self) -> FeedbackContext:
        """Read-only access to current feedback context."""
        return self._context
