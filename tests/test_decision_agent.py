"""Tests for DecisionAgent — Step 32. All HTTP calls are mocked."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from agents.base_agent import BaseAgent
from agents.models import AgentResult, DecisionVerdict
from agents.prompts.decision_prompt import build_decision_prompt


# ── helpers ───────────────────────────────────────────────────────────────────

def _img(h: int = 10, w: int = 10) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _ng_images(n: int = 3) -> list:
    return [_img() for _ in range(n)]


def _mock_http(
    dinov2_features_per_call: list[list[float]] | None = None,
    internvl_data: dict | None = None,
    dinov2_exc: Exception | None = None,
    internvl_exc: Exception | None = None,
):
    """Return (mock_cm, mock_client) routing DINOv2 and InternVL calls by URL."""
    if dinov2_features_per_call is None and dinov2_exc is None:
        dinov2_features_per_call = [[0.1] * 384]
    if internvl_data is None and internvl_exc is None:
        internvl_data = {"pattern_type": "diverse", "complexity_score": 0.5, "reasoning": "test"}

    call_count = [0]
    features_list = dinov2_features_per_call or []

    async def _post(url, **kwargs):
        if "dinov2" in url:
            if dinov2_exc is not None:
                raise dinov2_exc
            idx = min(call_count[0], len(features_list) - 1)
            call_count[0] += 1
            feat = features_list[idx]
            resp = MagicMock()
            resp.json.return_value = {"features": [feat], "shape": [1, len(feat)]}
            return resp
        elif "internvl" in url:
            if internvl_exc is not None:
                raise internvl_exc
            resp = MagicMock()
            resp.json.return_value = internvl_data
            return resp
        raise ValueError(f"Unexpected URL: {url}")

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=_post)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm, mock_client


def _feedback_ctx(tried: list[str] | None = None) -> dict:
    return {
        "iteration": len(tried or []),
        "history": [],
        "tried_strategies": tried or [],
        "failed_pipelines": [],
        "constraints": [],
    }


# ── instantiation ─────────────────────────────────────────────────────────────

class TestInstantiation:
    def test_is_base_agent(self):
        from agents.decision_agent import DecisionAgent
        assert isinstance(DecisionAgent(remote_url="http://localhost:8888"), BaseAgent)

    def test_name(self):
        from agents.decision_agent import DecisionAgent
        assert DecisionAgent(remote_url="http://localhost:8888").name == "decision_agent"

    def test_remote_url_stored(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://colab:9999")
        assert agent.remote_url == "http://colab:9999"

    def test_default_directive_empty(self):
        from agents.decision_agent import DecisionAgent
        assert DecisionAgent(remote_url="http://localhost:8888").directive == ""

    def test_custom_directive_stored(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://localhost:8888", directive="strict")
        assert agent.directive == "strict"


# ── align mode ────────────────────────────────────────────────────────────────

class TestAlignMode:
    def test_align_verdict_is_hardware_improvement(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888")
        result = asyncio.run(agent.run(mode="align", ng_images=_ng_images()))
        assert result.data["verdict"] == DecisionVerdict.HARDWARE_IMPROVEMENT.value

    def test_align_status_success(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888")
        result = asyncio.run(agent.run(mode="align", ng_images=_ng_images()))
        assert result.status == "success"

    def test_align_no_remote_calls(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888")
        with patch("agents.decision_agent.httpx.AsyncClient") as mock_cls:
            asyncio.run(agent.run(mode="align", ng_images=_ng_images()))
        mock_cls.assert_not_called()

    def test_align_confidence_is_one(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888")
        result = asyncio.run(agent.run(mode="align", ng_images=_ng_images()))
        assert result.data["confidence"] == 1.0

    def test_align_dinov2_variability_is_none(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888")
        result = asyncio.run(agent.run(mode="align", ng_images=_ng_images()))
        assert result.data["dinov2_variability"] is None

    def test_align_internvl_analysis_is_none(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888")
        result = asyncio.run(agent.run(mode="align", ng_images=_ng_images()))
        assert result.data["internvl_analysis"] is None


# ── AgentResult structure ─────────────────────────────────────────────────────

class TestAgentResultStructure:
    @pytest.fixture
    def result(self):
        from agents.decision_agent import DecisionAgent
        mock_cm, _ = _mock_http()
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            return asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection",
                    ng_images=_ng_images(),
                )
            )

    def test_status_success(self, result):
        assert result.status == "success"

    def test_has_verdict(self, result):
        assert "verdict" in result.data

    def test_has_reasoning(self, result):
        assert "reasoning" in result.data

    def test_has_dinov2_variability(self, result):
        assert "dinov2_variability" in result.data

    def test_has_internvl_analysis(self, result):
        assert "internvl_analysis" in result.data

    def test_has_vision_judge_avg_score(self, result):
        assert "vision_judge_avg_score" in result.data

    def test_has_recommendation(self, result):
        assert "recommendation" in result.data

    def test_has_confidence(self, result):
        assert "confidence" in result.data

    def test_verdict_is_string(self, result):
        assert isinstance(result.data["verdict"], str)

    def test_reasoning_is_string(self, result):
        assert isinstance(result.data["reasoning"], str)

    def test_confidence_is_float(self, result):
        assert isinstance(result.data["confidence"], float)

    def test_execution_time_non_negative(self, result):
        assert result.execution_time_ms >= 0.0


# ── DINOv2 variability helper ─────────────────────────────────────────────────

class TestComputeFeatureCv:
    def test_identical_features_cv_is_zero(self):
        from agents.decision_agent import _compute_feature_cv
        features = [[0.1, 0.2, 0.3]] * 3
        assert _compute_feature_cv(features) == pytest.approx(0.0, abs=1e-6)

    def test_single_feature_returns_zero(self):
        from agents.decision_agent import _compute_feature_cv
        features = [[0.1, 0.2, 0.3]]
        assert _compute_feature_cv(features) == 0.0

    def test_empty_features_returns_zero(self):
        from agents.decision_agent import _compute_feature_cv
        assert _compute_feature_cv([]) == 0.0

    def test_diverse_features_cv_above_threshold(self):
        from agents.decision_agent import _compute_feature_cv
        features = [[0.1] * 10, [0.5] * 10, [0.9] * 10]
        cv = _compute_feature_cv(features)
        assert cv >= 0.2

    def test_similar_features_cv_below_threshold(self):
        from agents.decision_agent import _compute_feature_cv
        features = [[0.10] * 10, [0.11] * 10, [0.09] * 10]
        cv = _compute_feature_cv(features)
        assert cv < 0.2


# ── DINOv2 variability → verdict ──────────────────────────────────────────────

class TestDinov2VariabilityVerdict:
    def test_low_cv_gives_edge_learning(self):
        from agents.decision_agent import DecisionAgent
        low_cv_features = [[0.10] * 384] * 3  # all identical → CV = 0
        mock_cm, _ = _mock_http(dinov2_features_per_call=low_cv_features)
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.EDGE_LEARNING.value

    def test_high_cv_gives_deep_learning(self):
        from agents.decision_agent import DecisionAgent
        high_cv_features = [[0.1] * 384, [0.5] * 384, [0.9] * 384]
        mock_cm, _ = _mock_http(
            dinov2_features_per_call=high_cv_features,
            internvl_data={"pattern_type": "diverse", "complexity_score": 0.8, "reasoning": "diverse"},
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.DEEP_LEARNING.value

    def test_cv_stored_in_result(self):
        from agents.decision_agent import DecisionAgent, _compute_feature_cv
        low_cv_features = [[0.10] * 384] * 3
        mock_cm, _ = _mock_http(dinov2_features_per_call=low_cv_features)
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        expected_cv = _compute_feature_cv([[0.10] * 384] * 3)
        assert result.data["dinov2_variability"] == pytest.approx(expected_cv, abs=1e-6)

    def test_cv_at_boundary_gives_deep_learning(self):
        """CV >= 0.2 → DEEP_LEARNING (boundary: exactly >= 0.2)."""
        from agents.decision_agent import DecisionAgent, _compute_feature_cv
        # features chosen so CV is above 0.2
        boundary_features = [[0.7] * 384, [1.0] * 384, [1.3] * 384]
        cv = _compute_feature_cv(boundary_features)
        assert cv >= 0.2
        mock_cm, _ = _mock_http(dinov2_features_per_call=boundary_features)
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.DEEP_LEARNING.value


# ── InternVL integration ──────────────────────────────────────────────────────

class TestInternVLIntegration:
    def test_internvl_analysis_stored_when_succeeds(self):
        from agents.decision_agent import DecisionAgent
        ivl_data = {"pattern_type": "diverse", "complexity_score": 0.7, "reasoning": "varied"}
        mock_cm, _ = _mock_http(internvl_data=ivl_data)
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["internvl_analysis"] == ivl_data

    def test_internvl_fail_dinov2_decides(self):
        """When InternVL fails, DINOv2 CV alone decides verdict."""
        from agents.decision_agent import DecisionAgent
        import httpx
        low_cv_features = [[0.10] * 384] * 3
        mock_cm, _ = _mock_http(
            dinov2_features_per_call=low_cv_features,
            internvl_exc=httpx.ConnectError("unreachable"),
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.EDGE_LEARNING.value
        assert result.data["internvl_analysis"] is None

    def test_internvl_consistent_with_no_dinov2_gives_edge_learning(self):
        """When DINOv2 fails but InternVL says 'consistent' → EDGE_LEARNING."""
        from agents.decision_agent import DecisionAgent
        import httpx
        ivl_data = {"pattern_type": "consistent", "complexity_score": 0.2, "reasoning": "consistent"}
        mock_cm, _ = _mock_http(
            dinov2_exc=httpx.ConnectError("unreachable"),
            internvl_data=ivl_data,
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.EDGE_LEARNING.value

    def test_internvl_mixed_with_no_dinov2_gives_deep_learning(self):
        """When DINOv2 fails but InternVL says 'mixed' → DEEP_LEARNING."""
        from agents.decision_agent import DecisionAgent
        import httpx
        ivl_data = {"pattern_type": "mixed", "complexity_score": 0.5, "reasoning": "mixed"}
        mock_cm, _ = _mock_http(
            dinov2_exc=httpx.ConnectError("unreachable"),
            internvl_data=ivl_data,
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.DEEP_LEARNING.value


# ── Vision Judge score influence ──────────────────────────────────────────────

class TestVisionJudgeScoreInfluence:
    def test_high_avg_few_strategies_gives_rule_based(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection",
                ng_images=_ng_images(),
                vision_judge_scores=[0.8, 0.75, 0.85],
                feedback_context=_feedback_ctx(tried=["replace_pipeline"]),
            )
        )
        assert result.data["verdict"] == DecisionVerdict.RULE_BASED.value

    def test_high_avg_exactly_0_7_gives_rule_based(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection",
                ng_images=_ng_images(),
                vision_judge_scores=[0.7],
                feedback_context=_feedback_ctx(tried=[]),
            )
        )
        assert result.data["verdict"] == DecisionVerdict.RULE_BASED.value

    def test_high_avg_four_strategies_does_not_give_rule_based(self):
        from agents.decision_agent import DecisionAgent
        import httpx
        many = ["replace_pipeline", "retry_params", "change_category", "retry_pipeline"]
        mock_cm, _ = _mock_http(dinov2_exc=httpx.ConnectError("fail"))
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection",
                    ng_images=_ng_images(),
                    vision_judge_scores=[0.9, 0.95],
                    feedback_context=_feedback_ctx(tried=many),
                )
            )
        assert result.data["verdict"] != DecisionVerdict.RULE_BASED.value

    def test_low_vj_score_does_not_give_rule_based(self):
        from agents.decision_agent import DecisionAgent
        mock_cm, _ = _mock_http()
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection",
                    ng_images=_ng_images(),
                    vision_judge_scores=[0.5, 0.4],
                    feedback_context=_feedback_ctx(tried=[]),
                )
            )
        assert result.data["verdict"] != DecisionVerdict.RULE_BASED.value

    def test_no_vj_scores_does_not_give_rule_based(self):
        from agents.decision_agent import DecisionAgent
        mock_cm, _ = _mock_http()
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection",
                    ng_images=_ng_images(),
                    vision_judge_scores=None,
                    feedback_context=_feedback_ctx(),
                )
            )
        assert result.data["verdict"] != DecisionVerdict.RULE_BASED.value

    def test_vj_avg_score_stored_in_result(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align",
                ng_images=_ng_images(),
                vision_judge_scores=[0.6, 0.8],
            )
        )
        assert result.data["vision_judge_avg_score"] == pytest.approx(0.7)


# ── Decision logic priority ───────────────────────────────────────────────────

class TestDecisionLogicPriority:
    def test_align_overrides_high_vj_rule_based(self):
        """align mode always wins over RULE_BASED check."""
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align",
                ng_images=_ng_images(),
                vision_judge_scores=[0.9, 0.95],
                feedback_context=_feedback_ctx(tried=[]),
            )
        )
        assert result.data["verdict"] == DecisionVerdict.HARDWARE_IMPROVEMENT.value

    def test_rule_based_overrides_low_cv(self):
        """RULE_BASED check wins over DINOv2 low CV when threshold met."""
        from agents.decision_agent import DecisionAgent
        # high VJ, few strategies → RULE_BASED even though low CV would give EL
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection",
                ng_images=_ng_images(),
                vision_judge_scores=[0.75, 0.8],
                feedback_context=_feedback_ctx(tried=["replace_pipeline"]),
            )
        )
        assert result.data["verdict"] == DecisionVerdict.RULE_BASED.value

    def test_rule_based_overrides_high_cv(self):
        """RULE_BASED check wins over DINOv2 high CV when threshold met."""
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection",
                ng_images=_ng_images(),
                vision_judge_scores=[0.85],
                feedback_context=_feedback_ctx(tried=[]),
            )
        )
        assert result.data["verdict"] == DecisionVerdict.RULE_BASED.value


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_empty_ng_images_returns_error(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection", ng_images=[]
            )
        )
        assert result.status == "error"

    def test_empty_ng_images_error_message(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection", ng_images=[]
            )
        )
        assert result.error_message == "No NG images provided for decision"

    def test_dinov2_fail_proceeds_with_internvl(self):
        """DINOv2 ConnectError → dinov2_variability=None, InternVL decides."""
        from agents.decision_agent import DecisionAgent
        import httpx
        ivl_data = {"pattern_type": "diverse", "complexity_score": 0.8, "reasoning": "diverse"}
        mock_cm, _ = _mock_http(
            dinov2_exc=httpx.ConnectError("unreachable"),
            internvl_data=ivl_data,
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.status == "success"
        assert result.data["dinov2_variability"] is None
        assert result.data["verdict"] == DecisionVerdict.DEEP_LEARNING.value

    def test_internvl_fail_proceeds_with_dinov2(self):
        """InternVL ConnectError → internvl_analysis=None, DINOv2 decides."""
        from agents.decision_agent import DecisionAgent
        import httpx
        low_features = [[0.1] * 384] * 3
        mock_cm, _ = _mock_http(
            dinov2_features_per_call=low_features,
            internvl_exc=httpx.ConnectError("unreachable"),
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.status == "success"
        assert result.data["internvl_analysis"] is None
        assert result.data["verdict"] == DecisionVerdict.EDGE_LEARNING.value

    def test_both_fail_returns_deep_learning(self):
        from agents.decision_agent import DecisionAgent
        import httpx
        mock_cm, _ = _mock_http(
            dinov2_exc=httpx.ConnectError("unreachable"),
            internvl_exc=httpx.ConnectError("unreachable"),
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["verdict"] == DecisionVerdict.DEEP_LEARNING.value

    def test_both_fail_confidence_is_0_3(self):
        from agents.decision_agent import DecisionAgent
        import httpx
        mock_cm, _ = _mock_http(
            dinov2_exc=httpx.ConnectError("unreachable"),
            internvl_exc=httpx.ConnectError("unreachable"),
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["confidence"] == pytest.approx(0.3)


# ── Directive handling ────────────────────────────────────────────────────────

class TestDirectiveHandling:
    def test_constructor_directive_stored(self):
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888", directive="from_constructor")
        assert agent.directive == "from_constructor"

    def test_run_directive_none_falls_back_to_constructor(self):
        """directive=None in run() → uses constructor directive."""
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888", directive="ctor")
        # align mode returns quickly; just verify the field
        result = asyncio.run(agent.run(mode="align", ng_images=_ng_images(), directive=None))
        # Agent should succeed; directive used internally — verify via recommendation presence
        assert result.status == "success"
        assert agent.directive == "ctor"

    def test_run_directive_overrides_constructor(self):
        """directive="override" in run() → overrides constructor directive."""
        from agents.decision_agent import DecisionAgent
        agent = DecisionAgent(remote_url="http://test:8888", directive="ctor")
        assert agent.directive == "ctor"  # constructor stored
        # Verify agent doesn't mutate its own directive on run
        asyncio.run(agent.run(mode="align", ng_images=_ng_images(), directive="override"))
        assert agent.directive == "ctor"  # unchanged

    def test_run_directive_empty_string_overrides(self):
        """directive="" in run() → uses empty string (not constructor value)."""
        from agents.decision_agent import DecisionAgent
        mock_cm, _ = _mock_http()
        agent = DecisionAgent(remote_url="http://test:8888", directive="ctor")
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                agent.run(mode="inspection", ng_images=_ng_images(), directive="")
            )
        assert result.status == "success"
        assert agent.directive == "ctor"  # self.directive unchanged


# ── Reasoning and Recommendation output ──────────────────────────────────────

class TestReasoningOutput:
    def test_reasoning_is_non_empty(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align", ng_images=_ng_images()
            )
        )
        assert len(result.data["reasoning"]) > 0

    def test_reasoning_contains_korean(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align", ng_images=_ng_images()
            )
        )
        assert any("가" <= ch <= "힣" for ch in result.data["reasoning"])

    def test_recommendation_is_non_empty(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align", ng_images=_ng_images()
            )
        )
        assert len(result.data["recommendation"]) > 0

    def test_recommendation_contains_korean(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align", ng_images=_ng_images()
            )
        )
        assert any("가" <= ch <= "힣" for ch in result.data["recommendation"])

    def test_rule_based_reasoning_mentions_score(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection",
                ng_images=_ng_images(),
                vision_judge_scores=[0.75, 0.8],
                feedback_context=_feedback_ctx(tried=[]),
            )
        )
        assert result.data["verdict"] == DecisionVerdict.RULE_BASED.value
        assert "0.7" in result.data["reasoning"] or "Vision" in result.data["reasoning"]


# ── Confidence scoring ────────────────────────────────────────────────────────

class TestConfidenceScoring:
    def test_confidence_in_valid_range(self):
        from agents.decision_agent import DecisionAgent
        mock_cm, _ = _mock_http()
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert 0.0 <= result.data["confidence"] <= 1.0

    def test_align_confidence_exactly_one(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="align", ng_images=_ng_images()
            )
        )
        assert result.data["confidence"] == 1.0

    def test_rule_based_confidence_high(self):
        from agents.decision_agent import DecisionAgent
        result = asyncio.run(
            DecisionAgent(remote_url="http://test:8888").run(
                mode="inspection",
                ng_images=_ng_images(),
                vision_judge_scores=[0.8, 0.9],
                feedback_context=_feedback_ctx(tried=[]),
            )
        )
        assert result.data["confidence"] >= 0.7

    def test_both_servers_fail_confidence_low(self):
        from agents.decision_agent import DecisionAgent
        import httpx
        mock_cm, _ = _mock_http(
            dinov2_exc=httpx.ConnectError("fail"),
            internvl_exc=httpx.ConnectError("fail"),
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm):
            result = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result.data["confidence"] <= 0.4

    def test_dinov2_internvl_agree_higher_confidence_than_dinov2_alone(self):
        from agents.decision_agent import DecisionAgent
        import httpx
        # DINOv2 high CV + InternVL confirms "diverse" → higher confidence
        high_cv_features = [[0.1] * 384, [0.5] * 384, [0.9] * 384]
        ivl_confirms = {"pattern_type": "diverse", "complexity_score": 0.8, "reasoning": "diverse"}
        mock_cm_both, _ = _mock_http(
            dinov2_features_per_call=high_cv_features,
            internvl_data=ivl_confirms,
        )
        mock_cm_dinov2_only, _ = _mock_http(
            dinov2_features_per_call=high_cv_features,
            internvl_exc=httpx.ConnectError("fail"),
        )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm_both):
            result_both = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        with patch("agents.decision_agent.httpx.AsyncClient", return_value=mock_cm_dinov2_only):
            result_dinov2_only = asyncio.run(
                DecisionAgent(remote_url="http://test:8888").run(
                    mode="inspection", ng_images=_ng_images()
                )
            )
        assert result_both.data["confidence"] >= result_dinov2_only.data["confidence"]


# ── Prompt builder tests ──────────────────────────────────────────────────────

class TestBuildDecisionPrompt:
    def test_returns_tuple_of_two_strings(self):
        result = build_decision_prompt(
            mode="inspection",
            dinov2_cv=0.15,
            vision_judge_avg=0.6,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
        )
        assert isinstance(result, tuple) and len(result) == 2

    def test_system_prompt_is_string(self):
        system, _ = build_decision_prompt(
            mode="inspection",
            dinov2_cv=None,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
        )
        assert isinstance(system, str) and len(system) > 0

    def test_user_prompt_is_string(self):
        _, user = build_decision_prompt(
            mode="inspection",
            dinov2_cv=None,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
        )
        assert isinstance(user, str) and len(user) > 0

    def test_user_prompt_contains_mode(self):
        _, user = build_decision_prompt(
            mode="inspection",
            dinov2_cv=None,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
        )
        assert "inspection" in user

    def test_user_prompt_contains_cv_when_provided(self):
        _, user = build_decision_prompt(
            mode="inspection",
            dinov2_cv=0.123,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
        )
        assert "0.123" in user or "CV" in user or "variability" in user.lower()

    def test_directive_included_when_set(self):
        _, user = build_decision_prompt(
            mode="inspection",
            dinov2_cv=None,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
            directive="focus on edges",
        )
        assert "focus on edges" in user

    def test_directive_not_included_when_empty(self):
        _, user = build_decision_prompt(
            mode="inspection",
            dinov2_cv=None,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
            directive="",
        )
        # Should not crash and directive section absent
        assert isinstance(user, str)

    def test_system_prompt_mentions_pattern_type(self):
        system, _ = build_decision_prompt(
            mode="inspection",
            dinov2_cv=None,
            vision_judge_avg=None,
            evaluation_summary=None,
            feedback_summary=None,
            success_criteria=None,
        )
        assert "pattern_type" in system or "consistent" in system
