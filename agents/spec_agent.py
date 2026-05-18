"""SpecAgent — parses user text + ROI into structured vision spec via LLM."""
import json
import re
import time

from agents.base_agent import BaseAgent
from agents.models import AgentResult
from agents.prompts.spec_prompt import build_spec_prompt
from backend.services.ai_adapter.base import BaseAIAdapter

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    if match:
        return match.group(1)
    return text.strip()


def _parse_response(raw: str) -> dict:
    cleaned = _strip_fences(raw)
    if not cleaned:
        raise ValueError("Empty response from adapter")
    return json.loads(cleaned)


class SpecAgent(BaseAgent):
    def __init__(
        self,
        adapter: BaseAIAdapter,
        model: str = "qwen2.5-coder:7b",
        directive: str = "",
    ) -> None:
        super().__init__(name="spec", directive=directive)
        self.adapter = adapter
        self.model = model

    async def run(
        self,
        user_text: str,
        roi: dict | None = None,
        directive: str | None = None,
        **kwargs,
    ) -> AgentResult:
        effective_directive = directive if directive is not None else self.directive

        system_prompt, user_prompt = build_spec_prompt(
            user_text=user_text,
            roi=roi,
            directive=effective_directive or None,
        )

        start = time.monotonic()
        try:
            raw = await self.adapter.generate_text(
                user_prompt,
                self.model,
                system_prompt=system_prompt,
            )
            data = _parse_response(raw)
        except TimeoutError as exc:
            elapsed = (time.monotonic() - start) * 1000
            self._log("error", "SpecAgent timeout", error=str(exc))
            return AgentResult(
                status="error",
                data={},
                error_message=f"timeout: {exc}",
                execution_time_ms=elapsed,
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            self._log("error", "SpecAgent failed", error=str(exc))
            return AgentResult(
                status="error",
                data={},
                error_message=str(exc),
                execution_time_ms=elapsed,
            )

        elapsed = (time.monotonic() - start) * 1000
        self._log("info", "SpecAgent completed", mode=data.get("mode"))
        return AgentResult(
            status="success",
            data=data,
            error_message=None,
            execution_time_ms=elapsed,
        )
