from typing import Optional

from fastapi import APIRouter, Query

from backend.services.logger import clear_logs, get_agent_names, get_logs

router = APIRouter(tags=["logs"])


@router.get("/logs/agents")
async def list_log_agents():
    return {"agents": get_agent_names()}


@router.get("/logs")
async def list_logs(
    agent_name: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=10000),
):
    logs = get_logs(agent_name=agent_name, level=level, limit=limit)
    return {"logs": logs, "total": len(logs)}


@router.delete("/logs")
async def delete_logs():
    clear_logs()
    return {"cleared": True}
