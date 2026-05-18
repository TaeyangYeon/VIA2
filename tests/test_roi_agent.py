"""Tests for ROIAgent — all HTTP calls are mocked, no real server required."""
import base64
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from agents.roi_agent import ROIAgent
from agents.models import AgentResult
from agents.base_agent import BaseAgent


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_image(h: int = 40, w: int = 40, channels: int = 3) -> np.ndarray:
    return np.zeros((h, w, channels), dtype=np.uint8)


def _make_grayscale(h: int = 40, w: int = 40) -> np.ndarray:
    return np.zeros((h, w), dtype=np.uint8)


def _dino_response(boxes=None, scores=None, labels=None) -> dict:
    return {
        "boxes": boxes if boxes is not None else [[5, 5, 25, 25]],
        "scores": scores if scores is not None else [0.85],
        "labels": labels if labels is not None else ["scratch"],
    }


def _sam2_response(masks=None, scores=None) -> dict:
    return {
        "masks": masks if masks is not None else [
            {"bbox": [5, 5, 25, 25], "area": 400, "segmentation_rle": "abc123"}
        ],
        "scores": scores if scores is not None else [0.90],
    }


def _mock_auto(dino_resp: dict, sam2_resp: dict):
    """Return (mock_cm, mock_client) — first post returns dino_resp, second sam2_resp."""
    dino_mock = MagicMock()
    dino_mock.json.return_value = dino_resp

    sam2_mock = MagicMock()
    sam2_mock.json.return_value = sam2_resp

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[dino_mock, sam2_mock])

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_cm, mock_client


def _mock_connect_error():
    """Mock client that raises ConnectError on any post call."""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm


# ── class instantiation ───────────────────────────────────────────────────────

def test_roi_agent_is_base_agent():
    assert isinstance(ROIAgent(remote_url="http://localhost:8080"), BaseAgent)


def test_roi_agent_name_is_roi_agent():
    assert ROIAgent(remote_url="http://localhost:8080").name == "roi_agent"


def test_roi_agent_stores_remote_url():
    agent = ROIAgent(remote_url="http://colab-server:8080")
    assert agent.remote_url == "http://colab-server:8080"


def test_roi_agent_default_directive_empty():
    assert ROIAgent(remote_url="http://localhost:8080").directive == ""


def test_roi_agent_custom_directive_stored():
    agent = ROIAgent(remote_url="http://localhost:8080", directive="focus on defects")
    assert agent.directive == "focus on defects"


# ── error: neither roi nor text_query ────────────────────────────────────────

@pytest.mark.asyncio
async def test_neither_roi_nor_query_status_error():
    result = await ROIAgent(remote_url="http://test:8080").run(image=_make_image())
    assert result.status == "error"


@pytest.mark.asyncio
async def test_neither_roi_nor_query_error_message():
    result = await ROIAgent(remote_url="http://test:8080").run(image=_make_image())
    assert "No ROI or text query provided" in result.error_message


# ── error: image too small ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_image_too_small_with_roi():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=np.zeros((2, 2, 3), dtype=np.uint8),
        roi={"x1": 0, "y1": 0, "x2": 2, "y2": 2},
    )
    assert result.status == "error"
    assert "too small" in result.error_message.lower()


@pytest.mark.asyncio
async def test_image_too_small_with_text_query():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=np.zeros((1, 1, 3), dtype=np.uint8),
        text_query="scratch",
    )
    assert result.status == "error"
    assert "too small" in result.error_message.lower()


# ── manual ROI: valid ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manual_roi_returns_success():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(), roi={"x1": 5, "y1": 5, "x2": 25, "y2": 25}
    )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_manual_roi_mode_is_manual():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(), roi={"x1": 5, "y1": 5, "x2": 25, "y2": 25}
    )
    assert result.data["mode"] == "manual"


@pytest.mark.asyncio
async def test_manual_roi_data_has_roi_key():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(), roi={"x1": 5, "y1": 5, "x2": 25, "y2": 25}
    )
    assert "roi" in result.data


@pytest.mark.asyncio
async def test_manual_roi_data_has_roi_stats_key():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(), roi={"x1": 5, "y1": 5, "x2": 25, "y2": 25}
    )
    assert "roi_stats" in result.data


@pytest.mark.asyncio
async def test_manual_roi_stats_has_area_ratio():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 0, "y1": 0, "x2": 20, "y2": 20}
    )
    assert "area_ratio" in result.data["roi_stats"]


@pytest.mark.asyncio
async def test_manual_roi_stats_has_aspect_ratio():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 0, "y1": 0, "x2": 20, "y2": 20}
    )
    assert "aspect_ratio" in result.data["roi_stats"]


@pytest.mark.asyncio
async def test_manual_roi_area_ratio_correct():
    """20×20 ROI on 40×40 image → 400/1600 = 0.25."""
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 0, "y1": 0, "x2": 20, "y2": 20}
    )
    assert abs(result.data["roi_stats"]["area_ratio"] - 0.25) < 1e-4


