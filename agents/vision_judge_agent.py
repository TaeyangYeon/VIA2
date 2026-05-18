"""VisionJudgeAgent — remote HTTP client for Qwen2.5-VL vision quality evaluation."""
import base64
import time
from dataclasses import asdict

import cv2
import httpx
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, JudgementResult
from agents.prompts.vision_judge_prompt import build_vision_judge_prompt


class VisionJudgeAgent(BaseAgent):
    def __init__(self, remote_url: str, directive: str = "") -> None:
        super().__init__(name="vision_judge_agent", directive=directive)
        self.remote_url = remote_url

    async def run(
        self,
        original_image: np.ndarray,
        processed_image: np.ndarray,
        purpose: str,
        directive: str | None = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.perf_counter()

        h_o, w_o = original_image.shape[:2]
        if h_o < 3 or w_o < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="Original image too small for vision judge",
            )

        h_p, w_p = processed_image.shape[:2]
        if h_p < 3 or w_p < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="Processed image too small for vision judge",
            )

        effective_directive = directive if directive is not None else self.directive

        orig_bgr = _to_bgr(original_image)
        proc_bgr = _to_bgr(processed_image)
        _, orig_bytes = cv2.imencode(".jpg", orig_bgr)
        _, proc_bytes = cv2.imencode(".jpg", proc_bgr)
        orig_b64 = base64.b64encode(orig_bytes.tobytes()).decode("utf-8")
        proc_b64 = base64.b64encode(proc_bytes.tobytes()).decode("utf-8")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.remote_url}/vision_judge/evaluate",
                    json={
                        "original_image": orig_b64,
                        "processed_image": proc_b64,
                        "purpose": purpose,
                        "directive": effective_directive,
                    },
                    timeout=60.0,
                )
        except httpx.ConnectError:
            return AgentResult(
                status="error",
                data={},
                error_message=f"Vision Judge server unreachable: {self.remote_url}",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )
        except Exception:
            return AgentResult(
                status="error",
                data={},
                error_message=f"Vision Judge server unreachable: {self.remote_url}",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        if not response.is_success:
            return AgentResult(
                status="error",
                data={},
                error_message=f"Vision Judge server error: {response.status_code}",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        try:
            raw = response.json()
            vis = _clamp(float(raw["visibility_score"]))
            sep = _clamp(float(raw["separability_score"]))
            meas = _clamp(float(raw["measurability_score"]))
            problems = list(raw["problems"])
            next_sug = str(raw["next_suggestion"])
        except Exception:
            return AgentResult(
                status="error",
                data={},
                error_message="Invalid Vision Judge response format",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        overall = 0.4 * vis + 0.35 * sep + 0.25 * meas

        judgement = JudgementResult(
            visibility_score=vis,
            separability_score=sep,
            measurability_score=meas,
            overall_score=overall,
            problems=problems,
            next_suggestion=next_sug,
        )

        return AgentResult(
            status="success",
            data={"judgement": asdict(judgement), "raw_response": response.text},
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_bgr(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image
