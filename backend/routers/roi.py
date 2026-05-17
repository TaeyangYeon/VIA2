from typing import Optional
from fastapi import APIRouter

from backend.models.roi import ROICoordinates
from backend.services import roi_store

router = APIRouter()


@router.get("/roi")
async def get_roi() -> Optional[ROICoordinates]:
    return roi_store.get()


@router.post("/roi")
async def set_roi(roi: ROICoordinates) -> ROICoordinates:
    return roi_store.set(roi)


@router.delete("/roi")
async def clear_roi():
    roi_store.clear()
    return {"message": "ROI cleared"}
