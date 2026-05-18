"""Tests for DepthAgent — all HTTP calls are mocked, no real server required."""
import base64
import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from agents.depth_agent import DepthAgent
from agents.models import AgentResult
from agents.base_agent import BaseAgent


# ── synthetic depth map helpers ──────────────────────────────────────────────

def _encode_depth_response(depth_map: np.ndarray) -> dict:
    """Encode depth map as the remote server would return it."""
    d = depth_map.astype(np.float32)
    return {"depth_map": base64.b64encode(d.tobytes()).decode(), "shape": list(d.shape)}


def _flat_depth(h: int = 20, w: int = 20, value: float = 0.5) -> np.ndarray:
    return np.full((h, w), value, dtype=np.float32)


def _gradient_depth(h: int = 20, w: int = 20) -> np.ndarray:
    row = np.linspace(0.0, 1.0, w, dtype=np.float32)
    return np.tile(row, (h, 1))


def _step_depth(h: int = 20, w: int = 20) -> np.ndarray:
    """Left half=0.0, right half=1.0 — steep gradient at the boundary."""
    d = np.zeros((h, w), dtype=np.float32)
    d[:, w // 2 :] = 1.0
    return d


def _mock_http(depth_map: np.ndarray):
    """Return (mock_cm, mock_client) for patching httpx.AsyncClient."""
    mock_response = MagicMock()
    mock_response.json.return_value = _encode_depth_response(depth_map)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_cm, mock_client


# ── class instantiation ──────────────────────────────────────────────────────

def test_depth_agent_is_base_agent():
    agent = DepthAgent(remote_url="http://localhost:8080")
    assert isinstance(agent, BaseAgent)


def test_depth_agent_name_is_depth_agent():
    agent = DepthAgent(remote_url="http://localhost:8080")
    assert agent.name == "depth_agent"


def test_depth_agent_stores_remote_url():
    agent = DepthAgent(remote_url="http://colab-server:8080")
    assert agent.remote_url == "http://colab-server:8080"


def test_depth_agent_default_directive_is_empty():
    agent = DepthAgent(remote_url="http://localhost:8080")
    assert agent.directive == ""


def test_depth_agent_custom_directive_stored():
    agent = DepthAgent(remote_url="http://localhost:8080", directive="focus on shadows")
    assert agent.directive == "focus on shadows"


# ── AgentResult structure ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_returns_success_status():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_result_has_depth_map_key():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert "depth_map" in result.data


@pytest.mark.asyncio
async def test_run_result_has_depth_stats_key():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert "depth_stats" in result.data


@pytest.mark.asyncio
async def test_run_result_depth_map_is_ndarray():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert isinstance(result.data["depth_map"], np.ndarray)


@pytest.mark.asyncio
async def test_run_execution_time_non_negative():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.execution_time_ms >= 0.0


@pytest.mark.asyncio
async def test_run_success_has_no_error_message():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.error_message is None


# ── depth_stats required fields ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_depth_stats_has_all_required_fields():
    mock_cm, _ = _mock_http(_gradient_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    stats = result.data["depth_stats"]
    for key in ("depth_complexity", "has_shadow_region", "depth_range", "depth_mean", "depth_gradient_max"):
        assert key in stats, f"Missing depth_stats key: {key}"


# ── depth_complexity ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_depth_complexity_in_range_0_to_1():
    mock_cm, _ = _mock_http(_gradient_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    dc = result.data["depth_stats"]["depth_complexity"]
    assert 0.0 <= dc <= 1.0


@pytest.mark.asyncio
async def test_depth_complexity_flat_map_is_near_zero():
    mock_cm, _ = _mock_http(_flat_depth(value=0.5))
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["depth_complexity"] < 0.05


@pytest.mark.asyncio
async def test_depth_complexity_step_map_is_high():
    mock_cm, _ = _mock_http(_step_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["depth_complexity"] > 0.8


# ── has_shadow_region ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_has_shadow_region_false_for_flat_depth():
    mock_cm, _ = _mock_http(_flat_depth(value=0.5))
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["has_shadow_region"] is False


@pytest.mark.asyncio
async def test_has_shadow_region_true_for_step_edge():
    mock_cm, _ = _mock_http(_step_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["has_shadow_region"] is True


# ── depth_range ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_depth_range_is_one_for_step_map():
    mock_cm, _ = _mock_http(_step_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert abs(result.data["depth_stats"]["depth_range"] - 1.0) < 1e-4


@pytest.mark.asyncio
async def test_depth_range_is_zero_for_flat_map():
    mock_cm, _ = _mock_http(_flat_depth(value=0.5))
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["depth_range"] < 1e-4


# ── depth_mean ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_depth_mean_correct_for_flat_07():
    mock_cm, _ = _mock_http(_flat_depth(value=0.7))
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert abs(result.data["depth_stats"]["depth_mean"] - 0.7) < 1e-4


@pytest.mark.asyncio
async def test_depth_mean_half_for_step_map():
    mock_cm, _ = _mock_http(_step_depth(h=20, w=20))
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert abs(result.data["depth_stats"]["depth_mean"] - 0.5) < 1e-4


# ── depth_gradient_max ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_depth_gradient_max_nonzero_for_gradient_map():
    mock_cm, _ = _mock_http(_gradient_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["depth_gradient_max"] > 0.0


@pytest.mark.asyncio
async def test_depth_gradient_max_near_zero_for_flat():
    mock_cm, _ = _mock_http(_flat_depth(value=0.5))
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.data["depth_stats"]["depth_gradient_max"] < 1e-4


# ── ROI cropping ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_roi_left_half_of_step_map_has_zero_mean():
    """Step map: left half=0, right half=1. ROI on left region → mean ≈ 0."""
    mock_cm, _ = _mock_http(_step_depth(h=20, w=20))
    roi = {"x1": 0, "y1": 0, "x2": 8, "y2": 20}
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8), roi=roi
        )
    assert result.data["depth_stats"]["depth_mean"] < 0.05


@pytest.mark.asyncio
async def test_roi_right_half_of_step_map_has_one_mean():
    """Step map: left half=0, right half=1. ROI on right region → mean ≈ 1."""
    mock_cm, _ = _mock_http(_step_depth(h=20, w=20))
    roi = {"x1": 12, "y1": 0, "x2": 20, "y2": 20}
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8), roi=roi
        )
    assert result.data["depth_stats"]["depth_mean"] > 0.95


# ── remote call verification ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_posts_to_remote_url_slash_depth():
    mock_cm, mock_client = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        await DepthAgent(remote_url="http://colab-server:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    called_url = mock_client.post.call_args.args[0]
    assert called_url == "http://colab-server:8080/depth"


@pytest.mark.asyncio
async def test_run_payload_contains_base64_image():
    mock_cm, mock_client = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    call_kwargs = mock_client.post.call_args
    payload = call_kwargs.kwargs.get("json", {})
    assert "image" in payload
    decoded = base64.b64decode(payload["image"])
    assert len(decoded) > 0


# ── error handling ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_image_too_small():
    agent = DepthAgent(remote_url="http://test:8080")
    result = await agent.run(image=np.zeros((2, 2, 3), dtype=np.uint8))
    assert result.status == "error"
    assert "too small" in result.error_message.lower()


@pytest.mark.asyncio
async def test_error_server_unreachable_status():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://unreachable:9999").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.status == "error"


@pytest.mark.asyncio
async def test_error_server_unreachable_message_contains_url():
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://unreachable:9999").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert "http://unreachable:9999" in result.error_message


@pytest.mark.asyncio
async def test_error_invalid_response_missing_depth_map_key():
    mock_response = MagicMock()
    mock_response.json.return_value = {"shape": [20, 20]}  # depth_map key missing
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.status == "error"
    assert "Invalid depth response format" in result.error_message


@pytest.mark.asyncio
async def test_error_invalid_response_missing_shape_key():
    depth_map = _flat_depth()
    depth_b64 = base64.b64encode(depth_map.tobytes()).decode()
    mock_response = MagicMock()
    mock_response.json.return_value = {"depth_map": depth_b64}  # shape key missing
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20, 3), dtype=np.uint8)
        )
    assert result.status == "error"
    assert "Invalid depth response format" in result.error_message


# ── grayscale input ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grayscale_image_handled_successfully():
    mock_cm, _ = _mock_http(_flat_depth())
    with patch("agents.depth_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await DepthAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20), dtype=np.uint8)
        )
    assert result.status == "success"


# ── directive passthrough ────────────────────────────────────────────────────

def test_directive_stored_from_constructor():
    agent = DepthAgent(remote_url="http://localhost:8080", directive="analyze shadows")
    assert agent.directive == "analyze shadows"


def test_directive_empty_by_default():
    agent = DepthAgent(remote_url="http://localhost:8080")
    assert agent.directive == ""