@pytest.mark.asyncio
async def test_manual_roi_aspect_ratio_correct():
    """30×10 ROI → w/h = 3.0."""
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 0, "y1": 0, "x2": 30, "y2": 10}
    )
    assert abs(result.data["roi_stats"]["aspect_ratio"] - 3.0) < 1e-4


@pytest.mark.asyncio
async def test_manual_roi_area_ratio_in_range():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 5, "y1": 5, "x2": 35, "y2": 35}
    )
    ratio = result.data["roi_stats"]["area_ratio"]
    assert 0.0 < ratio <= 1.0


@pytest.mark.asyncio
async def test_manual_roi_no_error_message():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(), roi={"x1": 5, "y1": 5, "x2": 25, "y2": 25}
    )
    assert result.error_message is None


@pytest.mark.asyncio
async def test_manual_roi_execution_time_nonnegative():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(), roi={"x1": 5, "y1": 5, "x2": 25, "y2": 25}
    )
    assert result.execution_time_ms >= 0.0


# ── manual ROI: clamping ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manual_roi_out_of_bounds_is_clamped_to_success():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": -10, "y1": -10, "x2": 50, "y2": 50}
    )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_manual_roi_clamped_coordinates_within_image():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": -5, "y1": -5, "x2": 100, "y2": 100}
    )
    clamped = result.data["roi"]
    assert clamped["x1"] == 0
    assert clamped["y1"] == 0
    assert clamped["x2"] == 40
    assert clamped["y2"] == 40


# ── manual ROI: invalid after clamping ───────────────────────────────────────

@pytest.mark.asyncio
async def test_manual_roi_zero_width_after_clamp_is_error():
    """x1=50 x2=60 on 40px-wide image → after clamp x1=x2=40 → zero width → error."""
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 50, "y1": 5, "x2": 60, "y2": 25}
    )
    assert result.status == "error"


@pytest.mark.asyncio
async def test_manual_roi_zero_height_after_clamp_is_error():
    """y1=50 y2=60 on 40px-tall image → zero height after clamp → error."""
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_image(40, 40), roi={"x1": 5, "y1": 50, "x2": 25, "y2": 60}
    )
    assert result.status == "error"


# ── auto mode: Grounding DINO + SAM 2 success ────────────────────────────────

@pytest.mark.asyncio
async def test_auto_mode_returns_success():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_auto_mode_data_mode_is_auto():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.data["mode"] == "auto"


@pytest.mark.asyncio
async def test_auto_mode_data_has_query():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.data["query"] == "scratch"


@pytest.mark.asyncio
async def test_auto_mode_data_has_detections():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert "detections" in result.data


@pytest.mark.asyncio
async def test_auto_mode_detections_count_matches_dino_boxes():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert len(result.data["detections"]) == 1


@pytest.mark.asyncio
async def test_auto_mode_data_has_recommended_roi():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert "recommended_roi" in result.data
    assert result.data["recommended_roi"] is not None


@pytest.mark.asyncio
async def test_auto_mode_recommended_roi_has_correct_keys():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    roi = result.data["recommended_roi"]
    for key in ("x1", "y1", "x2", "y2"):
        assert key in roi, f"recommended_roi missing key: {key}"


@pytest.mark.asyncio
async def test_auto_mode_data_has_masks():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert "masks" in result.data
    assert isinstance(result.data["masks"], list)


@pytest.mark.asyncio
async def test_auto_mode_data_has_confidence():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert "confidence" in result.data
    assert isinstance(result.data["confidence"], float)


@pytest.mark.asyncio
async def test_auto_mode_no_error_message():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.error_message is None


@pytest.mark.asyncio
async def test_auto_mode_execution_time_nonnegative():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.execution_time_ms >= 0.0


# ── remote call verification ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auto_mode_dino_endpoint_called_correctly():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://colab:8080").run(
            image=_make_image(), text_query="hole"
        )
    first_url = mock_client.post.call_args_list[0].args[0]
    assert first_url == "http://colab:8080/grounding_dino/detect"


@pytest.mark.asyncio
async def test_auto_mode_sam2_endpoint_called_correctly():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://colab:8080").run(
            image=_make_image(), text_query="hole"
        )
    second_url = mock_client.post.call_args_list[1].args[0]
    assert second_url == "http://colab:8080/sam2/segment"


@pytest.mark.asyncio
async def test_auto_mode_dino_payload_has_text_query():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    payload = mock_client.post.call_args_list[0].kwargs.get("json", {})
    assert payload.get("text_query") == "scratch"


@pytest.mark.asyncio
async def test_auto_mode_dino_payload_has_threshold_03():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    payload = mock_client.post.call_args_list[0].kwargs.get("json", {})
    assert payload.get("threshold") == 0.3


@pytest.mark.asyncio
async def test_auto_mode_dino_payload_contains_base64_image():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    payload = mock_client.post.call_args_list[0].kwargs.get("json", {})
    assert "image" in payload
    assert len(base64.b64decode(payload["image"])) > 0


