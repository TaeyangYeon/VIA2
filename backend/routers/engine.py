from fastapi import APIRouter

from backend.models.engine import EngineSettings
from backend.services import engine_store

router = APIRouter()


@router.get("/engine")
async def get_engine_settings() -> EngineSettings:
    return engine_store.get_settings()


@router.post("/engine")
async def update_engine_settings(settings: EngineSettings) -> EngineSettings:
    return engine_store.update_settings(settings)
