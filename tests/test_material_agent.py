"""Tests for MaterialAgent — all HTTP calls are mocked, no real server required."""
import base64
import pytest
import numpy as np
import cv2
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from agents.material_agent import MaterialAgent, _cosine_similarity
from agents.material_lut import MATERIAL_LUT
from agents.models import AgentResult
from agents.base_agent import BaseAgent


# ── helpers ───────────────────────────────────────────────────────────────────

def _florence_ok(label: str = "metal", confidence: float = 0.9) -> dict:
    return {
        "caption": f"{label} surface",
        "regions": [{"label": label, "bbox": [0, 0, 100, 100], "confidence": confidence}],
    }


def _dinov2_ok(n: int = 1, dim: int = 384) -> dict:
    return {"features": [[0.1] * dim for _ in range(n)], "shape": [n, dim]}


def _mock_http(
    florence_data: dict = None,
    dinov2_data: dict = None,
    florence_exc: Exception = None,
    dinov2_exc: Exception = None,
):
    """Return (mock_cm, mock_client) routing Florence-2 and DINOv2 calls by URL."""
    if florence_data is None and florence_exc is None:
        florence_data = _florence_ok()
    if dinov2_data is None and dinov2_exc is None:
        dinov2_data = _dinov2_ok()

    async def _post(url, **kwargs):
        if "florence2" in url:
            if florence_exc is not None:
                raise florence_exc
            resp = MagicMock()
            resp.json.return_value = florence_data
            return resp
        if dinov2_exc is not None:
            raise dinov2_exc
        resp = MagicMock()
        resp.json.return_value = dinov2_data
        return resp

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=_post)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm, mock_client


def _img(h: int = 20, w: int = 20, ch: int = 3) -> np.ndarray:
    if ch == 1:
        return np.zeros((h, w), dtype=np.uint8)
    return np.zeros((h, w, ch), dtype=np.uint8)


# ── class instantiation ───────────────────────────────────────────────────────

def test_material_agent_is_base_agent():
    assert isinstance(MaterialAgent(remote_url="http://localhost:8080"), BaseAgent)


def test_material_agent_name_is_material_agent():
    assert MaterialAgent(remote_url="http://localhost:8080").name == "material_agent"


def test_material_agent_stores_remote_url():
    assert MaterialAgent(remote_url="http://colab:8080").remote_url == "http://colab:8080"


def test_material_agent_default_directive_is_empty():
    assert MaterialAgent(remote_url="http://localhost:8080").directive == ""


def test_material_agent_custom_directive_stored():
    agent = MaterialAgent(remote_url="http://localhost:8080", directive="focus on metal")
    assert agent.directive == "focus on metal"


# ── AgentResult structure ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_returns_success_status():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_result_has_surface_type_key():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert "surface_type" in result.data


@pytest.mark.asyncio
async def test_run_result_has_material_map_key():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert "material_map" in result.data


@pytest.mark.asyncio
async def test_run_result_has_confidence_key():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert "confidence" in result.data


@pytest.mark.asyncio
async def test_run_result_has_regions_key():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert "regions" in result.data


@pytest.mark.asyncio
async def test_run_result_has_feature_stats_key():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert "feature_stats" in result.data


@pytest.mark.asyncio
async def test_run_execution_time_non_negative():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.execution_time_ms >= 0.0


@pytest.mark.asyncio
async def test_run_success_has_no_error_message():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.error_message is None


# ── Material LUT ──────────────────────────────────────────────────────────────

def test_lut_has_all_required_materials():
    required = {"metal", "plastic", "glass", "rubber", "ceramic", "wood", "fabric", "paper"}
    assert required == set(MATERIAL_LUT.keys())


def test_lut_optical_properties_in_range():
    for name, props in MATERIAL_LUT.items():
        for field in ("specular", "diffuse", "roughness"):
            v = props[field]
            assert 0.0 <= v <= 1.0, f"{name}.{field}={v} out of [0,1]"


def test_lut_reference_features_have_dim_384():
    for name, props in MATERIAL_LUT.items():
        assert len(props["reference_features"]) == 384, f"{name} dim != 384"


def test_lut_metal_has_higher_specular_than_fabric():
    assert MATERIAL_LUT["metal"]["specular"] > MATERIAL_LUT["fabric"]["specular"]


# ── cosine similarity ─────────────────────────────────────────────────────────

def test_cosine_similarity_identical_vectors_returns_one():
    v = [1.0, 0.0, 0.0]
    assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6


