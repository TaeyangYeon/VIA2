"""ImageAnalysisAgent — pure OpenCV image analysis, no LLM calls."""
import time
from typing import Optional

import cv2
import numpy as np

from agents.base_agent import BaseAgent
from agents.models import AgentResult, ImageDiagnosis


class ImageAnalysisAgent(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__(name="image_analysis", directive=directive)

    async def run(
        self,
        image: np.ndarray,
        roi: Optional[dict] = None,
        **kwargs,
    ) -> AgentResult:
        t0 = time.perf_counter()

        img = _crop_roi(image, roi)
        is_gray_input = img.ndim == 2 or (img.ndim == 3 and img.shape[2] == 1)
        gray = _to_gray(img)

        contrast = _contrast(gray)
        noise_level = _noise_level(gray)
        edge_density = _edge_density(gray)
        lighting_uniformity, illumination_type = _lighting(gray)
        noise_frequency = _noise_frequency(gray)
        reflection_level = _reflection_level(gray)
        blob_feasibility, blob_count_estimate = _blob_analysis(gray, contrast)
        color_discriminability = _color_discriminability(img, is_gray_input)
        dominant_channel_ratio = _dominant_channel_ratio(img, is_gray_input)
        structural_regularity = _structural_regularity(gray)
        pattern_repetition = _pattern_repetition(gray)
        threshold_candidate = _threshold_candidate(gray)
        edge_sharpness = _edge_sharpness(gray)
        optimal_color_space = _optimal_color_space(
            img, is_gray_input, color_discriminability
        )

        diagnosis = ImageDiagnosis(
            contrast=contrast,
            noise_level=noise_level,
            edge_density=edge_density,
            lighting_uniformity=lighting_uniformity,
            illumination_type=illumination_type,
            noise_frequency=noise_frequency,
            reflection_level=reflection_level,
            surface_type="",
            depth_complexity=0.0,
            has_shadow_region=False,
            blob_feasibility=blob_feasibility,
            blob_count_estimate=blob_count_estimate,
            color_discriminability=color_discriminability,
            dominant_channel_ratio=dominant_channel_ratio,
            structural_regularity=structural_regularity,
            pattern_repetition=pattern_repetition,
            optimal_color_space=optimal_color_space,
            threshold_candidate=threshold_candidate,
            edge_sharpness=edge_sharpness,
        )

        return AgentResult(
            status="success",
            data={"diagnosis": diagnosis},
            execution_time_ms=(time.perf_counter() - t0) * 1000.0,
        )


# ── preprocessing ─────────────────────────────────────────────────────────────

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


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    if image.ndim == 3 and image.shape[2] == 1:
        return image[:, :, 0]
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# ── basic optical metrics ──────────────────────────────────────────────────────

def _contrast(gray: np.ndarray) -> float:
    """RMS contrast: std of normalised pixel values."""
    return float(np.std(gray.astype(np.float64)) / 255.0)


def _noise_level(gray: np.ndarray) -> float:
    """Laplacian variance — proxy for high-frequency noise energy."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _edge_density(gray: np.ndarray) -> float:
    """Fraction of pixels classified as edges by Canny."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    edges = cv2.Canny(gray, 100, 200)
    return float(np.count_nonzero(edges) / edges.size)


def _lighting(gray: np.ndarray) -> tuple[float, str]:
    """Returns (uniformity_cv, illumination_type).

    uniformity = coefficient of variation of 4×4 block luminance means.
    """
    h, w = gray.shape
    n = min(4, h, w)
    if n < 1:
        return 0.0, "uniform"

    bh = max(1, h // n)
    bw = max(1, w // n)

    block_means = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            block = gray[i * bh : min((i + 1) * bh, h), j * bw : min((j + 1) * bw, w)]
            block_means[i, j] = float(np.mean(block)) if block.size > 0 else 0.0

    flat = block_means.flatten()
    overall_mean = float(np.mean(flat))
    uniformity = float(np.std(flat) / (overall_mean + 1e-6))
    itype = _classify_illumination(block_means, uniformity, overall_mean)
    return uniformity, itype


def _classify_illumination(
    bm: np.ndarray, cv: float, overall_mean: float
) -> str:
    n = bm.shape[0]

    if cv < 0.05:
        return "uniform"

    if n >= 4:
        ci, cj = n // 2 - 1, n // 2 - 1
        center_mean = float(bm[ci : ci + 2, cj : cj + 2].mean())
        n_edge = n * n - 4
        edge_sum = float(bm.sum()) - float(bm[ci : ci + 2, cj : cj + 2].sum())
        edge_mean = edge_sum / max(1, n_edge)
        if center_mean > edge_mean * 1.5 and center_mean > overall_mean * 1.1:
            return "spot"

    xs = np.arange(n, dtype=np.float64)
    r_row = _corrcoef(bm.mean(axis=1), xs)
    r_col = _corrcoef(bm.mean(axis=0), xs)
    if max(r_row, r_col) > 0.85:
        return "gradient"

    return "uneven"


def _corrcoef(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) < 1e-6 or np.std(b) < 1e-6:
        return 0.0
    return float(abs(np.corrcoef(a, b)[0, 1]))


def _noise_frequency(gray: np.ndarray) -> str:
    """Classify dominant frequency content via FFT energy distribution."""
    h, w = gray.shape
    if h < 4 or w < 4:
        return "low_freq"

    fft_shift = np.fft.fftshift(np.fft.fft2(gray.astype(np.float32)))
    magnitude = np.abs(fft_shift)

    cy, cx = h // 2, w // 2
    ys, xs = np.ogrid[:h, :w]
    dist = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2)
    max_dist = float(np.sqrt(cy ** 2 + cx ** 2))
    threshold = max_dist * 0.3

    total_energy = float(magnitude.sum())
    if total_energy < 1e-10:
        return "low_freq"

    high_energy = float(magnitude[dist > threshold].sum())
    return "high_freq" if high_energy / total_energy > 0.5 else "low_freq"


def _reflection_level(gray: np.ndarray) -> float:
    """Fraction of pixels with intensity > 230 (near-saturated)."""
    return float(np.count_nonzero(gray > 230) / max(1, gray.size))


# ── blob analysis ─────────────────────────────────────────────────────────────

def _blob_analysis(gray: np.ndarray, contrast: float) -> tuple[float, int]:
    """Returns (blob_feasibility, blob_count_estimate)."""
    h, w = gray.shape
    if h < 2 or w < 2:
        return float(np.clip(contrast * 2.0, 0.0, 1.0)), 0

    try:
        otsu_val, thresh_img = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
    except cv2.error:
        return float(np.clip(contrast * 2.0, 0.0, 1.0)), 0

    try:
        n_labels, _, stats, _ = cv2.connectedComponentsWithStats(
            thresh_img, connectivity=8
        )
    except cv2.error:
        return float(np.clip(contrast * 2.0, 0.0, 1.0)), 0

    min_area = max(4, gray.size // 1000)
    blob_count = sum(
        1 for i in range(1, n_labels) if stats[i, cv2.CC_STAT_AREA] >= min_area
    )

    blob_feasibility = float(np.clip(contrast * 2.0, 0.0, 1.0))
    return blob_feasibility, blob_count


# ── colour metrics ────────────────────────────────────────────────────────────

def _color_discriminability(image: np.ndarray, is_gray: bool) -> float:
    """Mean of pairwise channel differences, normalised to [0, 1]."""
    if is_gray or image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
        return 0.0
    b = image[:, :, 0].astype(np.float64)
    g = image[:, :, 1].astype(np.float64)
    r = image[:, :, 2].astype(np.float64)
    max_diff = max(
        float(np.abs(b - g).mean()),
        float(np.abs(b - r).mean()),
        float(np.abs(g - r).mean()),
    )
    return float(np.clip(max_diff / 128.0, 0.0, 1.0))


def _dominant_channel_ratio(image: np.ndarray, is_gray: bool) -> float:
    """max channel mean / sum of channel means."""
    if is_gray or image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
        return 1.0
    means = [float(image[:, :, c].mean()) for c in range(image.shape[2])]
    total = sum(means) + 1e-6
    return float(np.clip(max(means) / total, 0.0, 1.0))


# ── structure / regularity ────────────────────────────────────────────────────

def _structural_regularity(gray: np.ndarray) -> float:
    """Normalised autocorrelation at a small shift — high = more regular."""
    h, w = gray.shape
    if h < 4 or w < 4:
        return 0.5

    g = gray.astype(np.float64)
    g_norm = g - g.mean()
    var = float(g_norm.var())
    if var < 1e-10:
        return 1.0

    shift = max(1, min(h, w) // 8)
    corr = float(
        np.mean(g_norm[shift:, shift:] * g_norm[: h - shift, : w - shift]) / var
    )
    return float(np.clip((corr + 1.0) / 2.0, 0.0, 1.0))


def _pattern_repetition(gray: np.ndarray) -> float:
    """Peak of the off-centre normalised autocorrelation function."""
    h, w = gray.shape
    if h < 4 or w < 4:
        return 0.0

    g = gray.astype(np.float64) - gray.mean()
    power = float(np.abs(np.fft.fft2(g) ** 2).real.sum())
    if power < 1e-10:
        return 0.0

    acf = np.fft.ifft2(np.abs(np.fft.fft2(g)) ** 2).real
    acf_norm = np.fft.fftshift(acf / (acf[0, 0] + 1e-10))

    cy, cx = h // 2, w // 2
    excl = max(2, min(h, w) // 8)
    acf_norm[cy - excl : cy + excl + 1, cx - excl : cx + excl + 1] = 0.0
    return float(np.clip(float(np.max(np.abs(acf_norm))), 0.0, 1.0))


# ── processing hints ──────────────────────────────────────────────────────────

def _threshold_candidate(gray: np.ndarray) -> float:
    """Otsu threshold value."""
    if gray.size == 0:
        return 0.0
    try:
        val, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return float(val)
    except cv2.error:
        return float(np.mean(gray))


def _edge_sharpness(gray: np.ndarray) -> float:
    """Mean Sobel gradient magnitude — proxy for overall edge sharpness."""
    if gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    sx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return float(np.mean(np.sqrt(sx ** 2 + sy ** 2)))


def _optimal_color_space(
    image: np.ndarray, is_gray: bool, color_discriminability: float
) -> str:
    """Recommend an analysis colour space based on image characteristics."""
    if is_gray or image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
        return "gray"
    if color_discriminability > 0.4:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if float(hsv[:, :, 1].mean()) > 30.0:
            return "hsv_s"
        return "lab_l"
    return "bgr"
