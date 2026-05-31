"""Light Test analysis, PBR rendering, histogram, and preset router (Steps 43–48)."""
import asyncio
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from agents.depth_agent import DepthAgent
from agents.material_agent import MaterialAgent
from backend.models.engine import EngineMode
from backend.services import engine_store, image_store

router = APIRouter()

# ── module-level preset store ─────────────────────────────────────────────────
_presets: dict[str, dict] = {}


class PresetSaveRequest(BaseModel):
    name: str
    lights: list[dict]
    lens_polarizer_angle: float = 0.0
    description: str = ""


class RenderRequest(BaseModel):
    image_id: str
    depth_map_base64: str | None = None
    lights: list[dict] = []
    surface_type: str = "default"
    lens_polarizer_angle: float = 0.0


class HistogramRequest(BaseModel):
    image_base64: str


def _depth_map_to_base64(depth_map: np.ndarray) -> str:
    d_min = float(depth_map.min())
    d_max = float(depth_map.max())
    if d_max > d_min:
        uint8_map = ((depth_map - d_min) / (d_max - d_min) * 255).astype(np.uint8)
    else:
        uint8_map = np.zeros_like(depth_map, dtype=np.uint8)
    _, encoded = cv2.imencode(".png", uint8_map)
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


@router.post("/light_test/analyze")
async def analyze_light_test(file: UploadFile) -> dict[str, Any]:
    settings = engine_store.get_settings()

    if settings.mode == EngineMode.local or settings.remote_url is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Light Test analysis requires remote AI engine (Colab). "
                "Please configure remote engine settings."
            ),
        )

    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=422, detail="Invalid image file")

    depth_agent = DepthAgent(remote_url=settings.remote_url)
    material_agent = MaterialAgent(remote_url=settings.remote_url)

    depth_result, material_result = await asyncio.gather(
        depth_agent.run(image=image),
        material_agent.run(image=image),
    )

    depth_response: dict[str, Any] = {
        "status": depth_result.status,
        "depth_stats": None,
        "depth_map_shape": None,
        "depth_map_base64": None,
        "error_message": depth_result.error_message,
    }
    if depth_result.status == "success":
        depth_map = depth_result.data.get("depth_map")
        depth_response["depth_stats"] = depth_result.data.get("depth_stats")
        if depth_map is not None:
            depth_response["depth_map_shape"] = list(depth_map.shape[:2])
            depth_response["depth_map_base64"] = _depth_map_to_base64(depth_map)

    material_response: dict[str, Any] = {
        "status": material_result.status,
        "surface_type": None,
        "material_map": None,
        "confidence": None,
        "error_message": material_result.error_message,
    }
    if material_result.status == "success":
        material_response["surface_type"] = material_result.data.get("surface_type")
        material_response["material_map"] = material_result.data.get("material_map")
        material_response["confidence"] = material_result.data.get("confidence")

    if depth_result.status == "success" and material_result.status == "success":
        overall_status = "success"
    elif depth_result.status == "error" and material_result.status == "error":
        overall_status = "error"
    else:
        overall_status = "partial"

    return {
        "status": overall_status,
        "depth": depth_response,
        "material": material_response,
    }


@router.post("/light_test/render")
async def render_light_test(request: RenderRequest) -> dict[str, Any]:
    """Apply PBR rendering with depth-based shadows to the stored image."""
    from light_test.renderer import PBRRenderer

    metadata = image_store.get_by_id(request.image_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Image not found")

    file_path = Path(metadata.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    image = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=422, detail="Failed to read image file")

    depth_map: np.ndarray | None = None
    if request.depth_map_base64:
        try:
            depth_bytes = base64.b64decode(request.depth_map_base64)
            depth_array = np.frombuffer(depth_bytes, np.uint8)
            depth_img = cv2.imdecode(depth_array, cv2.IMREAD_GRAYSCALE)
            if depth_img is not None:
                depth_map = depth_img.astype(np.float32) / 255.0
        except Exception:
            depth_map = None

    h, w = image.shape[:2]
    renderer = PBRRenderer()
    rendered = renderer.render(
        image=image,
        depth_map=depth_map,
        lights=request.lights,
        surface_type=request.surface_type,
        image_width=w,
        image_height=h,
        lens_polarizer_angle=request.lens_polarizer_angle,
    )

    _, encoded = cv2.imencode(".png", rendered)
    rendered_b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return {"rendered_image": rendered_b64}


@router.post("/light_test/histogram")
async def compute_light_test_histogram(request: HistogramRequest) -> dict[str, Any]:
    """Compute per-channel histogram for a base64-encoded image."""
    from light_test.polarization import compute_histogram

    try:
        img_bytes = base64.b64decode(request.image_base64)
        img_array = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid image_base64")

    if image is None:
        raise HTTPException(status_code=422, detail="Failed to decode image")

    return compute_histogram(image)


# ── preset endpoints ──────────────────────────────────────────────────────────

@router.post("/light_test/preset/save")
async def save_preset(request: PresetSaveRequest) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    _presets[request.name] = {
        "name": request.name,
        "lights": request.lights,
        "lens_polarizer_angle": request.lens_polarizer_angle,
        "description": request.description,
        "created_at": created_at,
    }
    return {"status": "saved", "name": request.name, "created_at": created_at}


@router.get("/light_test/preset/list")
async def list_presets() -> dict[str, Any]:
    return {
        "presets": [
            {
                "name": p["name"],
                "description": p["description"],
                "created_at": p["created_at"],
            }
            for p in _presets.values()
        ]
    }


@router.get("/light_test/preset/{name}")
async def get_preset(name: str) -> dict[str, Any]:
    if name not in _presets:
        raise HTTPException(status_code=404, detail="Preset not found")
    return _presets[name]


@router.delete("/light_test/preset/{name}")
async def delete_preset(name: str) -> dict[str, Any]:
    if name not in _presets:
        raise HTTPException(status_code=404, detail="Preset not found")
    del _presets[name]
    return {"status": "deleted", "name": name}
