"""InspectionPlanAgent — uses LLM to freely design inspection plans from purpose + SceneContext."""
import json
import re
import time
from dataclasses import asdict

from agents.base_agent import BaseAgent
from agents.models import AgentResult, AlgorithmCategory, InspectionItem, InspectionPlan, SceneContext
from agents.prompts.inspection_plan_prompt import build_inspection_plan_prompt
from backend.services.ai_adapter.base import BaseAIAdapter

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    if match:
        return match.group(1)
    return text.strip()


def _parse_items(raw: str) -> list[dict]:
    cleaned = _strip_fences(raw)
    if not cleaned:
        raise ValueError("Empty response from adapter")
    data = json.loads(cleaned)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items", [])
    raise ValueError("Unexpected JSON structure from LLM")


def _validate_depends_on(items: list[dict], logger) -> list[dict]:
    valid_ids = {item["item_id"] for item in items}
    cleaned = []
    for item in items:
        original = list(item.get("depends_on", []))
        filtered = [dep for dep in original if dep in valid_ids]
        if len(filtered) != len(original):
            invalid = set(original) - set(filtered)
            logger.warning("Removing invalid depends_on references", item_id=item["item_id"], invalid=invalid)
        cleaned.append({**item, "depends_on": filtered})
    return cleaned


def _to_inspection_item(raw: dict) -> InspectionItem:
    success_criteria = raw.get("success_criteria", {})
    if not isinstance(success_criteria, dict):
        success_criteria = {"metric": str(success_criteria), "threshold": 0}
    safety_role = raw.get("safety_role", False)
    if not isinstance(safety_role, bool):
        safety_role = bool(safety_role)
    return InspectionItem(
        item_id=int(raw["item_id"]),
        name=str(raw["name"]),
        category=str(raw.get("category", "")),
        depends_on=list(raw.get("depends_on", [])),
        safety_role=safety_role,
        success_criteria=success_criteria,
    )


class InspectionPlanAgent(BaseAgent):
    def __init__(
        self,
        adapter: BaseAIAdapter,
        model: str = "qwen2.5-coder:7b",
        directive: str = "",
    ) -> None:
        super().__init__(name="inspection_plan", directive=directive)
        self.adapter = adapter
        self.model = model

    async def run(
        self,
        purpose: str,
        scene_context: SceneContext | None,
        algorithm_category: AlgorithmCategory | None,
        directive: str | None = None,
        **kwargs,
    ) -> AgentResult:
        if not purpose or not purpose.strip():
            return AgentResult(
                status="error",
                data={},
                error_message="Inspection purpose is required",
                execution_time_ms=0.0,
            )
        if scene_context is None:
            return AgentResult(
                status="error",
                data={},
                error_message="SceneContext is required",
                execution_time_ms=0.0,
            )
        if algorithm_category is None:
            return AgentResult(
                status="error",
                data={},
                error_message="AlgorithmCategory is required",
                execution_time_ms=0.0,
            )

        effective_directive = directive if directive is not None else self.directive
        system_prompt, user_prompt = build_inspection_plan_prompt(
            purpose=purpose,
            scene_context=scene_context,
            algorithm_category=algorithm_category,
            directive=effective_directive or None,
        )

        start = time.monotonic()
        try:
            raw = await self.adapter.generate_text(
                user_prompt,
                self.model,
                system_prompt=system_prompt,
            )
            raw_items = _parse_items(raw)
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            self._log("error", "InspectionPlanAgent failed", error=str(exc))
            error_msg = str(exc)
            if isinstance(exc, (json.JSONDecodeError, ValueError)) and "Empty response" not in error_msg:
                error_msg = "Failed to parse inspection plan from LLM response"
            return AgentResult(
                status="error",
                data={},
                error_message=error_msg,
                execution_time_ms=elapsed,
            )

        if not raw_items:
            elapsed = (time.monotonic() - start) * 1000
            self._log("warning", "InspectionPlanAgent received empty plan")
            return AgentResult(
                status="error",
                data={},
                error_message="LLM returned empty inspection plan",
                execution_time_ms=elapsed,
            )

        validated = _validate_depends_on(raw_items, self._logger)
        items = [_to_inspection_item(r) for r in validated]
        plan = InspectionPlan(items=items, inspection_purpose=purpose)

        elapsed = (time.monotonic() - start) * 1000
        self._log("info", "InspectionPlanAgent completed", total_items=plan.total_items)
        return AgentResult(
            status="success",
            data={"plan": asdict(plan), "raw_response": raw},
            error_message=None,
            execution_time_ms=elapsed,
        )
