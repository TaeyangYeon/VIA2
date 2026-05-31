"""Tests for export router endpoints — SVG, PDF, parameters, and preset CRUD."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.main import app
import backend.routers.light_test as lt_router


# ── helpers ───────────────────────────────────────────────────────────────────

SVG_CONTENT = "<svg xmlns='http://www.w3.org/2000/svg'><rect width='800' height='400'/></svg>"

EXECUTION_ID = "test-exec-abc123"


def _make_mock_status(
    execution_id: str = EXECUTION_ID,
    blueprint_svg: str | None = SVG_CONTENT,
    parameter_sheets: list | None = None,
) -> dict:
    result: dict = {}
    if blueprint_svg is not None:
        result["blueprint_svg"] = blueprint_svg
    if parameter_sheets is not None:
        result["parameter_sheets"] = parameter_sheets
    return {
        "execution_id": execution_id,
        "status": "completed",
        "result": result,
    }


@pytest.fixture(autouse=True)
def reset_presets():
    lt_router._presets.clear()
    yield
    lt_router._presets.clear()


# ── SVG export tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_svg_returns_200():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": EXECUTION_ID})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_export_svg_content_type():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": EXECUTION_ID})
    assert "image/svg+xml" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_export_svg_content_disposition():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": EXECUTION_ID})
    assert "blueprint.svg" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_export_svg_body_contains_svg():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": EXECUTION_ID})
    assert b"<svg" in resp.content


@pytest.mark.asyncio
async def test_export_svg_unknown_execution_404():
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=None)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": "nonexistent"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_svg_no_blueprint_in_result_404():
    mock_status = _make_mock_status(blueprint_svg=None)
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": EXECUTION_ID})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_svg_nested_blueprint_field():
    """Should also find SVG inside result['blueprint']['svg_content']."""
    mock_status = {
        "execution_id": EXECUTION_ID,
        "status": "completed",
        "result": {
            "blueprint": {"svg_content": SVG_CONTENT, "nodes": [], "edges": []}
        },
    }
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/svg", json={"execution_id": EXECUTION_ID})
    assert resp.status_code == 200
    assert b"<svg" in resp.content


# ── PDF export tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_pdf_returns_200():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/pdf", json={"execution_id": EXECUTION_ID})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_export_pdf_content_type():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/pdf", json={"execution_id": EXECUTION_ID})
    assert "application/pdf" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_export_pdf_content_disposition():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/pdf", json={"execution_id": EXECUTION_ID})
    assert "blueprint.pdf" in resp.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_export_pdf_non_empty_body():
    mock_status = _make_mock_status()
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/pdf", json={"execution_id": EXECUTION_ID})
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_export_pdf_unknown_execution_404():
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=None)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/pdf", json={"execution_id": "bad-id"})
    assert resp.status_code == 404


# ── Parameters export tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_parameters_returns_200():
    sheets = [{"node_id": "n1", "node_name": "grayscale", "parameters": []}]
    mock_status = _make_mock_status(parameter_sheets=sheets)
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/parameters", json={"execution_id": EXECUTION_ID})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_export_parameters_contains_execution_id():
    sheets = [{"node_id": "n1", "parameters": []}]
    mock_status = _make_mock_status(parameter_sheets=sheets)
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/parameters", json={"execution_id": EXECUTION_ID})
    data = resp.json()
    assert data["execution_id"] == EXECUTION_ID


@pytest.mark.asyncio
async def test_export_parameters_contains_parameter_sheets():
    sheets = [{"node_id": "n1", "node_name": "grayscale", "parameters": []}]
    mock_status = _make_mock_status(parameter_sheets=sheets)
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/parameters", json={"execution_id": EXECUTION_ID})
    data = resp.json()
    assert "parameter_sheets" in data
    assert len(data["parameter_sheets"]) == 1


@pytest.mark.asyncio
async def test_export_parameters_contains_exported_at():
    sheets = [{"node_id": "n1", "parameters": []}]
    mock_status = _make_mock_status(parameter_sheets=sheets)
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/parameters", json={"execution_id": EXECUTION_ID})
    data = resp.json()
    assert "exported_at" in data


@pytest.mark.asyncio
async def test_export_parameters_unknown_execution_404():
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=None)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/parameters", json={"execution_id": "bad"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_parameters_no_sheets_in_result_404():
    mock_status = {
        "execution_id": EXECUTION_ID,
        "status": "completed",
        "result": {"blueprint_svg": SVG_CONTENT},  # no parameter_sheets key
    }
    with patch("backend.routers.export.get_manager") as mock_gm:
        mock_gm.return_value.get_status = AsyncMock(return_value=mock_status)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/export/parameters", json={"execution_id": EXECUTION_ID})
    assert resp.status_code == 404


# ── preset CRUD tests ─────────────────────────────────────────────────────────

SAMPLE_LIGHTS = [
    {"id": "l1", "type": "led", "shape": "ring", "position": {"x": 0, "y": 500, "z": 300},
     "intensity": 1.0, "color": {"r": 255, "g": 255, "b": 255}, "polarizer": False},
]


@pytest.mark.asyncio
async def test_preset_save_returns_saved_status():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/light_test/preset/save", json={
            "name": "ring-test",
            "lights": SAMPLE_LIGHTS,
        })
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"


@pytest.mark.asyncio
async def test_preset_save_returns_name():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/api/light_test/preset/save", json={
            "name": "my-preset",
            "lights": SAMPLE_LIGHTS,
        })
    assert resp.json()["name"] == "my-preset"


@pytest.mark.asyncio
async def test_preset_list_shows_saved_preset():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/light_test/preset/save", json={
            "name": "preset-A",
            "lights": SAMPLE_LIGHTS,
        })
        resp = await client.get("/api/light_test/preset/list")
    names = [p["name"] for p in resp.json()["presets"]]
    assert "preset-A" in names


@pytest.mark.asyncio
async def test_preset_get_returns_full_data():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/light_test/preset/save", json={
            "name": "detail-test",
            "lights": SAMPLE_LIGHTS,
            "lens_polarizer_angle": 45.0,
            "description": "test desc",
        })
        resp = await client.get("/api/light_test/preset/detail-test")
    data = resp.json()
    assert data["name"] == "detail-test"
    assert data["lens_polarizer_angle"] == 45.0
    assert len(data["lights"]) == 1


@pytest.mark.asyncio
async def test_preset_get_unknown_returns_404():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/light_test/preset/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_preset_delete_removes_preset():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/light_test/preset/save", json={
            "name": "to-delete",
            "lights": SAMPLE_LIGHTS,
        })
        del_resp = await client.delete("/api/light_test/preset/to-delete")
        assert del_resp.json()["status"] == "deleted"
        get_resp = await client.get("/api/light_test/preset/to-delete")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_preset_delete_unknown_returns_404():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.delete("/api/light_test/preset/missing")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_preset_overwrite_same_name():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/light_test/preset/save", json={
            "name": "overwrite-me",
            "lights": SAMPLE_LIGHTS,
            "lens_polarizer_angle": 0.0,
        })
        await client.post("/api/light_test/preset/save", json={
            "name": "overwrite-me",
            "lights": SAMPLE_LIGHTS,
            "lens_polarizer_angle": 90.0,
        })
        resp = await client.get("/api/light_test/preset/overwrite-me")
    assert resp.json()["lens_polarizer_angle"] == 90.0


@pytest.mark.asyncio
async def test_preset_list_empty_initially():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/light_test/preset/list")
    assert resp.json()["presets"] == []


@pytest.mark.asyncio
async def test_preset_list_includes_description():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/light_test/preset/save", json={
            "name": "desc-test",
            "lights": SAMPLE_LIGHTS,
            "description": "ring light setup",
        })
        resp = await client.get("/api/light_test/preset/list")
    presets = resp.json()["presets"]
    assert presets[0]["description"] == "ring light setup"
