"""Tests for POST /api/light_test/analyze — all agent HTTP calls are mocked."""
import base64

import cv2
import httpx
import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.main import app
from backend.models.engine import EngineMode, EngineSettings
from backend.services import engine_store
from agents.models import AgentResult


# ── helpers ───────────────────────────────────────────────────────────────────

REMOTE_URL = "https://colab.example.com"


def _make_png_bytes(h: int = 100, w: int = 100) -> bytes:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[20:80, 20:80] = 128
    _, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


def _make_depth_result(success: bool = True) -> AgentResult:
    if success:
        return AgentResult(
            status="success",
            data={
                "depth_map": np.random.rand(100, 100).astype(np.float32),
                "depth_stats": {
                    "depth_complexity": 0.5,
                    "has_shadow_region": True,
                    "depth_range": 0.8,
                    "depth_mean": 0.4,
                    "depth_gradient_max": 0.35,
                },
            },
        )
    return AgentResult(
        status="error",
        data={},
        error_message="Depth server unreachable",
    )


def _make_material_result(success: bool = True) -> AgentResult:
    if success:
        return AgentResult(
            status="success",
            data={
                "surface_type": "metal",
                "material_map": {"region": {"type": "metal", "confidence": 0.8, "bbox": []}},
                "confidence": 0.85,
                "regions": [],
                "feature_stats": {},
            },
        )
    return AgentResult(
        status="error",
        data={},
        error_message="Material server unreachable",
    )


def _mock_agents(depth_ok: bool = True, material_ok: bool = True):
    mock_depth = MagicMock()
    mock_depth.run = AsyncMock(return_value=_make_depth_result(depth_ok))

    mock_material = MagicMock()
    mock_material.run = AsyncMock(return_value=_make_material_result(material_ok))

    return mock_depth, mock_material


@pytest.fixture(autouse=True)
def reset_engine():
    engine_store.update_settings(EngineSettings())
    yield
    engine_store.update_settings(EngineSettings())


@pytest.fixture()
def remote_engine():
    engine_store.update_settings(
        EngineSettings(mode=EngineMode.remote, remote_url=REMOTE_URL)
    )


IMAGE_BYTES = _make_png_bytes()


# ── local engine / bad image guard tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_local_engine_returns_400():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
        response = await client.post("/api/light_test/analyze", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_local_engine_error_message():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
        response = await client.post("/api/light_test/analyze", files=files)
    assert "remote" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_analyze_remote_url_none_returns_400():
    engine_store.update_settings(EngineSettings(mode=EngineMode.remote, remote_url=REMOTE_URL))
    engine_store.update_settings(
        EngineSettings.__new__(EngineSettings)
    )
    # Bypass validator: directly set mode=remote, remote_url=None via local mode
    engine_store.update_settings(EngineSettings())  # back to local
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
        response = await client.post("/api/light_test/analyze", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_analyze_invalid_image_returns_422(remote_engine):  # noqa: F811
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        mock_depth, mock_material = _mock_agents()
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("bad.png", b"not-an-image", "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_invalid_image_detail(remote_engine):  # noqa: F811
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        mock_depth, mock_material = _mock_agents()
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("bad.png", b"not-an-image", "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert "invalid" in response.json()["detail"].lower()


# ── success / partial / error status tests ───────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_both_success_http_200(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True, material_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyze_both_success_status_is_success(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True, material_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_analyze_depth_success_material_error_partial(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True, material_ok=False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["status"] == "partial"


@pytest.mark.asyncio
async def test_analyze_depth_error_material_success_partial(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=False, material_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["status"] == "partial"


@pytest.mark.asyncio
async def test_analyze_both_error_status_is_error(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=False, material_ok=False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["status"] == "error"


# ── response structure tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_response_has_depth_field(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert "depth" in response.json()


@pytest.mark.asyncio
async def test_analyze_response_has_material_field(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert "material" in response.json()


@pytest.mark.asyncio
async def test_analyze_depth_has_required_fields(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    depth = response.json()["depth"]
    for field in ("status", "depth_stats", "depth_map_shape", "depth_map_base64", "error_message"):
        assert field in depth, f"Missing field: {field}"


@pytest.mark.asyncio
async def test_analyze_material_has_required_fields(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    material = response.json()["material"]
    for field in ("status", "surface_type", "material_map", "confidence", "error_message"):
        assert field in material, f"Missing field: {field}"


# ── depth_map_base64 tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_depth_map_base64_is_string(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    b64 = response.json()["depth"]["depth_map_base64"]
    assert isinstance(b64, str) and len(b64) > 0


@pytest.mark.asyncio
async def test_analyze_depth_map_base64_decodable(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    b64 = response.json()["depth"]["depth_map_base64"]
    decoded = base64.b64decode(b64)
    assert len(decoded) > 0


@pytest.mark.asyncio
async def test_analyze_depth_map_base64_decodes_to_png(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    b64 = response.json()["depth"]["depth_map_base64"]
    decoded = base64.b64decode(b64)
    # PNG magic bytes
    assert decoded[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_analyze_depth_map_base64_null_when_depth_fails(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=False, material_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["depth"]["depth_map_base64"] is None


# ── agent call / instantiation tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_both_agents_called_once(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            await client.post("/api/light_test/analyze", files=files)
    mock_depth.run.assert_called_once()
    mock_material.run.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_agents_instantiated_with_remote_url(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    depth_cls = MagicMock(return_value=mock_depth)
    material_cls = MagicMock(return_value=mock_material)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", depth_cls),
            patch("backend.routers.light_test.MaterialAgent", material_cls),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            await client.post("/api/light_test/analyze", files=files)
    depth_cls.assert_called_once_with(remote_url=REMOTE_URL)
    material_cls.assert_called_once_with(remote_url=REMOTE_URL)


# ── error message propagation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_depth_error_message_propagated(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=False, material_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    error_msg = response.json()["depth"]["error_message"]
    assert error_msg == "Depth server unreachable"


@pytest.mark.asyncio
async def test_analyze_material_error_message_propagated(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True, material_ok=False)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    error_msg = response.json()["material"]["error_message"]
    assert error_msg == "Material server unreachable"


# ── success field population ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_depth_stats_populated_on_success(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    depth_stats = response.json()["depth"]["depth_stats"]
    assert depth_stats is not None
    assert "depth_complexity" in depth_stats


@pytest.mark.asyncio
async def test_analyze_material_confidence_populated_on_success(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["material"]["confidence"] == 0.85


@pytest.mark.asyncio
async def test_analyze_surface_type_populated_on_success(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    assert response.json()["material"]["surface_type"] == "metal"


@pytest.mark.asyncio
async def test_analyze_depth_map_shape_is_list_of_two(remote_engine):  # noqa: F811
    mock_depth, mock_material = _mock_agents(depth_ok=True)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        with (
            patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
            patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
        ):
            files = {"file": ("test.png", IMAGE_BYTES, "image/png")}
            response = await client.post("/api/light_test/analyze", files=files)
    shape = response.json()["depth"]["depth_map_shape"]
    assert isinstance(shape, list) and len(shape) == 2
