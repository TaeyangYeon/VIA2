"""E2E tests for Light Test window — upload, render, presets, and export.

Uses pytest + httpx + ASGITransport throughout.
AI models (DepthAgent, MaterialAgent) are mocked to return synthetic numpy arrays.
"""
from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import httpx
import numpy as np
import pytest
import pytest_asyncio

from agents.models import AgentResult
from backend.main import app
from backend.models.engine import EngineMode, EngineSettings
from backend.services import engine_store
import backend.routers.light_test as lt_router


# ── helpers ───────────────────────────────────────────────────────────────────

REMOTE_URL = "https://colab.example.com"

SVG_CONTENT = "<svg xmlns='http://www.w3.org/2000/svg'><rect width='800' height='400'/></svg>"


def _make_png_bytes(h: int = 256, w: int = 256) -> bytes:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[50:200, 50:200] = 200
    img[80:170, 80:170] = 100
    _, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


def _depth_agent_result(success: bool = True) -> AgentResult:
    if success:
        depth_map = np.random.rand(256, 256).astype(np.float32)
        return AgentResult(
            status="success",
            data={
                "depth_map": depth_map,
                "depth_stats": {
                    "depth_complexity": 0.4,
                    "has_shadow_region": True,
                    "depth_range": 0.7,
                    "depth_mean": 0.5,
                    "depth_gradient_max": 0.3,
                },
            },
        )
    return AgentResult(status="error", data={}, error_message="Depth agent failed")


def _material_agent_result(surface_type: str = "metal") -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "surface_type": surface_type,
            "material_map": {"region": {"type": surface_type, "confidence": 0.85, "bbox": []}},
            "confidence": 0.85,
        },
    )


def _mock_agents(depth_ok: bool = True, surface: str = "metal"):
    mock_depth = MagicMock()
    mock_depth.run = AsyncMock(return_value=_depth_agent_result(depth_ok))
    mock_material = MagicMock()
    mock_material.run = AsyncMock(return_value=_material_agent_result(surface))
    return mock_depth, mock_material


def _ring_light(light_id: str = "l1") -> dict:
    return {
        "id": light_id,
        "type": "led",
        "shape": "ring",
        "position": {"x": 0, "y": 500, "z": 300},
        "intensity": 1.0,
        "color": {"r": 255, "g": 255, "b": 255},
        "polarizer": False,
    }


def _make_depth_b64(h: int = 64, w: int = 64) -> str:
    depth = (np.random.rand(h, w) * 255).astype(np.uint8)
    _, enc = cv2.imencode(".png", depth)
    return base64.b64encode(enc.tobytes()).decode()


@pytest.fixture(autouse=True)
def _reset_engine():
    engine_store.update_settings(EngineSettings())
    yield
    engine_store.update_settings(EngineSettings())


@pytest.fixture(autouse=True)
def _reset_presets():
    lt_router._presets.clear()
    yield
    lt_router._presets.clear()


@pytest.fixture()
def remote_engine():
    engine_store.update_settings(EngineSettings(mode=EngineMode.remote, remote_url=REMOTE_URL))


PNG_BYTES = _make_png_bytes()


# ═══════════════════════════════════════════════════════════════════════════════
# Class 1: Upload and Analyze
# ═══════════════════════════════════════════════════════════════════════════════