@pytest.mark.asyncio
async def test_auto_mode_sam2_payload_boxes_match_dino_output():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    payload = mock_client.post.call_args_list[1].kwargs.get("json", {})
    assert payload.get("boxes") == [[5, 5, 25, 25]]


# ── auto mode: no detections ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auto_no_detections_returns_success():
    dino_empty = {"boxes": [], "scores": [], "labels": []}
    mock_cm, _ = _mock_auto(dino_empty, _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="unknown_thing"
        )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_auto_no_detections_recommended_roi_is_none():
    dino_empty = {"boxes": [], "scores": [], "labels": []}
    mock_cm, _ = _mock_auto(dino_empty, _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="unknown_thing"
        )
    assert result.data["recommended_roi"] is None


@pytest.mark.asyncio
async def test_auto_no_detections_message_contains_query():
    dino_empty = {"boxes": [], "scores": [], "labels": []}
    mock_cm, _ = _mock_auto(dino_empty, _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="unknown_thing"
        )
    assert "unknown_thing" in result.data.get("message", "")


@pytest.mark.asyncio
async def test_auto_no_detections_detections_list_is_empty():
    dino_empty = {"boxes": [], "scores": [], "labels": []}
    mock_cm, _ = _mock_auto(dino_empty, _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="unknown_thing"
        )
    assert result.data["detections"] == []


@pytest.mark.asyncio
async def test_auto_no_detections_sam2_not_called():
    dino_empty = {"boxes": [], "scores": [], "labels": []}
    mock_cm, mock_client = _mock_auto(dino_empty, _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="unknown_thing"
        )
    assert mock_client.post.call_count == 1


# ── auto mode: both roi and text_query → auto takes precedence ────────────────

@pytest.mark.asyncio
async def test_both_roi_and_query_auto_takes_precedence():
    mock_cm, mock_client = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(),
            roi={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
            text_query="scratch",
        )
    assert result.data["mode"] == "auto"
    assert mock_client.post.call_count >= 1


# ── error: Grounding DINO unreachable ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_dino_unreachable_status_error():
    mock_cm = _mock_connect_error()
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://bad:9999").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.status == "error"


@pytest.mark.asyncio
async def test_dino_unreachable_message_contains_url():
    mock_cm = _mock_connect_error()
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://bad:9999").run(
            image=_make_image(), text_query="scratch"
        )
    assert "http://bad:9999" in result.error_message


@pytest.mark.asyncio
async def test_dino_unreachable_message_mentions_grounding_dino():
    mock_cm = _mock_connect_error()
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://bad:9999").run(
            image=_make_image(), text_query="scratch"
        )
    assert "Grounding DINO" in result.error_message


# ── SAM 2 unreachable → partial success ──────────────────────────────────────

@pytest.mark.asyncio
async def test_sam2_unreachable_returns_success():
    dino_mock_resp = MagicMock()
    dino_mock_resp.json.return_value = _dino_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=[dino_mock_resp, httpx.ConnectError("sam2 refused")]
    )
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_sam2_unreachable_recommended_roi_uses_dino_box():
    dino_mock_resp = MagicMock()
    dino_mock_resp.json.return_value = _dino_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=[dino_mock_resp, httpx.ConnectError("sam2 refused")]
    )
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    roi = result.data["recommended_roi"]
    assert roi is not None
    assert roi["x1"] == 5 and roi["y1"] == 5 and roi["x2"] == 25 and roi["y2"] == 25


@pytest.mark.asyncio
async def test_sam2_unreachable_mode_is_auto():
    dino_mock_resp = MagicMock()
    dino_mock_resp.json.return_value = _dino_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(
        side_effect=[dino_mock_resp, httpx.ConnectError("sam2 refused")]
    )
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.data["mode"] == "auto"


# ── error: invalid Grounding DINO response ───────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_dino_response_missing_boxes_key():
    bad_resp = MagicMock()
    bad_resp.json.return_value = {"scores": [0.9]}  # "boxes" key absent
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=bad_resp)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.status == "error"
    assert "Invalid Grounding DINO response format" in result.error_message


# ── partial success: invalid SAM 2 response ───────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_sam2_response_partial_success():
    dino_mock_resp = MagicMock()
    dino_mock_resp.json.return_value = _dino_response()
    sam2_bad_resp = MagicMock()
    sam2_bad_resp.json.return_value = {"scores": [0.9]}  # "masks" key absent

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[dino_mock_resp, sam2_bad_resp])
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_image(), text_query="scratch"
        )
    assert result.status == "success"
    assert result.data["recommended_roi"] is not None  # falls back to DINO box


# ── grayscale input ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grayscale_image_manual_mode_success():
    result = await ROIAgent(remote_url="http://test:8080").run(
        image=_make_grayscale(40, 40), roi={"x1": 0, "y1": 0, "x2": 20, "y2": 20}
    )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_grayscale_image_auto_mode_success():
    mock_cm, _ = _mock_auto(_dino_response(), _sam2_response())
    with patch("agents.roi_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await ROIAgent(remote_url="http://test:8080").run(
            image=_make_grayscale(40, 40), text_query="scratch"
        )
    assert result.status == "success"
