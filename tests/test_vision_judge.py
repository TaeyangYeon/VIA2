"""Tests for VisionJudgeAgent — all HTTP calls are mocked, no real server required."""
import base64
import json
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from agents.vision_judge_agent import VisionJudgeAgent
from agents.models import AgentResult
from agents.base_agent import BaseAgent
from agents.prompts.vision_judge_prompt import build_vision_judge_prompt


# ── helpers ───────────────────────────────────────────────────────────────────

def _good_response() -> dict:
    return {
        "visibility_score": 0.9,
        "separability_score": 0.85,
        "measurability_score": 0.8,
        "problems": [],
        "next_suggestion": "Processing looks good.",
    }


def _bad_response() -> dict:
    return {
        "visibility_score": 0.2,
        "separability_score": 0.15,
        "measurability_score": 0.1,
        "problems": ["low contrast", "noise not removed"],
        "next_suggestion": "Apply edge enhancement.",
    }


def _mock_http(server_response: dict):
    """Return (mock_cm, mock_client) for patching httpx.AsyncClient."""
    raw_text = json.dumps(server_response)
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.status_code = 200
    mock_response.json.return_value = server_response
    mock_response.text = raw_text

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_cm, mock_client


def _bgr(h: int = 20, w: int = 20) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def _gray(h: int = 20, w: int = 20) -> np.ndarray:
    return np.zeros((h, w), dtype=np.uint8)


# ── class instantiation ───────────────────────────────────────────────────────

def test_vision_judge_agent_is_base_agent():
    agent = VisionJudgeAgent(remote_url="http://localhost:8080")
    assert isinstance(agent, BaseAgent)


def test_vision_judge_agent_name():
    agent = VisionJudgeAgent(remote_url="http://localhost:8080")
    assert agent.name == "vision_judge_agent"


def test_vision_judge_agent_stores_remote_url():
    agent = VisionJudgeAgent(remote_url="http://colab-server:8080")
    assert agent.remote_url == "http://colab-server:8080"


def test_vision_judge_agent_default_directive_empty():
    agent = VisionJudgeAgent(remote_url="http://localhost:8080")
    assert agent.directive == ""


def test_vision_judge_agent_custom_directive_stored():
    agent = VisionJudgeAgent(remote_url="http://localhost:8080", directive="focus on edges")
    assert agent.directive == "focus on edges"


# ── AgentResult structure ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_returns_success_status():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect scratches"
        )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_result_has_judgement_key():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect scratches"
        )
    assert "judgement" in result.data


@pytest.mark.asyncio
async def test_run_result_has_raw_response_key():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect scratches"
        )
    assert "raw_response" in result.data


@pytest.mark.asyncio
async def test_run_execution_time_non_negative():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect scratches"
        )
    assert result.execution_time_ms >= 0.0


@pytest.mark.asyncio
async def test_run_success_has_no_error_message():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect scratches"
        )
    assert result.error_message is None


@pytest.mark.asyncio
async def test_run_raw_response_is_string():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect scratches"
        )
    assert isinstance(result.data["raw_response"], str)


# ── JudgementResult fields ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_judgement_has_visibility_score():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert "visibility_score" in result.data["judgement"]


@pytest.mark.asyncio
async def test_judgement_has_separability_score():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert "separability_score" in result.data["judgement"]


@pytest.mark.asyncio
async def test_judgement_has_measurability_score():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert "measurability_score" in result.data["judgement"]


@pytest.mark.asyncio
async def test_judgement_has_overall_score():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert "overall_score" in result.data["judgement"]


@pytest.mark.asyncio
async def test_judgement_has_problems_list():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert isinstance(result.data["judgement"]["problems"], list)


@pytest.mark.asyncio
async def test_judgement_has_next_suggestion_string():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert isinstance(result.data["judgement"]["next_suggestion"], str)


# ── score computation ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_overall_score_weighted_average():
    server_resp = {
        "visibility_score": 0.8,
        "separability_score": 0.6,
        "measurability_score": 0.4,
        "problems": [],
        "next_suggestion": "",
    }
    expected = 0.4 * 0.8 + 0.35 * 0.6 + 0.25 * 0.4
    mock_cm, _ = _mock_http(server_resp)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert abs(result.data["judgement"]["overall_score"] - expected) < 1e-9


@pytest.mark.asyncio
async def test_score_clamping_high_values():
    server_resp = {
        "visibility_score": 1.5,
        "separability_score": 2.0,
        "measurability_score": 1.1,
        "problems": [],
        "next_suggestion": "",
    }
    mock_cm, _ = _mock_http(server_resp)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    j = result.data["judgement"]
    assert j["visibility_score"] == 1.0
    assert j["separability_score"] == 1.0
    assert j["measurability_score"] == 1.0


@pytest.mark.asyncio
async def test_score_clamping_low_values():
    server_resp = {
        "visibility_score": -0.5,
        "separability_score": -1.0,
        "measurability_score": -0.1,
        "problems": [],
        "next_suggestion": "",
    }
    mock_cm, _ = _mock_http(server_resp)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    j = result.data["judgement"]
    assert j["visibility_score"] == 0.0
    assert j["separability_score"] == 0.0
    assert j["measurability_score"] == 0.0


@pytest.mark.asyncio
async def test_overall_score_in_range_0_to_1():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    score = result.data["judgement"]["overall_score"]
    assert 0.0 <= score <= 1.0


