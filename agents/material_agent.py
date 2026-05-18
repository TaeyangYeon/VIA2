"""MaterialAgent — thin HTTP client for Florence-2 and DINOv2 material classification."""
import base64
import time
from typing import Optional

import cv2
import httpx
import numpy as np

from agents.base_agent import BaseAgent
from agents.material_lut import MATERIAL_LUT
from agents.models import AgentResult


class MaterialAgent(BaseAgent):
    def __init__(self, remote_url: str, directive: str = "") -> None:
        super().__init__(name="material_agent", directive=directive)
        self.remote_url = remote_url

    async def run(
        self,
        image: np.ndarray,
        roi: Optional[dict] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.perf_counter()

        h, w = image.shape[:2]
        if h < 3 or w < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="Image too small for material analysis",
            )

        work_image = _crop_roi(image, roi)
        _, jpeg_bytes = cv2.imencode(".jpg", work_image)
        image_b64 = base64.b64encode(jpeg_bytes.tobytes()).decode("utf-8")

        florence_data = None
        dinov2_data = None
        florence_error: Optional[str] = None
        dinov2_error: Optional[str] = None

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.remote_url}/florence2/caption",
                    json={"image": image_b64},
                    timeout=60.0,
                )
                raw = resp.json()
                if "regions" not in raw:
                    raise ValueError("missing regions key")
                florence_data = raw
            except httpx.ConnectError:
                florence_error = f"Florence-2 server unreachable: {self.remote_url}"
            except Exception:
                florence_error = "Invalid Florence-2 response format"

            try:
                resp = await client.post(
                    f"{self.remote_url}/dinov2/features",
                    json={"image": image_b64},
                    timeout=60.0,
                )
                raw = resp.json()
                if "features" not in raw:
                    raise ValueError("missing features key")
                dinov2_data = raw
            except httpx.ConnectError:
                dinov2_error = f"DINOv2 server unreachable: {self.remote_url}"
            except Exception:
                dinov2_error = "Invalid DINOv2 response format"

        if florence_data is None and dinov2_data is None:
            return AgentResult(
                status="error",
                data={},
                error_message=florence_error or dinov2_error,
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        regions = florence_data.get("regions", []) if florence_data else []
        surface_type, material_map = _classify_from_regions(regions)

        feature_stats: dict = {"feature_dim": 0, "feature_norm": 0.0, "top_similarities": {}}
        if dinov2_data:
            features = dinov2_data.get("features", [])
            feature_stats = _compute_feature_stats(features)
            if features and not surface_type:
                top_sims = feature_stats["top_similarities"]
                if top_sims:
                    surface_type = max(top_sims, key=lambda k: top_sims[k])

        if not surface_type:
            surface_type = "unknown"

        both_ok = florence_data is not None and dinov2_data is not None
        base_conf = 0.85 if both_ok else 0.5
        if regions:
            top_conf = max((r.get("confidence", 0.5) for r in regions), default=0.5)
            confidence = float(min(base_conf * top_conf, 1.0))
        else:
            confidence = float(base_conf * 0.5)

        return AgentResult(
            status="success",
            data={
                "surface_type": surface_type,
                "material_map": material_map,
                "confidence": confidence,
                "regions": regions,
                "feature_stats": feature_stats,
            },
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )


def _crop_roi(image: np.ndarray, roi: Optional[dict]) -> np.ndarray:
    if roi is None:
        return image
    h, w = image.shape[:2]
    x1 = max(0, int(roi["x1"]))
    y1 = max(0, int(roi["y1"]))
    x2 = min(w, int(roi["x2"]))
    y2 = min(h, int(roi["y2"]))
    if x2 <= x1 or y2 <= y1:
        return image
    return image[y1:y2, x1:x2]


def _cosine_similarity(a: list, b: list) -> float:
    a_arr = np.array(a, dtype=np.float64)
    b_arr = np.array(b, dtype=np.float64)
    norm_a = float(np.linalg.norm(a_arr))
    norm_b = float(np.linalg.norm(b_arr))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


def _classify_from_regions(regions: list) -> tuple:
    if not regions:
        return "", {}
    material_map: dict = {}
    best_material = ""
    best_confidence = 0.0
    for region in regions:
        label = region.get("label", "unknown")
        confidence = float(region.get("confidence", 0.5))
        bbox = region.get("bbox", [])
        material = _normalize_label(label)
        material_map[label] = {"type": material, "confidence": confidence, "bbox": bbox}
        if confidence > best_confidence:
            best_confidence = confidence
            best_material = material
    return best_material, material_map


def _normalize_label(label: str) -> str:
    lower = label.lower()
    for material in MATERIAL_LUT:
        if material in lower:
            return material
    parts = lower.split()
    return parts[0] if parts else "unknown"


def _compute_feature_stats(features: list) -> dict:
    if not features:
        return {"feature_dim": 0, "feature_norm": 0.0, "top_similarities": {}}
    feat = features[0]
    dim = len(feat)
    norm = float(np.linalg.norm(np.array(feat, dtype=np.float64)))
    sims = {
        name: _cosine_similarity(feat, props["reference_features"])
        for name, props in MATERIAL_LUT.items()
    }
    return {"feature_dim": dim, "feature_norm": norm, "top_similarities": sims}