def test_cosine_similarity_zero_vector_returns_zero():
    assert _cosine_similarity([0.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == 0.0


def test_cosine_similarity_orthogonal_vectors_return_zero():
    assert abs(_cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-6


# ── Florence-2 remote call ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_posts_to_florence2_caption_url():
    mock_cm, mock_client = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        await MaterialAgent(remote_url="http://colab:8080").run(image=_img())
    called_urls = [c.args[0] for c in mock_client.post.call_args_list]
    assert any("florence2/caption" in u for u in called_urls)


@pytest.mark.asyncio
async def test_florence2_payload_contains_base64_image():
    mock_cm, mock_client = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    call = next(c for c in mock_client.post.call_args_list if "florence2" in c.args[0])
    payload = call.kwargs.get("json", {})
    assert "image" in payload
    assert len(base64.b64decode(payload["image"])) > 0


@pytest.mark.asyncio
async def test_florence2_regions_appear_in_result():
    mock_cm, _ = _mock_http(
        florence_data={
            "caption": "metal panel",
            "regions": [{"label": "metal", "bbox": [0, 0, 50, 50], "confidence": 0.95}],
        }
    )
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert len(result.data["regions"]) == 1
    assert result.data["regions"][0]["label"] == "metal"


# ── DINOv2 remote call ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_posts_to_dinov2_features_url():
    mock_cm, mock_client = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        await MaterialAgent(remote_url="http://colab:8080").run(image=_img())
    called_urls = [c.args[0] for c in mock_client.post.call_args_list]
    assert any("dinov2/features" in u for u in called_urls)


@pytest.mark.asyncio
async def test_dinov2_payload_contains_base64_image():
    mock_cm, mock_client = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    call = next(c for c in mock_client.post.call_args_list if "dinov2" in c.args[0])
    assert "image" in call.kwargs.get("json", {})


@pytest.mark.asyncio
async def test_dinov2_features_reflected_in_feature_stats():
    mock_cm, _ = _mock_http(dinov2_data={"features": [[0.5] * 384], "shape": [1, 384]})
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    stats = result.data["feature_stats"]
    assert stats["feature_dim"] == 384
    assert stats["feature_norm"] > 0.0


# ── combined classification ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_metal_region_label_sets_surface_type():
    mock_cm, _ = _mock_http(
        florence_data={
            "caption": "metal panel",
            "regions": [{"label": "metal", "bbox": [0, 0, 100, 100], "confidence": 0.9}],
        }
    )
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.data["surface_type"] == "metal"


@pytest.mark.asyncio
async def test_confidence_in_range_0_to_1():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert 0.0 <= result.data["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_feature_stats_has_required_fields():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    stats = result.data["feature_stats"]
    for key in ("feature_dim", "feature_norm", "top_similarities"):
        assert key in stats, f"Missing feature_stats key: {key}"


# ── ROI cropping ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_roi_crops_image_before_sending():
    """Sent image should match ROI dimensions, not original image size."""
    mock_cm, mock_client = _mock_http()
    roi = {"x1": 0, "y1": 0, "x2": 10, "y2": 10}
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        await MaterialAgent(remote_url="http://test:8080").run(
            image=np.zeros((40, 40, 3), dtype=np.uint8), roi=roi
        )
    call = next(c for c in mock_client.post.call_args_list if "florence2" in c.args[0])
    img_bytes = base64.b64decode(call.kwargs["json"]["image"])
    decoded = cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape[0] == 10
    assert decoded.shape[1] == 10


@pytest.mark.asyncio
async def test_roi_none_sends_full_image():
    mock_cm, mock_client = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        await MaterialAgent(remote_url="http://test:8080").run(
            image=np.zeros((30, 30, 3), dtype=np.uint8)
        )
    call = next(c for c in mock_client.post.call_args_list if "florence2" in c.args[0])
    img_bytes = base64.b64decode(call.kwargs["json"]["image"])
    decoded = cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded.shape[0] == 30
    assert decoded.shape[1] == 30


# ── error handling ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_image_too_small():
    result = await MaterialAgent(remote_url="http://test:8080").run(
        image=np.zeros((2, 2, 3), dtype=np.uint8)
    )
    assert result.status == "error"
    assert "too small" in result.error_message.lower()


@pytest.mark.asyncio
async def test_error_image_1x1_too_small():
    result = await MaterialAgent(remote_url="http://test:8080").run(
        image=np.zeros((1, 1, 3), dtype=np.uint8)
    )
    assert result.status == "error"


@pytest.mark.asyncio
async def test_error_both_servers_unreachable_status():
    exc = httpx.ConnectError("connection refused")
    mock_cm, _ = _mock_http(florence_exc=exc, dinov2_exc=exc)
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://unreachable:9999").run(image=_img())
    assert result.status == "error"


@pytest.mark.asyncio
async def test_error_both_servers_unreachable_message_has_url():
    exc = httpx.ConnectError("connection refused")
    mock_cm, _ = _mock_http(florence_exc=exc, dinov2_exc=exc)
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://unreachable:9999").run(image=_img())
    assert "http://unreachable:9999" in result.error_message


@pytest.mark.asyncio
async def test_error_invalid_florence2_format_when_both_fail():
    bad_florence = {"caption": "metal panel"}       # no "regions" key
    bad_dinov2 = {"shape": [1, 384]}               # no "features" key
    mock_cm, _ = _mock_http(florence_data=bad_florence, dinov2_data=bad_dinov2)
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.status == "error"
    assert "Invalid Florence-2 response format" in result.error_message


@pytest.mark.asyncio
async def test_error_florence2_unreachable_message_mentions_florence():
    exc = httpx.ConnectError("refused")
    bad_dinov2 = {"shape": [1, 384]}  # no "features" key — both fail
    mock_cm, _ = _mock_http(florence_exc=exc, dinov2_data=bad_dinov2)
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.status == "error"
    assert "Florence-2" in result.error_message


# ── partial failure ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_partial_failure_dinov2_unreachable_returns_success():
    """Florence-2 succeeds, DINOv2 unreachable → still success with partial data."""
    mock_cm, _ = _mock_http(dinov2_exc=httpx.ConnectError("refused"))
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_partial_failure_florence2_unreachable_returns_success():
    """DINOv2 succeeds, Florence-2 unreachable → still success with partial data."""
    mock_cm, _ = _mock_http(florence_exc=httpx.ConnectError("refused"))
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(image=_img())
    assert result.status == "success"


# ── grayscale input ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grayscale_image_handled_successfully():
    mock_cm, _ = _mock_http()
    with patch("agents.material_agent.httpx.AsyncClient", return_value=mock_cm):
        result = await MaterialAgent(remote_url="http://test:8080").run(
            image=np.zeros((20, 20), dtype=np.uint8)
        )
    assert result.status == "success"


# ── directive ─────────────────────────────────────────────────────────────────

def test_directive_stored_from_constructor():
    agent = MaterialAgent(remote_url="http://localhost:8080", directive="analyze specular")
    assert agent.directive == "analyze specular"
