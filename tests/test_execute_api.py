"""Tests for Execute API endpoints — POST/GET/DELETE /api/execute."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import numpy as np
import pytest

from backend.main import app
from backend.models.engine import EngineSettings, EngineMode


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fake_image_metadata(group: str = "analysis", file_path: str = "/tmp/fake.jpg"):
    meta = MagicMock()
    meta.group = group
    meta.file_path = file_path
    meta.id = "img-001"
    meta.label = "ok"
    meta.index = 1
    return meta


def _fake_execution_status(execution_id: str, status: str = "pending", result: dict = None):
    d = {
        "execution_id": execution_id,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    if result is not None:
        d["result"] = result
    return d


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_stores():
    from backend.services import roi_store, config_store, directives_store, engine_store
    from backend.models.engine import EngineSettings
    roi_store.clear()
    config_store.reset()
    directives_store.reset()
    engine_store.update_settings(EngineSettings())
    yield
    roi_store.clear()
    config_store.reset()
    directives_store.reset()
    engine_store.update_settings(EngineSettings())


# ── POST /api/execute ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_execute_returns_202_with_execution_id():
    mock_manager = MagicMock()
    mock_manager.start_execution = AsyncMock(return_value="exec-uuid-001")
    fake_img = np.zeros((10, 10, 3), dtype=np.uint8)

    with patch("backend.routers.execute.image_store") as mock_img_store, \
         patch("backend.routers.execute.get_manager", return_value=mock_manager), \
         patch("backend.routers.execute.cv2") as mock_cv2:
        mock_img_store.get_all.return_value = [_fake_image_metadata("analysis")]
        mock_cv2.imread.return_value = fake_img

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/execute", json={"user_text": "inspect welds"})

    assert response.status_code == 202
    data = response.json()
    assert data["execution_id"] == "exec-uuid-001"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_post_execute_empty_user_text_returns_422():
    with patch("backend.routers.execute.image_store") as mock_img_store, \
         patch("backend.routers.execute.get_manager"):
        mock_img_store.get_all.return_value = [_fake_image_metadata()]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/execute", json={"user_text": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_execute_no_images_returns_422():
    with patch("backend.routers.execute.image_store") as mock_img_store, \
         patch("backend.routers.execute.get_manager"):
        mock_img_store.get_all.return_value = []

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/execute", json={"user_text": "inspect"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_execute_whitespace_user_text_returns_422():
    with patch("backend.routers.execute.image_store") as mock_img_store, \
         patch("backend.routers.execute.get_manager"):
        mock_img_store.get_all.return_value = [_fake_image_metadata()]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/execute", json={"user_text": "   "})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_execute_ng_images_are_passed_separately():
    mock_manager = MagicMock()
    mock_manager.start_execution = AsyncMock(return_value="exec-001")
    fake_img = np.zeros((10, 10, 3), dtype=np.uint8)

    ok_meta = _fake_image_metadata("analysis", "/tmp/ok.jpg")
    ng_meta = _fake_image_metadata("test", "/tmp/ng.jpg")

    with patch("backend.routers.execute.image_store") as mock_img_store, \
         patch("backend.routers.execute.get_manager", return_value=mock_manager), \
         patch("backend.routers.execute.cv2") as mock_cv2:
        mock_img_store.get_all.return_value = [ok_meta, ng_meta]
        mock_cv2.imread.return_value = fake_img

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.post("/api/execute", json={"user_text": "inspect"})

    call_kwargs = mock_manager.start_execution.call_args
    images_arg = call_kwargs.kwargs.get("images") or call_kwargs.args[1]
    ng_arg = call_kwargs.kwargs.get("ng_images") or call_kwargs.args[2]
    assert len(images_arg) == 1
    assert len(ng_arg) == 1


# ── GET /api/execute/{id} ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_execution_returns_status():
    mock_manager = MagicMock()
    mock_manager.get_status = AsyncMock(
        return_value=_fake_execution_status("exec-001", "running")
    )

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute/exec-001")

    assert response.status_code == 200
    data = response.json()
    assert data["execution_id"] == "exec-001"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_get_execution_not_found_returns_404():
    mock_manager = MagicMock()
    mock_manager.get_status = AsyncMock(return_value=None)

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute/nonexistent")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_completed_execution_includes_lighting_suggestions():
    mock_manager = MagicMock()
    completed_result = {
        "mode": "inspection",
        "scene_context": {
            "surface_type": "metal",
            "contrast": 0.5,
        },
    }
    mock_manager.get_status = AsyncMock(
        return_value=_fake_execution_status("exec-001", "completed", completed_result)
    )

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute/exec-001")

    assert response.status_code == 200
    data = response.json()
    assert "lighting_suggestions" in data["result"]
    assert isinstance(data["result"]["lighting_suggestions"], list)


@pytest.mark.asyncio
async def test_get_completed_execution_lighting_suggestions_triggered_by_metal():
    mock_manager = MagicMock()
    completed_result = {
        "scene_context": {"surface_type": "metal"},
    }
    mock_manager.get_status = AsyncMock(
        return_value=_fake_execution_status("exec-001", "completed", completed_result)
    )

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute/exec-001")

    data = response.json()
    suggestions = data["result"]["lighting_suggestions"]
    assert any(s["category"] == "polarization" for s in suggestions)


@pytest.mark.asyncio
async def test_get_running_execution_no_lighting_suggestions():
    mock_manager = MagicMock()
    mock_manager.get_status = AsyncMock(
        return_value=_fake_execution_status("exec-001", "running")
    )

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute/exec-001")

    data = response.json()
    assert "result" not in data or "lighting_suggestions" not in data.get("result", {})


# ── GET /api/execute ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_executions_returns_list():
    mock_manager = MagicMock()
    mock_manager.list_executions = AsyncMock(return_value=[
        _fake_execution_status("exec-001", "completed"),
        _fake_execution_status("exec-002", "running"),
    ])

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_executions_empty_returns_empty_list():
    mock_manager = MagicMock()
    mock_manager.list_executions = AsyncMock(return_value=[])

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/execute")

    assert response.status_code == 200
    assert response.json() == []


# ── DELETE /api/execute/{id} ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_execution_returns_200_when_cancelled():
    mock_manager = MagicMock()
    mock_manager.cancel_execution = AsyncMock(return_value="cancelled")

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete("/api/execute/exec-001")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_execution_returns_404_for_not_found():
    mock_manager = MagicMock()
    mock_manager.cancel_execution = AsyncMock(return_value="not_found")

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete("/api/execute/nonexistent")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_execution_returns_409_for_completed():
    mock_manager = MagicMock()
    mock_manager.cancel_execution = AsyncMock(return_value="already_completed")

    with patch("backend.routers.execute.get_manager", return_value=mock_manager):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete("/api/execute/exec-001")

    assert response.status_code == 409
