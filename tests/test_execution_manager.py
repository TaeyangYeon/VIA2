"""Tests for ExecutionManager — async pipeline execution lifecycle."""
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from agents.models import AgentDirectives, AgentResult
from backend.models.engine import EngineSettings, EngineMode
from backend.services.execution_manager import ExecutionManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def _img() -> np.ndarray:
    return np.zeros((10, 10, 3), dtype=np.uint8)


def _success_result() -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "mode": "inspection",
            "scene_context": {"contrast": 0.5, "surface_type": "plastic"},
        },
    )


def _failed_result() -> AgentResult:
    return AgentResult(
        status="error",
        data={},
        error_message="pipeline failed",
    )


def _engine_settings() -> EngineSettings:
    return EngineSettings(mode=EngineMode.local)


def _directives() -> AgentDirectives:
    return AgentDirectives()


# ── start_execution ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_execution_returns_execution_id():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = AsyncMock(return_value=_success_result())
        with patch("backend.services.execution_manager.create_adapter"):
            eid = await manager.start_execution(
                user_text="test",
                images=[_img()],
                ng_images=[_img()],
                roi=None,
                text_query=None,
                success_criteria=None,
                directives=_directives(),
                engine_settings=_engine_settings(),
            )
    assert isinstance(eid, str)
    assert len(eid) == 36  # UUID4 format


@pytest.mark.asyncio
async def test_start_execution_initial_status_is_pending():
    manager = ExecutionManager()
    # Use a slow mock so we can check status before it completes
    slow_event = asyncio.Event()

    async def slow_run(*args, **kwargs):
        await slow_event.wait()
        return _success_result()

    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = slow_run
        with patch("backend.services.execution_manager.create_adapter"):
            eid = await manager.start_execution(
                user_text="test",
                images=[_img()],
                ng_images=None,
                roi=None,
                text_query=None,
                success_criteria=None,
                directives=_directives(),
                engine_settings=_engine_settings(),
            )
    status = await manager.get_status(eid)
    assert status["status"] in ("pending", "running")
    slow_event.set()


# ── get_status ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_status_returns_none_for_unknown_id():
    manager = ExecutionManager()
    result = await manager.get_status("nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_get_status_completed_contains_result():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch, \
         patch("backend.services.execution_manager.create_adapter"):
        MockOrch.return_value.run = AsyncMock(return_value=_success_result())
        eid = await manager.start_execution(
            user_text="inspect",
            images=[_img()],
            ng_images=[_img()],
            roi=None,
            text_query=None,
            success_criteria=None,
            directives=_directives(),
            engine_settings=_engine_settings(),
        )
        # Allow background task to complete while patches are still active
        await asyncio.sleep(0.05)
    status = await manager.get_status(eid)
    assert status["status"] == "completed"
    assert "result" in status
    assert status["result"]["mode"] == "inspection"


@pytest.mark.asyncio
async def test_get_status_failed_contains_error():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = AsyncMock(return_value=_failed_result())
        with patch("backend.services.execution_manager.create_adapter"):
            eid = await manager.start_execution(
                user_text="inspect",
                images=[_img()],
                ng_images=[_img()],
                roi=None,
                text_query=None,
                success_criteria=None,
                directives=_directives(),
                engine_settings=_engine_settings(),
            )
    await asyncio.sleep(0.05)
    status = await manager.get_status(eid)
    assert status["status"] == "failed"
    assert "error" in status


@pytest.mark.asyncio
async def test_get_status_exception_marks_failed():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch, \
         patch("backend.services.execution_manager.create_adapter"):
        MockOrch.return_value.run = AsyncMock(side_effect=RuntimeError("boom"))
        eid = await manager.start_execution(
            user_text="inspect",
            images=[_img()],
            ng_images=None,
            roi=None,
            text_query=None,
            success_criteria=None,
            directives=_directives(),
            engine_settings=_engine_settings(),
        )
        await asyncio.sleep(0.05)
    status = await manager.get_status(eid)
    assert status["status"] == "failed"
    assert "boom" in status["error"]


@pytest.mark.asyncio
async def test_get_status_dict_contains_required_keys():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = AsyncMock(return_value=_success_result())
        with patch("backend.services.execution_manager.create_adapter"):
            eid = await manager.start_execution(
                user_text="test",
                images=[_img()],
                ng_images=None,
                roi=None,
                text_query=None,
                success_criteria=None,
                directives=_directives(),
                engine_settings=_engine_settings(),
            )
    await asyncio.sleep(0.05)
    status = await manager.get_status(eid)
    assert "execution_id" in status
    assert "status" in status
    assert "created_at" in status
    assert status["execution_id"] == eid


# ── cancel_execution ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cancel_execution_returns_not_found_for_unknown_id():
    manager = ExecutionManager()
    result = await manager.cancel_execution("nonexistent")
    assert result == "not_found"


@pytest.mark.asyncio
async def test_cancel_execution_returns_already_completed_for_done_execution():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = AsyncMock(return_value=_success_result())
        with patch("backend.services.execution_manager.create_adapter"):
            eid = await manager.start_execution(
                user_text="inspect",
                images=[_img()],
                ng_images=None,
                roi=None,
                text_query=None,
                success_criteria=None,
                directives=_directives(),
                engine_settings=_engine_settings(),
            )
    await asyncio.sleep(0.05)
    result = await manager.cancel_execution(eid)
    assert result == "already_completed"


@pytest.mark.asyncio
async def test_cancel_running_execution_marks_cancelled():
    manager = ExecutionManager()
    cancel_event = asyncio.Event()

    async def blocking_run(*args, **kwargs):
        await cancel_event.wait()
        return _success_result()

    with patch("backend.services.execution_manager.Orchestrator") as MockOrch, \
         patch("backend.services.execution_manager.create_adapter"):
        MockOrch.return_value.run = blocking_run
        eid = await manager.start_execution(
            user_text="test",
            images=[_img()],
            ng_images=None,
            roi=None,
            text_query=None,
            success_criteria=None,
            directives=_directives(),
            engine_settings=_engine_settings(),
        )
        await asyncio.sleep(0.02)  # let task start running
        result = await manager.cancel_execution(eid)
    assert result == "cancelled"
    status = await manager.get_status(eid)
    assert status["status"] == "cancelled"


# ── list_executions ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_executions_empty_initially():
    manager = ExecutionManager()
    result = await manager.list_executions()
    assert result == []


@pytest.mark.asyncio
async def test_list_executions_returns_all():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = AsyncMock(return_value=_success_result())
        with patch("backend.services.execution_manager.create_adapter"):
            eid1 = await manager.start_execution(
                user_text="test1", images=[_img()], ng_images=None,
                roi=None, text_query=None, success_criteria=None,
                directives=_directives(), engine_settings=_engine_settings(),
            )
            eid2 = await manager.start_execution(
                user_text="test2", images=[_img()], ng_images=None,
                roi=None, text_query=None, success_criteria=None,
                directives=_directives(), engine_settings=_engine_settings(),
            )
    await asyncio.sleep(0.05)
    executions = await manager.list_executions()
    ids = [e["execution_id"] for e in executions]
    assert eid1 in ids
    assert eid2 in ids
    assert len(executions) == 2


@pytest.mark.asyncio
async def test_list_executions_each_entry_has_required_keys():
    manager = ExecutionManager()
    with patch("backend.services.execution_manager.Orchestrator") as MockOrch:
        MockOrch.return_value.run = AsyncMock(return_value=_success_result())
        with patch("backend.services.execution_manager.create_adapter"):
            await manager.start_execution(
                user_text="test", images=[_img()], ng_images=None,
                roi=None, text_query=None, success_criteria=None,
                directives=_directives(), engine_settings=_engine_settings(),
            )
    await asyncio.sleep(0.05)
    executions = await manager.list_executions()
    for entry in executions:
        assert "execution_id" in entry
        assert "status" in entry
        assert "created_at" in entry
