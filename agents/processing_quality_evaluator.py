"""Pure OpenCV quality scorer for image processing pipelines."""
from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class QualityScore:
    contrast_score: float
    noise_score: float
    edge_score: float
    overall_score: float
    details: dict = field(default_factory=dict)


class ProcessingQualityEvaluator:
    def evaluate(
        self, original: np.ndarray, processed: np.ndarray, purpose: str = ""
    ) -> QualityScore:
        proc_gray = self._to_gray(processed)

        # Degenerate: processed is constant (all black or all white)
        if float(proc_gray.std()) < 1.0:
            return QualityScore(
                contrast_score=0.0,
                noise_score=0.0,
                edge_score=0.0,
                overall_score=0.0,
                details={"degenerate": True},
            )

        orig_gray = self._to_gray(original)

        # Contrast score: higher std in processed = better
        orig_std = float(orig_gray.std())
        proc_std = float(proc_gray.std())
        contrast_score = min(1.0, proc_std / max(orig_std, 1.0))

        # Noise score: Laplacian variance ratio — less HF energy in processed = better
        orig_lap_var = float(cv2.Laplacian(orig_gray, cv2.CV_64F).var())
        proc_lap_var = float(cv2.Laplacian(proc_gray, cv2.CV_64F).var())
        noise_score = min(1.0, orig_lap_var / max(proc_lap_var, 1.0))

        # Edge score: Canny edge pixel ratio — preserve or enhance edges
        orig_gray_u8 = orig_gray if orig_gray.dtype == np.uint8 else np.clip(orig_gray, 0, 255).astype(np.uint8)
        proc_gray_u8 = proc_gray if proc_gray.dtype == np.uint8 else np.clip(proc_gray, 0, 255).astype(np.uint8)
        orig_edge_count = float(cv2.Canny(orig_gray_u8, 50, 150).sum()) / 255.0
        proc_edge_count = float(cv2.Canny(proc_gray_u8, 50, 150).sum()) / 255.0
        edge_score = min(1.0, proc_edge_count / max(orig_edge_count, 1.0))

        # Clamp all sub-scores
        contrast_score = max(0.0, min(1.0, contrast_score))
        noise_score = max(0.0, min(1.0, noise_score))
        edge_score = max(0.0, min(1.0, edge_score))

        overall_score = 0.3 * contrast_score + 0.3 * noise_score + 0.4 * edge_score

        return QualityScore(
            contrast_score=contrast_score,
            noise_score=noise_score,
            edge_score=edge_score,
            overall_score=overall_score,
            details={
                "orig_std": orig_std,
                "proc_std": proc_std,
                "orig_lap_var": orig_lap_var,
                "proc_lap_var": proc_lap_var,
                "orig_edge_count": orig_edge_count,
                "proc_edge_count": proc_edge_count,
            },
        )

    def _to_gray(self, img: np.ndarray) -> np.ndarray:
        if img.ndim == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img
