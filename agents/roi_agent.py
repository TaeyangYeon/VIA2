"""ROIAgent — thin HTTP client for Grounding DINO + SAM 2 ROI detection."""
import base64
import time
from typing import Optional

import cv2
import httpx
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult


class ROIAgent(BaseAgent):
    def __init__(self, remote_url: str, directive: str = "") -> None:
        super().__init__(name="roi_agent", directive=directive)
        self.remote_url = remote_url

    async def run(
        self,
        image: np.ndarray,
        roi: Optional[dict] = None,
        text_query: Optional[str] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.perf_counter()

        h, w = image.shape[:2]
        if h < 3 or w < 3:
            return AgentResult(
                status="error",
                data={},
                error_message="Image too small for ROI analysis",
            )

        if text_query is not None:
            return await self._run_auto(image, text_query, t0)

        if roi is not None:
            return self._run_manual(image, roi, t0)

        return AgentResult(
            status="error",
            data={},
            error_message="No ROI or text query provided",
        )

    def _run_manual(self, image: np.ndarray, roi: dict, t0: float) -> AgentResult:
        h, w = image.shape[:2]
        x1 = max(0, int(roi["x1"]))
        y1 = max(0, int(roi["y1"]))
        x2 = min(w, int(roi["x2"]))
        y2 = min(h, int(roi["y2"]))

        if x2 - x1 < 1 or y2 - y1 < 1:
            return AgentResult(
                status="error",
                data={},
                error_message="ROI has zero width or height after clamping to image bounds",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        roi_w = x2 - x1
        roi_h = y2 - y1
        area_ratio = (roi_w * roi_h) / (w * h)
        aspect_ratio = roi_w / roi_h

        return AgentResult(
            status="success",
            data={
                "mode": "manual",
                "roi": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "roi_stats": {"area_ratio": area_ratio, "aspect_ratio": aspect_ratio},
            },
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )

    async def _run_auto(
        self, image: np.ndarray, text_query: str, t0: float
    ) -> AgentResult:
        _, jpeg_bytes = cv2.imencode(".jpg", image)
        image_b64 = base64.b64encode(jpeg_bytes.tobytes()).decode("utf-8")

        dino_data = None
        dino_error: Optional[str] = None

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.remote_url}/grounding_dino/detect",
                    json={"image": image_b64, "text_query": text_query, "threshold": 0.3},
                    timeout=60.0,
                )
                raw = resp.json()
                if "boxes" not in raw:
                    raise ValueError("missing boxes key")
                dino_data = raw
            except httpx.ConnectError:
                dino_error = f"Grounding DINO server unreachable: {self.remote_url}"
            except Exception:
                dino_error = "Invalid Grounding DINO response format"

            if dino_data is None:
                return AgentResult(
                    status="error",
                    data={},
                    error_message=dino_error,
                    execution_time_ms=(time.perf_counter() - t0) * 1000.0,
                )

            boxes = dino_data.get("boxes", [])
            scores = dino_data.get("scores", [])
            labels = dino_data.get("labels", [])

            if not boxes:
                return AgentResult(
                    status="success",
                    data={
                        "mode": "auto",
                        "query": text_query,
                        "detections": [],
                        "recommended_roi": None,
                        "message": f"No objects found for query: {text_query}",
                    },
                    execution_time_ms=(time.perf_counter() - t0) * 1000.0,
                )

            detections = [
                {
                    "box": boxes[i],
                    "score": scores[i] if i < len(scores) else 0.0,
                    "label": labels[i] if i < len(labels) else "",
                }
                for i in range(len(boxes))
            ]

            sam2_data = None
            try:
                resp = await client.post(
                    f"{self.remote_url}/sam2/segment",
                    json={"image": image_b64, "boxes": boxes},
                    timeout=60.0,
                )
                raw = resp.json()
                if "masks" not in raw:
                    raise ValueError("missing masks key")
                sam2_data = raw
            except httpx.ConnectError:
                pass
            except Exception:
                pass

        if sam2_data is not None:
            masks = sam2_data.get("masks", [])
            sam2_scores = sam2_data.get("scores", [])
            confidence = float(sam2_scores[0]) if sam2_scores else (float(scores[0]) if scores else 0.0)
            recommended_roi = None
            if masks:
                bbox = masks[0].get("bbox", [])
                if len(bbox) == 4:
                    recommended_roi = {"x1": bbox[0], "y1": bbox[1], "x2": bbox[2], "y2": bbox[3]}
        else:
            masks = []
            confidence = float(scores[0]) if scores else 0.0
            b = boxes[0]
            recommended_roi = {"x1": b[0], "y1": b[1], "x2": b[2], "y2": b[3]}

        return AgentResult(
            status="success",
            data={
                "mode": "auto",
                "query": text_query,
                "detections": detections,
                "recommended_roi": recommended_roi,
                "masks": masks,
                "confidence": confidence,
            },
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )
