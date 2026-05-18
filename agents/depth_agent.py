"""DepthAgent — thin client for remote Depth-Anything-V2 inference."""
import base64
import time
from typing import Optional

import cv2
import httpx
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult


class DepthAgent(BaseAgent):
    def __init__(self, remote_url: str, directive: str = "") -> None:
        super().__init__(name="depth_agent", directive=directive)
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
                error_message="Image too small for depth estimation",
            )

        _, jpeg_bytes = cv2.imencode(".jpg", image)
        image_b64 = base64.b64encode(jpeg_bytes.tobytes()).decode("utf-8")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.remote_url}/depth",
                    json={"image": image_b64},
                    timeout=30.0,
                )
            response_data = response.json()
        except Exception:
            return AgentResult(
                status="error",
                data={},
                error_message=f"Depth server unreachable: {self.remote_url}",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        try:
            depth_b64 = response_data["depth_map"]
            shape = response_data["shape"]
            depth_map = np.frombuffer(base64.b64decode(depth_b64), dtype=np.float32).reshape(shape)
        except Exception:
            return AgentResult(
                status="error",
                data={},
                error_message="Invalid depth response format",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        depth_stats = _compute_depth_stats(depth_map, roi)

        return AgentResult(
            status="success",
            data={"depth_map": depth_map, "depth_stats": depth_stats},
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )


def _compute_depth_stats(depth_map: np.ndarray, roi: Optional[dict]) -> dict:
    d = _crop_roi(depth_map, roi)

    depth_mean = float(np.mean(d))
    depth_range = float(np.max(d) - np.min(d))
    depth_std = float(np.std(d))
    depth_complexity = float(min(depth_std * 2.0, 1.0))

    if d.shape[0] >= 3 and d.shape[1] >= 3:
        sx = cv2.Sobel(d, cv2.CV_64F, 1, 0, ksize=3)
        sy = cv2.Sobel(d, cv2.CV_64F, 0, 1, ksize=3)
        depth_gradient_max = float(np.max(np.sqrt(sx ** 2 + sy ** 2)))
    else:
        depth_gradient_max = 0.0

    has_shadow_region = depth_gradient_max > 0.3

    return {
        "depth_complexity": depth_complexity,
        "has_shadow_region": has_shadow_region,
        "depth_range": depth_range,
        "depth_mean": depth_mean,
        "depth_gradient_max": depth_gradient_max,
    }


def _crop_roi(depth_map: np.ndarray, roi: Optional[dict]) -> np.ndarray:
    if roi is None:
        return depth_map
    h, w = depth_map.shape[:2]
    x1 = max(0, int(roi["x1"]))
    y1 = max(0, int(roi["y1"]))
    x2 = min(w, int(roi["x2"]))
    y2 = min(h, int(roi["y2"]))
    if x2 <= x1 or y2 <= y1:
        return depth_map
    return depth_map[y1:y2, x1:x2]
