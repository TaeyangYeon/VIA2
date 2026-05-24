"""ExecutionManager — manages async pipeline execution lifecycle."""
from __future__ import annotations

import asyncio
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

from agents.models import AgentDirectives, AgentResult
from agents.orchestrator import Orchestrator
from backend.models.engine import EngineSettings
from backend.services.ai_adapter.factory import create_adapter


class _ExecutionRecord:
    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        self.status: str = "pending"
        self.result: Optional[AgentResult] = None
        self.error: Optional[str] = None
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None
        self.task: Optional[asyncio.Task] = None


class ExecutionManager:
    """Thread-safe async manager for Orchestrator pipeline executions."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._executions: dict[str, _ExecutionRecord] = {}

    async def start_execution(
        self,
        user_text: str,
        images: list,
        ng_images: list | None,
        roi: dict | None,
        text_query: str | None,
        success_criteria: dict | None,
        directives: AgentDirectives,
        engine_settings: EngineSettings,
    ) -> str:
        execution_id = str(uuid.uuid4())
        record = _ExecutionRecord(execution_id)

        async with self._lock:
            self._executions[execution_id] = record

        task = asyncio.create_task(
            self._run(
                record, user_text, images, ng_images, roi,
                text_query, success_criteria, directives, engine_settings,
            )
        )
        record.task = task
        return execution_id

    async def _run(
        self,
        record: _ExecutionRecord,
        user_text: str,
        images: list,
        ng_images: list | None,
        roi: dict | None,
        text_query: str | None,
        success_criteria: dict | None,
        directives: AgentDirectives,
        engine_settings: EngineSettings,
    ) -> None:
        async with self._lock:
            record.status = "running"

        try:
            adapter = create_adapter(engine_settings)
            orchestrator = Orchestrator(
                adapter=adapter,
                remote_url=engine_settings.remote_url or "",
                model=engine_settings.model_name,
                max_iterations=3,
                directives=directives,
            )
            result = await orchestrator.run(
                user_text=user_text,
                images=images,
                ng_images=ng_images,
                roi=roi,
                text_query=text_query,
                success_criteria=success_criteria,
            )
            async with self._lock:
                record.result = result
                record.status = "completed" if result.status == "success" else "failed"
                if result.status != "success":
                    record.error = result.error_message
                record.completed_at = datetime.now(timezone.utc).isoformat()

        except asyncio.CancelledError:
            async with self._lock:
                if record.status != "cancelled":
                    record.status = "cancelled"
                    record.completed_at = datetime.now(timezone.utc).isoformat()
            raise

        except Exception as exc:
            async with self._lock:
                record.status = "failed"
                record.error = str(exc)
                record.completed_at = datetime.now(timezone.utc).isoformat()

    async def get_status(self, execution_id: str) -> dict | None:
        async with self._lock:
            record = self._executions.get(execution_id)
            if record is None:
                return None
            return self._to_dict(record)

    async def cancel_execution(self, execution_id: str) -> str:
        """Cancel an execution. Returns 'cancelled', 'not_found', or 'already_completed'."""
        async with self._lock:
            record = self._executions.get(execution_id)
            if record is None:
                return "not_found"
            if record.status in ("completed", "failed", "cancelled"):
                return "already_completed"
            if record.task and not record.task.done():
                record.task.cancel()
            record.status = "cancelled"
            record.completed_at = datetime.now(timezone.utc).isoformat()
            return "cancelled"

    async def list_executions(self) -> list[dict]:
        async with self._lock:
            return [self._to_dict(r) for r in self._executions.values()]

    def _to_dict(self, record: _ExecutionRecord) -> dict:
        d: dict = {
            "execution_id": record.execution_id,
            "status": record.status,
            "created_at": record.created_at,
            "completed_at": record.completed_at,
        }
        if record.result is not None:
            d["result"] = record.result.data
        if record.error is not None:
            d["error"] = record.error
        return d


# ── Module-level singleton ─────────────────────────────────────────────────────

_manager: Optional[ExecutionManager] = None
_init_lock = threading.Lock()


def get_manager() -> ExecutionManager:
    global _manager
    if _manager is None:
        with _init_lock:
            if _manager is None:
                _manager = ExecutionManager()
    return _manager
