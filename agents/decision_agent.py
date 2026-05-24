"""DecisionAgent — final verdict when max_iteration is exceeded."""
import base64
import time
from typing import Optional

import cv2
import httpx
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, DecisionVerdict
from agents.prompts.decision_prompt import build_decision_prompt


# ── pure helpers ──────────────────────────────────────────────────────────────

def _compute_feature_cv(all_features: list[list[float]]) -> float:
    """Mean coefficient of variation across feature dimensions.

    CV = std(dim) / (|mean(dim)| + eps) averaged over all D dimensions.
    Returns 0.0 when fewer than 2 samples are available.
    """
    if len(all_features) < 2:
        return 0.0
    matrix = np.array(all_features, dtype=np.float64)  # [N, D]
    mean_per_dim = np.abs(np.mean(matrix, axis=0))
    std_per_dim = np.std(matrix, axis=0)
    cv_per_dim = std_per_dim / (mean_per_dim + 1e-8)
    return float(np.mean(cv_per_dim))


def _avg_scores(scores: list[float] | None) -> float | None:
    if not scores:
        return None
    return float(sum(scores) / len(scores))


def _determine_verdict(
    dinov2_cv: float | None,
    internvl_analysis: dict | None,
) -> DecisionVerdict:
    if dinov2_cv is not None:
        return DecisionVerdict.EDGE_LEARNING if dinov2_cv < 0.2 else DecisionVerdict.DEEP_LEARNING
    if internvl_analysis is not None:
        pattern = internvl_analysis.get("pattern_type", "diverse")
        return DecisionVerdict.EDGE_LEARNING if pattern == "consistent" else DecisionVerdict.DEEP_LEARNING
    return DecisionVerdict.DEEP_LEARNING  # safe default when both fail


def _compute_confidence(
    verdict: DecisionVerdict,
    dinov2_cv: float | None,
    internvl_analysis: dict | None,
) -> float:
    if verdict == DecisionVerdict.HARDWARE_IMPROVEMENT:
        return 1.0
    if verdict == DecisionVerdict.RULE_BASED:
        return 0.8

    has_dinov2 = dinov2_cv is not None
    has_internvl = internvl_analysis is not None

    if not has_dinov2 and not has_internvl:
        return 0.3

    if has_dinov2 and has_internvl:
        pattern = internvl_analysis.get("pattern_type", "")
        el_confirmed = verdict == DecisionVerdict.EDGE_LEARNING and pattern == "consistent"
        dl_confirmed = verdict == DecisionVerdict.DEEP_LEARNING and pattern in ("diverse", "mixed")
        return 0.9 if (el_confirmed or dl_confirmed) else 0.75

    return 0.75 if has_dinov2 else 0.6


def _build_reasoning(
    verdict: DecisionVerdict,
    dinov2_cv: float | None,
    internvl_analysis: dict | None,
    vision_judge_avg: float | None,
) -> str:
    if verdict == DecisionVerdict.HARDWARE_IMPROVEMENT:
        return (
            "정렬(Align) 모드에서는 알고리즘 개선만으로 한계가 있습니다. "
            "카메라 위치, 조명 조건, 렌즈 선택 등 하드웨어 수준의 개선이 필요합니다."
        )
    if verdict == DecisionVerdict.RULE_BASED:
        avg_str = f"{vision_judge_avg:.2f}" if vision_judge_avg is not None else "알 수 없음"
        return (
            f"Vision Judge 평균 점수({avg_str})가 0.7 이상으로 충분한 품질을 보이며, "
            "아직 시도하지 않은 전략이 남아있습니다. 현재 Rule-Based 파이프라인 최적화를 지속합니다."
        )
    if verdict == DecisionVerdict.EDGE_LEARNING:
        cv_str = f"{dinov2_cv:.4f}" if dinov2_cv is not None else "분석 불가"
        ivl_str = ""
        if internvl_analysis:
            ivl_str = f" InternVL 시각 분석 결과 '{internvl_analysis.get('pattern_type', '')}' 패턴이 확인됩니다."
        return (
            f"결함 패턴이 일관되고 반복적입니다 (DINOv2 특징 변동계수: {cv_str}).{ivl_str} "
            "Edge Learning 접근법으로 소수의 학습 샘플로 효과적인 검사가 가능합니다."
        )
    # DEEP_LEARNING
    cv_str = f"{dinov2_cv:.4f}" if dinov2_cv is not None else "분석 불가"
    ivl_str = ""
    if internvl_analysis:
        reasoning_snippet = internvl_analysis.get("reasoning", "")[:50]
        ivl_str = f" InternVL 분석: '{reasoning_snippet}'"
    return (
        f"결함 패턴이 다양하고 불규칙합니다 (DINOv2 특징 변동계수: {cv_str}).{ivl_str} "
        "Deep Learning 모델 구축을 통한 다양한 결함 유형 학습이 필요합니다."
    )