class TestLightTestUploadAndAnalyze:

    @pytest.mark.asyncio
    async def test_analyze_returns_200_with_mocked_agents(self, remote_engine):  # noqa: F811
        mock_depth, mock_material = _mock_agents()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_response_contains_depth_field(self, remote_engine):  # noqa: F811
        mock_depth, mock_material = _mock_agents()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        assert "depth" in resp.json()

    @pytest.mark.asyncio
    async def test_analyze_response_contains_material_field(self, remote_engine):  # noqa: F811
        mock_depth, mock_material = _mock_agents()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        assert "material" in resp.json()

    @pytest.mark.asyncio
    async def test_analyze_depth_map_base64_present(self, remote_engine):  # noqa: F811
        mock_depth, mock_material = _mock_agents()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        depth = resp.json()["depth"]
        assert depth["depth_map_base64"] is not None

    @pytest.mark.asyncio
    async def test_analyze_depth_map_values_in_range(self, remote_engine):  # noqa: F811
        """Decoded depth PNG values should be in [0, 255] (uint8 range)."""
        mock_depth, mock_material = _mock_agents()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        b64 = resp.json()["depth"]["depth_map_base64"]
        raw = base64.b64decode(b64)
        arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        assert img is not None
        assert img.min() >= 0
        assert img.max() <= 255

    @pytest.mark.asyncio
    async def test_analyze_status_is_success_when_both_ok(self, remote_engine):  # noqa: F811
        mock_depth, mock_material = _mock_agents(depth_ok=True)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        assert resp.json()["status"] == "success"

    @pytest.mark.asyncio
    async def test_analyze_surface_type_returned(self, remote_engine):  # noqa: F811
        mock_depth, mock_material = _mock_agents(surface="plastic")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
        assert resp.json()["material"]["surface_type"] == "plastic"

    @pytest.mark.asyncio
    async def test_analyze_local_engine_returns_400(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/light_test/analyze",
                files={"file": ("test.png", PNG_BYTES, "image/png")},
            )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# Class 2: Render
# ═══════════════════════════════════════════════════════════════════════════════

