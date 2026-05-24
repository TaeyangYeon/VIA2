"""Execute router — start, query, and cancel pipeline executions."""
from __future__ import annotations

import cv2
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.lighting_advisor import LightingAdvisor
from agents.models import AgentDirectives as AgentDirectivesDataclass
from backend.services import config_store, directives_store, engine_store, image_store, roi_store
from backend.services.execution_manager import get_manager

router = APIRouter()
_advisor = LightingAdvisor()


class ExecuteRequest(BaseModel):
    user_text: str


@router.post("/execute", status_code=202)
async def start_execution(req: ExecuteRequest):
    if not req.user_text.strip():
        raise HTTPException(status_code=422, detail="user_text cannot be empty")

    all_images = image_store.get_all()
    ok_metas = [m for m in all_images if m.group == "analysis"]
    ng_metas = [m for m in all_images if m.group == "test"]

    if not ok_metas:
        raise HTTPException(status_code=422, detail="At least one image must be uploaded")

    ok_images = [img for m in ok_metas if (img := cv2.imread(m.file_path)) is not None]
    ng_images = [img for m in ng_metas if (img := cv2.imread(m.file_path)) is not None]

    if not ok_images:
        raise HTTPException(status_code=422, detail="Failed to load uploaded images from disk")

    roi_coords = roi_store.get()
    roi = roi_coords.model_dump() if roi_coords else None

    config = config_store.get()
    sc = config.success_criteria
    success_criteria: dict | None = {}
    if sc.accuracy is not None:
        success_criteria["min_accuracy"] = sc.accuracy
    if sc.fp_rate is not None:
        success_criteria["max_fp_rate"] = sc.fp_rate
    if sc.fn_rate is not None:
        success_criteria["max_fn_rate"] = sc.fn_rate
    if not success_criteria:
        success_criteria = None

    pydantic_dir = directives_store.get()
    directives = AgentDirectivesDataclass(
        orchestrator=pydantic_dir.orchestrator,
        spec=pydantic_dir.spec,
        image_analysis=pydantic_dir.image_analysis,
        depth=pydantic_dir.depth,
        material=pydantic_dir.material,
        pipeline_composer=pydantic_dir.pipeline_composer,
        vision_judge=pydantic_dir.vision_judge,
        inspection_plan=pydantic_dir.inspection_plan,
        test=pydantic_dir.test,
    )

    engine_settings = engine_store.get_settings()
    manager = get_manager()

    execution_id = await manager.start_execution(
        user_text=req.user_text,
        images=ok_images,
        ng_images=ng_images if ng_images else None,
        roi=roi,
        text_query=None,
        success_criteria=success_criteria,
        directives=directives,
        engine_settings=engine_settings,
    )

    return {"execution_id": execution_id, "status": "pending"}


@router.get("/execute")
async def list_executions():
    return await get_manager().list_executions()


@router.get("/execute/{execution_id}")
async def get_execution(execution_id: str):
    status = await get_manager().get_status(execution_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    if status["status"] == "completed" and "result" in status:
        scene_ctx = status["result"].get("scene_context") or {}
        status["result"]["lighting_suggestions"] = _advisor.generate_recommendations(scene_ctx)

    return status


@router.delete("/execute/{execution_id}")
async def cancel_execution(execution_id: str):
    result = await get_manager().cancel_execution(execution_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Execution not found")
    if result == "already_completed":
        raise HTTPException(status_code=409, detail="Execution already completed or cancelled")
    return {"message": "Execution cancelled", "execution_id": execution_id}