# ── good vs bad processing ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_good_processing_high_overall_score():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert result.data["judgement"]["overall_score"] > 0.7


@pytest.mark.asyncio
async def test_bad_processing_low_overall_score():
    mock_cm, _ = _mock_http(_bad_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert result.data["judgement"]["overall_score"] < 0.3


# ── prompt building ───────────────────────────────────────────────────────────

def test_build_vision_judge_prompt_returns_string():
    result = build_vision_judge_prompt("detect corrosion")
    assert isinstance(result, str)


def test_build_vision_judge_prompt_contains_purpose():
    result = build_vision_judge_prompt("detect corrosion on metal surface")
    assert "detect corrosion on metal surface" in result


def test_build_vision_judge_prompt_without_directive_no_directive_text():
    result = build_vision_judge_prompt("detect cracks", directive="")
    assert "Additional evaluation guidance" not in result


def test_build_vision_judge_prompt_with_directive_includes_it():
    result = build_vision_judge_prompt("detect cracks", directive="focus on sharp edges")
    assert "focus on sharp edges" in result


def test_build_vision_judge_prompt_contains_visibility_score_schema():
    result = build_vision_judge_prompt("test purpose")
    assert "visibility_score" in result


def test_build_vision_judge_prompt_contains_full_json_schema():
    result = build_vision_judge_prompt("test purpose")
    assert "separability_score" in result
    assert "measurability_score" in result
    assert "next_suggestion" in result
    assert "problems" in result


# ── remote HTTP call verification ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_posts_to_vision_judge_evaluate_endpoint():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(remote_url="http://colab-server:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    called_url = mock_client.post.call_args.args[0]
    assert called_url == "http://colab-server:8080/vision_judge/evaluate"


@pytest.mark.asyncio
async def test_run_payload_contains_original_image_key():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert "original_image" in payload
    assert len(base64.b64decode(payload["original_image"])) > 0


@pytest.mark.asyncio
async def test_run_payload_contains_processed_image_key():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert "processed_image" in payload
    assert len(base64.b64decode(payload["processed_image"])) > 0


@pytest.mark.asyncio
async def test_run_payload_contains_purpose():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="detect cracks"
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["purpose"] == "detect cracks"


@pytest.mark.asyncio
async def test_run_payload_contains_directive_key():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert "directive" in payload


# ── error handling ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_original_image_too_small():
    agent = VisionJudgeAgent(remote_url="http://test:8080")
    result = await agent.run(
        original_image=np.zeros((2, 2, 3), dtype=np.uint8),
        processed_image=_bgr(),
        purpose="test",
    )
    assert result.status == "error"
    assert "Original image too small" in result.error_message


@pytest.mark.asyncio
async def test_error_processed_image_too_small():
    agent = VisionJudgeAgent(remote_url="http://test:8080")
    result = await agent.run(
        original_image=_bgr(),
        processed_image=np.zeros((2, 2, 3), dtype=np.uint8),
        purpose="test",
    )
    assert result.status == "error"
    assert "Processed image too small" in result.error_message


@pytest.mark.asyncio
async def test_error_server_unreachable_status():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://unreachable:9999").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert result.status == "error"


@pytest.mark.asyncio
async def test_error_server_unreachable_message_contains_url():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://unreachable:9999").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert "http://unreachable:9999" in result.error_message


@pytest.mark.asyncio
async def test_error_invalid_response_missing_key():
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"visibility_score": 0.8}  # missing keys
    mock_response.text = '{"visibility_score": 0.8}'
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert result.status == "error"
    assert "Invalid Vision Judge response format" in result.error_message


@pytest.mark.asyncio
async def test_error_http_error_status():
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 500
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert result.status == "error"


@pytest.mark.asyncio
async def test_error_http_error_message_contains_status_code():
    mock_response = MagicMock()
    mock_response.is_success = False
    mock_response.status_code = 503
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose="test"
        )
    assert "503" in result.error_message


# ── grayscale input ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grayscale_images_handled_successfully():
    mock_cm, _ = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_gray(),
            processed_image=_gray(),
            purpose="test",
        )
    assert result.status == "success"


# ── directive handling ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_directive_override_uses_run_directive():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(
            remote_url="http://test:8080", directive="constructor directive"
        ).run(
            original_image=_bgr(),
            processed_image=_bgr(),
            purpose="test",
            directive="run directive",
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["directive"] == "run directive"


@pytest.mark.asyncio
async def test_run_no_directive_override_uses_constructor_directive():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(
            remote_url="http://test:8080", directive="constructor directive"
        ).run(
            original_image=_bgr(),
            processed_image=_bgr(),
            purpose="test",
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["directive"] == "constructor directive"


@pytest.mark.asyncio
async def test_run_directive_none_falls_back_to_constructor():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        await VisionJudgeAgent(remote_url="http://test:8080", directive="default").run(
            original_image=_bgr(),
            processed_image=_bgr(),
            purpose="test",
            directive=None,
        )
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["directive"] == "default"


# ── edge cases ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_same_image_as_original_and_processed():
    mock_cm, _ = _mock_http(_good_response())
    img = _bgr()
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=img, processed_image=img, purpose="test"
        )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_empty_purpose_string():
    mock_cm, mock_client = _mock_http(_good_response())
    with patch("agents.vision_judge_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await VisionJudgeAgent(remote_url="http://test:8080").run(
            original_image=_bgr(), processed_image=_bgr(), purpose=""
        )
    assert result.status == "success"
    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["purpose"] == ""