class TestLightTestRender:

    @pytest_asyncio.fixture()
    async def uploaded_image_id(self):
        """Upload a test image and return its ID."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/images/upload",
                files={"file": ("OK_1.png", PNG_BYTES, "image/png")},
            )
        assert resp.status_code in (200, 201)
        return resp.json()["id"]

    @pytest.mark.asyncio
    async def test_render_ring_light_returns_200(self, uploaded_image_id):
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light()],
                "surface_type": "metal",
            })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_render_returns_rendered_image_field(self, uploaded_image_id):
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light()],
                "surface_type": "metal",
            })
        assert "rendered_image" in resp.json()

    @pytest.mark.asyncio
    async def test_render_rendered_image_is_base64_decodable(self, uploaded_image_id):
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light()],
                "surface_type": "plastic",
            })
        b64 = resp.json()["rendered_image"]
        raw = base64.b64decode(b64)
        arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        assert img is not None

    @pytest.mark.asyncio
    async def test_render_unknown_image_id_returns_404(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": "nonexistent-id",
                "lights": [_ring_light()],
                "surface_type": "metal",
            })
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_render_with_depth_map_returns_200(self, uploaded_image_id):
        image_id = uploaded_image_id
        depth_b64 = _make_depth_b64()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "depth_map_base64": depth_b64,
                "lights": [_ring_light()],
                "surface_type": "metal",
            })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_render_polarizer_angle_endpoint_accepts_90(self, uploaded_image_id):
        """Verify lens_polarizer_angle=90 is accepted and returns 200."""
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light()],
                "surface_type": "metal",
                "lens_polarizer_angle": 90.0,
            })
        assert resp.status_code == 200
        assert "rendered_image" in resp.json()

    @pytest.mark.asyncio
    async def test_render_color_red_light_differs_from_white(self, uploaded_image_id):
        image_id = uploaded_image_id
        white_light = _ring_light()
        red_light = {**_ring_light(), "color": {"r": 255, "g": 0, "b": 0}}
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp_white = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [white_light],
                "surface_type": "plastic",
            })
            resp_red = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [red_light],
                "surface_type": "plastic",
            })
        assert resp_white.json()["rendered_image"] != resp_red.json()["rendered_image"]

    @pytest.mark.asyncio
    async def test_histogram_endpoint_returns_channels(self, uploaded_image_id):
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            render_resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light()],
                "surface_type": "metal",
            })
            rendered_b64 = render_resp.json()["rendered_image"]
            hist_resp = await client.post(
                "/api/light_test/histogram", json={"image_base64": rendered_b64}
            )
        hist = hist_resp.json()
        assert hist_resp.status_code == 200
        assert "channels" in hist
        assert len(hist["channels"]) > 0

    @pytest.mark.asyncio
    async def test_render_no_lights_returns_200(self, uploaded_image_id):
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [],
                "surface_type": "rubber",
            })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_render_two_lights_returns_200(self, uploaded_image_id):
        image_id = uploaded_image_id
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light("l1"), _ring_light("l2")],
                "surface_type": "metal",
            })
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# Class 3: Preset CRUD
# ═══════════════════════════════════════════════════════════════════════════════

class TestLightTestPresetCRUD:

    LIGHTS = [_ring_light("l1"), {**_ring_light("l2"), "shape": "bar"}]

    @pytest.mark.asyncio
    async def test_save_preset_returns_saved(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/light_test/preset/save", json={
                "name": "test-preset",
                "lights": self.LIGHTS,
                "lens_polarizer_angle": 30.0,
            })
        assert resp.status_code == 200
        assert resp.json()["status"] == "saved"

    @pytest.mark.asyncio
    async def test_list_presets_contains_saved(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/light_test/preset/save", json={
                "name": "list-test",
                "lights": self.LIGHTS,
            })
            resp = await client.get("/api/light_test/preset/list")
        names = [p["name"] for p in resp.json()["presets"]]
        assert "list-test" in names

    @pytest.mark.asyncio
    async def test_get_preset_by_name_returns_lights(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/light_test/preset/save", json={
                "name": "get-test",
                "lights": self.LIGHTS,
                "lens_polarizer_angle": 45.0,
            })
            resp = await client.get("/api/light_test/preset/get-test")
        data = resp.json()
        assert len(data["lights"]) == 2
        assert data["lens_polarizer_angle"] == 45.0

    @pytest.mark.asyncio
    async def test_delete_preset_returns_deleted(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/light_test/preset/save", json={
                "name": "del-me",
                "lights": self.LIGHTS,
            })
            resp = await client.delete("/api/light_test/preset/del-me")
        assert resp.json()["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_deleted_preset_returns_404_on_get(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/light_test/preset/save", json={
                "name": "del-check",
                "lights": self.LIGHTS,
            })
            await client.delete("/api/light_test/preset/del-check")
            resp = await client.get("/api/light_test/preset/del-check")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_save_duplicate_name_overwrites(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/light_test/preset/save", json={
                "name": "dup",
                "lights": self.LIGHTS,
                "lens_polarizer_angle": 0.0,
            })
            await client.post("/api/light_test/preset/save", json={
                "name": "dup",
                "lights": self.LIGHTS,
                "lens_polarizer_angle": 90.0,
            })
            resp = await client.get("/api/light_test/preset/dup")
        assert resp.json()["lens_polarizer_angle"] == 90.0

    @pytest.mark.asyncio
    async def test_list_returns_empty_when_no_presets(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/light_test/preset/list")
        assert resp.json()["presets"] == []

    @pytest.mark.asyncio
    async def test_get_unknown_preset_returns_404(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/light_test/preset/unknown")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Class 4: Export Flow
# ═══════════════════════════════════════════════════════════════════════════════

SVG_RESULT = SVG_CONTENT
EXEC_ID = "e2e-exec-001"


def _mock_exec_status(
    execution_id: str = EXEC_ID,
    svg: str | None = SVG_RESULT,
    sheets: list | None = None,
) -> dict:
    result: dict = {}
    if svg is not None:
        result["blueprint_svg"] = svg
    if sheets is not None:
        result["parameter_sheets"] = sheets
    return {
        "execution_id": execution_id,
        "status": "completed",
        "result": result if result else None,
    }


class TestLightTestExportFlow:

    @pytest.mark.asyncio
    async def test_export_svg_returns_200(self):
        status = _mock_exec_status()
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=status)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/svg", json={"execution_id": EXEC_ID})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_export_svg_content_type_is_svg(self):
        status = _mock_exec_status()
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=status)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/svg", json={"execution_id": EXEC_ID})
        assert "image/svg+xml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_pdf_returns_200(self):
        status = _mock_exec_status()
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=status)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/pdf", json={"execution_id": EXEC_ID})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_export_pdf_content_type_is_pdf(self):
        status = _mock_exec_status()
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=status)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/pdf", json={"execution_id": EXEC_ID})
        assert "application/pdf" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_parameters_json_structure(self):
        sheets = [{"node_id": "n1", "node_name": "grayscale", "parameters": []}]
        status = _mock_exec_status(sheets=sheets)
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=status)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/export/parameters", json={"execution_id": EXEC_ID}
                )
        data = resp.json()
        assert "execution_id" in data
        assert "parameter_sheets" in data
        assert "exported_at" in data

    @pytest.mark.asyncio
    async def test_export_svg_unknown_id_returns_404(self):
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=None)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/svg", json={"execution_id": "bad-id"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_pdf_unknown_id_returns_404(self):
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=None)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/pdf", json={"execution_id": "bad-id"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_export_parameters_unknown_id_returns_404(self):
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=None)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/export/parameters", json={"execution_id": "bad-id"}
                )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Class 5: Full Flow (integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TestLightTestFullFlow:

    @pytest.mark.asyncio
    async def test_upload_image_success(self):
        """Step 1: Upload image."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/images/upload",
                files={"file": ("OK_1.png", PNG_BYTES, "image/png")},
            )
        assert resp.status_code in (200, 201)
        assert "id" in resp.json()

    @pytest.mark.asyncio
    async def test_analyze_then_render_flow(self, remote_engine):  # noqa: F811
        """Upload image, analyze (mocked), then render."""
        mock_depth, mock_material = _mock_agents()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Upload
            upload_resp = await client.post(
                "/api/images/upload",
                files={"file": ("OK_1.png", PNG_BYTES, "image/png")},
            )
            image_id = upload_resp.json()["id"]

            # Analyze (mocked)
            with (
                patch("backend.routers.light_test.DepthAgent", return_value=mock_depth),
                patch("backend.routers.light_test.MaterialAgent", return_value=mock_material),
            ):
                analyze_resp = await client.post(
                    "/api/light_test/analyze",
                    files={"file": ("test.png", PNG_BYTES, "image/png")},
                )
            depth_b64 = analyze_resp.json()["depth"]["depth_map_base64"]
            surface_type = analyze_resp.json()["material"]["surface_type"]

            # Render
            render_resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "depth_map_base64": depth_b64,
                "lights": [_ring_light("l1"), {**_ring_light("l2"), "shape": "spot"}],
                "surface_type": surface_type,
            })

        assert render_resp.status_code == 200
        assert "rendered_image" in render_resp.json()

    @pytest.mark.asyncio
    async def test_save_and_reload_preset_matches_lights(self):
        """Save a preset, reload it, verify lights match."""
        lights = [_ring_light("l1"), {**_ring_light("l2"), "shape": "bar"}]
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/light_test/preset/save", json={
                "name": "flow-preset",
                "lights": lights,
                "lens_polarizer_angle": 60.0,
            })
            resp = await client.get("/api/light_test/preset/flow-preset")
        loaded = resp.json()
        assert loaded["lens_polarizer_angle"] == 60.0
        assert len(loaded["lights"]) == 2
        shapes = {l["shape"] for l in loaded["lights"]}
        assert "ring" in shapes
        assert "bar" in shapes

    @pytest.mark.asyncio
    async def test_histogram_after_render_has_valid_structure(self):
        """Render an image and verify histogram output structure."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            upload_resp = await client.post(
                "/api/images/upload",
                files={"file": ("OK_2.png", PNG_BYTES, "image/png")},
            )
            image_id = upload_resp.json()["id"]
            render_resp = await client.post("/api/light_test/render", json={
                "image_id": image_id,
                "lights": [_ring_light()],
                "surface_type": "metal",
            })
            rendered_b64 = render_resp.json()["rendered_image"]
            hist_resp = await client.post(
                "/api/light_test/histogram", json={"image_base64": rendered_b64}
            )
        hist = hist_resp.json()
        assert hist_resp.status_code == 200
        assert "channels" in hist
        for ch in hist["channels"]:
            assert "bins" in ch
            assert len(ch["bins"]) == 256

    @pytest.mark.asyncio
    async def test_export_svg_after_execution_flow(self):
        """Verify SVG export returns correct content type."""
        status = _mock_exec_status(execution_id="flow-exec", svg=SVG_CONTENT)
        with patch("backend.routers.export.get_manager") as mock_gm:
            mock_gm.return_value.get_status = AsyncMock(return_value=status)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/export/svg", json={"execution_id": "flow-exec"})
        assert resp.status_code == 200
        assert b"<svg" in resp.content