def _build_recommendation(verdict: DecisionVerdict) -> str:
    if verdict == DecisionVerdict.HARDWARE_IMPROVEMENT:
        return (
            "카메라 마운팅 각도와 위치를 점검하고, 조명 균일도와 광원 종류를 최적화하세요. "
            "렌즈 배율과 작업 거리도 재검토가 필요합니다."
        )
    if verdict == DecisionVerdict.RULE_BASED:
        return (
            "현재 Rule-Based 접근법을 유지하며 파라미터 탐색 범위를 확대하거나 "
            "다른 전처리 파이프라인을 시도해보세요."
        )
    if verdict == DecisionVerdict.EDGE_LEARNING:
        return (
            "Edge Learning 알고리즘(예: 이상 탐지 기반 접근법)을 적용하세요. "
            "소수의 양품 샘플만으로 효과적인 검사 모델 구축이 가능합니다."
        )
    return (
        "Deep Learning 기반 검사 시스템을 구축하세요. "
        "다양한 결함 유형별 충분한 학습 데이터를 수집하고 CNN/Transformer 기반 모델을 학습시키세요."
    )


# ── agent ─────────────────────────────────────────────────────────────────────

class DecisionAgent(BaseAgent):
    def __init__(self, remote_url: str, directive: str = "") -> None:
        super().__init__(name="decision_agent", directive=directive)
        self.remote_url = remote_url

    async def run(
        self,
        mode: str,
        ng_images: list[np.ndarray],
        evaluation_result: Optional[AgentResult] = None,
        feedback_context: Optional[dict] = None,
        vision_judge_scores: Optional[list[float]] = None,
        success_criteria: Optional[dict] = None,
        directive: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.perf_counter()
        effective_directive = directive if directive is not None else self.directive

        if not ng_images:
            return AgentResult(
                status="error",
                data={},
                error_message="No NG images provided for decision",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        vision_judge_avg = _avg_scores(vision_judge_scores)

        if mode == "align":
            return AgentResult(
                status="success",
                data={
                    "verdict": DecisionVerdict.HARDWARE_IMPROVEMENT.value,
                    "reasoning": _build_reasoning(
                        DecisionVerdict.HARDWARE_IMPROVEMENT, None, None, vision_judge_avg
                    ),
                    "dinov2_variability": None,
                    "internvl_analysis": None,
                    "vision_judge_avg_score": vision_judge_avg,
                    "recommendation": _build_recommendation(DecisionVerdict.HARDWARE_IMPROVEMENT),
                    "confidence": 1.0,
                },
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        tried_count = (
            len(feedback_context.get("tried_strategies", [])) if feedback_context else 0
        )

        if vision_judge_avg is not None and vision_judge_avg >= 0.7 and tried_count < 4:
            return AgentResult(
                status="success",
                data={
                    "verdict": DecisionVerdict.RULE_BASED.value,
                    "reasoning": _build_reasoning(
                        DecisionVerdict.RULE_BASED, None, None, vision_judge_avg
                    ),
                    "dinov2_variability": None,
                    "internvl_analysis": None,
                    "vision_judge_avg_score": vision_judge_avg,
                    "recommendation": _build_recommendation(DecisionVerdict.RULE_BASED),
                    "confidence": _compute_confidence(DecisionVerdict.RULE_BASED, None, None),
                },
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        eval_summary = evaluation_result.data if evaluation_result else None

        dinov2_cv: Optional[float] = None
        internvl_analysis: Optional[dict] = None

        async with httpx.AsyncClient() as client:
            dinov2_cv = await self._compute_dinov2_cv(client, ng_images)
            internvl_analysis = await self._get_internvl_analysis(
                client, ng_images, mode, dinov2_cv,
                eval_summary, feedback_context, success_criteria, effective_directive,
            )

        verdict = _determine_verdict(dinov2_cv, internvl_analysis)
        confidence = _compute_confidence(verdict, dinov2_cv, internvl_analysis)
        reasoning = _build_reasoning(verdict, dinov2_cv, internvl_analysis, vision_judge_avg)
        recommendation = _build_recommendation(verdict)

        self._log(
            "info", "decision_made",
            verdict=verdict.value, dinov2_cv=dinov2_cv, confidence=confidence,
        )

        return AgentResult(
            status="success",
            data={
                "verdict": verdict.value,
                "reasoning": reasoning,
                "dinov2_variability": dinov2_cv,
                "internvl_analysis": internvl_analysis,
                "vision_judge_avg_score": vision_judge_avg,
                "recommendation": recommendation,
                "confidence": confidence,
            },
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )

    async def _compute_dinov2_cv(
        self,
        client: httpx.AsyncClient,
        ng_images: list[np.ndarray],
    ) -> Optional[float]:
        all_features: list[list[float]] = []
        for img in ng_images:
            try:
                _, jpeg_bytes = cv2.imencode(".jpg", img)
                image_b64 = base64.b64encode(jpeg_bytes.tobytes()).decode("utf-8")
                resp = await client.post(
                    f"{self.remote_url}/dinov2/features",
                    json={"image": image_b64},
                    timeout=60.0,
                )
                raw = resp.json()
                if "features" not in raw:
                    raise ValueError("missing features key")
                features = raw["features"]
                if features:
                    all_features.append(features[0])
            except httpx.ConnectError:
                self._log("warning", "dinov2_server_unreachable", url=self.remote_url)
                return None
            except Exception as exc:
                self._log("warning", "dinov2_call_failed", error=str(exc))
                return None
        return _compute_feature_cv(all_features)

    async def _get_internvl_analysis(
        self,
        client: httpx.AsyncClient,
        ng_images: list[np.ndarray],
        mode: str,
        dinov2_cv: Optional[float],
        evaluation_summary: Optional[dict],
        feedback_summary: Optional[dict],
        success_criteria: Optional[dict],
        directive: str,
    ) -> Optional[dict]:
        images_b64: list[str] = []
        for img in ng_images:
            _, jpeg_bytes = cv2.imencode(".jpg", img)
            images_b64.append(base64.b64encode(jpeg_bytes.tobytes()).decode("utf-8"))

        _, user_prompt = build_decision_prompt(
            mode=mode,
            dinov2_cv=dinov2_cv,
            vision_judge_avg=None,
            evaluation_summary=evaluation_summary,
            feedback_summary=feedback_summary,
            success_criteria=success_criteria,
            directive=directive,
        )

        try:
            resp = await client.post(
                f"{self.remote_url}/internvl/analyze",
                json={"images": images_b64, "prompt": user_prompt},
                timeout=60.0,
            )
            raw = resp.json()
            if "pattern_type" not in raw:
                raise ValueError("missing pattern_type key")
            return raw
        except httpx.ConnectError:
            self._log("warning", "internvl_server_unreachable", url=self.remote_url)
            return None
        except Exception as exc:
            self._log("warning", "internvl_call_failed", error=str(exc))
            return None
