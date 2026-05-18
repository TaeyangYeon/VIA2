"""Tests for ImageAnalysisAgent — pure OpenCV, no LLM calls."""
import numpy as np
import pytest

from agents.models import AgentResult, ImageDiagnosis
from agents.base_agent import BaseAgent


# ── synthetic image helpers ──────────────────────────────────────────────────

def _uniform_image(value: int = 128, size: int = 100) -> np.ndarray:
    """Solid uniform gray BGR image."""
    return np.full((size, size, 3), value, dtype=np.uint8)


def _gradient_image(size: int = 200) -> np.ndarray:
    """Horizontal gradient BGR image, black→white."""
    row = np.linspace(0, 255, size, dtype=np.uint8)
    gray = np.tile(row, (size, 1))
    return np.stack([gray, gray, gray], axis=-1)


def _noisy_image(size: int = 100, seed: int = 42) -> np.ndarray:
    """Random noise BGR image (high-frequency content)."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, (size, size, 3), dtype=np.uint8)


def _spot_image(size: int = 100) -> np.ndarray:
    """Bright circular spot on dark background (spot illumination)."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    cx, cy = size // 2, size // 2
    radius = size // 4
    ys, xs = np.ogrid[:size, :size]
    mask = (xs - cx) ** 2 + (ys - cy) ** 2 <= radius ** 2
    img[mask] = [200, 200, 200]
    return img


def _color_image(size: int = 100) -> np.ndarray:
    """BGR image with distinct channels (B=50, G=150, R=220)."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:, :, 0] = 50   # B
    img[:, :, 1] = 150  # G
    img[:, :, 2] = 220  # R
    return img


def _blob_image(size: int = 100) -> np.ndarray:
    """Dark background with a few bright blob regions."""
    img = np.full((size, size, 3), 30, dtype=np.uint8)
    # 3 blobs
    centers = [(25, 25), (75, 25), (50, 75)]
    for cx, cy in centers:
        ys, xs = np.ogrid[:size, :size]
        mask = (xs - cx) ** 2 + (ys - cy) ** 2 <= 10 ** 2
        img[mask] = [220, 220, 220]
    return img


def _get_diagnosis(result: AgentResult) -> ImageDiagnosis:
    return result.data["diagnosis"]


# ── instantiation ────────────────────────────────────────────────────────────

def test_agent_is_base_agent():
    from agents.image_analysis_agent import ImageAnalysisAgent
    assert isinstance(ImageAnalysisAgent(), BaseAgent)


def test_agent_name_is_image_analysis():
    from agents.image_analysis_agent import ImageAnalysisAgent
    assert ImageAnalysisAgent().name == "image_analysis"


def test_agent_directive_stored():
    from agents.image_analysis_agent import ImageAnalysisAgent
    agent = ImageAnalysisAgent(directive="test directive")
    assert agent.directive == "test directive"


# ── AgentResult structure ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_result_status_is_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    result = await ImageAnalysisAgent().run(image=_uniform_image())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_result_data_has_diagnosis_key():
    from agents.image_analysis_agent import ImageAnalysisAgent
    result = await ImageAnalysisAgent().run(image=_uniform_image())
    assert "diagnosis" in result.data


@pytest.mark.asyncio
async def test_result_diagnosis_is_image_diagnosis_instance():
    from agents.image_analysis_agent import ImageAnalysisAgent
    result = await ImageAnalysisAgent().run(image=_uniform_image())
    assert isinstance(result.data["diagnosis"], ImageDiagnosis)


@pytest.mark.asyncio
async def test_result_execution_time_non_negative():
    from agents.image_analysis_agent import ImageAnalysisAgent
    result = await ImageAnalysisAgent().run(image=_uniform_image())
    assert result.execution_time_ms >= 0.0


# ── metric range validation ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_contrast_non_negative():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert diag.contrast >= 0.0


@pytest.mark.asyncio
async def test_noise_level_non_negative():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_noisy_image()))
    assert diag.noise_level >= 0.0


@pytest.mark.asyncio
async def test_edge_density_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.edge_density <= 1.0


@pytest.mark.asyncio
async def test_lighting_uniformity_non_negative():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_uniform_image()))
    assert diag.lighting_uniformity >= 0.0


@pytest.mark.asyncio
async def test_reflection_level_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.reflection_level <= 1.0


@pytest.mark.asyncio
async def test_blob_feasibility_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.blob_feasibility <= 1.0


@pytest.mark.asyncio
async def test_blob_count_estimate_non_negative():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert diag.blob_count_estimate >= 0


@pytest.mark.asyncio
async def test_color_discriminability_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_color_image()))
    assert 0.0 <= diag.color_discriminability <= 1.0


@pytest.mark.asyncio
async def test_dominant_channel_ratio_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.dominant_channel_ratio <= 1.0


@pytest.mark.asyncio
async def test_structural_regularity_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.structural_regularity <= 1.0


@pytest.mark.asyncio
async def test_pattern_repetition_in_unit_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.pattern_repetition <= 1.0


@pytest.mark.asyncio
async def test_threshold_candidate_in_uint8_range():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert 0.0 <= diag.threshold_candidate <= 255.0


@pytest.mark.asyncio
async def test_edge_sharpness_non_negative():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert diag.edge_sharpness >= 0.0


# ── illumination_type classification ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_illumination_type_uniform_for_flat_image():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_uniform_image(128)))
    assert diag.illumination_type == "uniform"


@pytest.mark.asyncio
async def test_illumination_type_gradient_for_gradient_image():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert diag.illumination_type == "gradient"


@pytest.mark.asyncio
async def test_illumination_type_spot_for_spot_image():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_spot_image()))
    assert diag.illumination_type == "spot"


@pytest.mark.asyncio
async def test_illumination_type_is_always_valid():
    from agents.image_analysis_agent import ImageAnalysisAgent
    valid = {"uniform", "gradient", "spot", "uneven"}
    for img in [_uniform_image(), _gradient_image(), _noisy_image(), _spot_image()]:
        diag = _get_diagnosis(await ImageAnalysisAgent().run(image=img))
        assert diag.illumination_type in valid


# ── noise_frequency classification ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_noise_frequency_high_for_random_noise():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_noisy_image()))
    assert diag.noise_frequency == "high_freq"


@pytest.mark.asyncio
async def test_noise_frequency_low_for_uniform_image():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_uniform_image()))
    assert diag.noise_frequency == "low_freq"


@pytest.mark.asyncio
async def test_noise_frequency_is_always_valid():
    from agents.image_analysis_agent import ImageAnalysisAgent
    valid = {"high_freq", "low_freq"}
    for img in [_uniform_image(), _gradient_image(), _noisy_image()]:
        diag = _get_diagnosis(await ImageAnalysisAgent().run(image=img))
        assert diag.noise_frequency in valid


# ── comparative behavior ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gradient_has_higher_contrast_than_uniform():
    from agents.image_analysis_agent import ImageAnalysisAgent
    agent = ImageAnalysisAgent()
    grad_diag = _get_diagnosis(await agent.run(image=_gradient_image()))
    unif_diag = _get_diagnosis(await agent.run(image=_uniform_image()))
    assert grad_diag.contrast > unif_diag.contrast


@pytest.mark.asyncio
async def test_noisy_image_has_higher_noise_than_smooth():
    from agents.image_analysis_agent import ImageAnalysisAgent
    agent = ImageAnalysisAgent()
    noisy_diag = _get_diagnosis(await agent.run(image=_noisy_image()))
    smooth_diag = _get_diagnosis(await agent.run(image=_uniform_image()))
    assert noisy_diag.noise_level > smooth_diag.noise_level


@pytest.mark.asyncio
async def test_blob_image_has_positive_blob_count():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_blob_image()))
    assert diag.blob_count_estimate > 0


# ── grayscale input handling ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_grayscale_2d_returns_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    gray = np.full((100, 100), 128, dtype=np.uint8)
    result = await ImageAnalysisAgent().run(image=gray)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_grayscale_color_discriminability_is_zero():
    from agents.image_analysis_agent import ImageAnalysisAgent
    gray = np.full((100, 100), 128, dtype=np.uint8)
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=gray))
    assert diag.color_discriminability == 0.0


@pytest.mark.asyncio
async def test_grayscale_optimal_color_space_is_gray():
    from agents.image_analysis_agent import ImageAnalysisAgent
    gray = np.full((100, 100), 128, dtype=np.uint8)
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=gray))
    assert diag.optimal_color_space == "gray"


# ── ROI cropping ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_roi_analysis_returns_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    img = _gradient_image(200)
    roi = {"x1": 10, "y1": 10, "x2": 90, "y2": 90}
    result = await ImageAnalysisAgent().run(image=img, roi=roi)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_roi_restricts_analysis_to_subregion():
    """ROI on a narrow band of the gradient → lower contrast than full image."""
    from agents.image_analysis_agent import ImageAnalysisAgent
    agent = ImageAnalysisAgent()
    img = _gradient_image(200)
    full_diag = _get_diagnosis(await agent.run(image=img))
    # narrow vertical slice near center → very small value range
    roi = {"x1": 90, "y1": 0, "x2": 110, "y2": 200}
    roi_diag = _get_diagnosis(await agent.run(image=img, roi=roi))
    assert roi_diag.contrast < full_diag.contrast


# ── edge cases ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1x1_image_returns_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    img = np.array([[[128, 128, 128]]], dtype=np.uint8)
    result = await ImageAnalysisAgent().run(image=img)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_3x3_image_returns_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    img = np.full((3, 3, 3), 64, dtype=np.uint8)
    result = await ImageAnalysisAgent().run(image=img)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_all_black_image_returns_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    result = await ImageAnalysisAgent().run(image=np.zeros((100, 100, 3), dtype=np.uint8))
    assert result.status == "success"


@pytest.mark.asyncio
async def test_all_black_contrast_is_zero():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=np.zeros((100, 100, 3), dtype=np.uint8)))
    assert diag.contrast == 0.0


@pytest.mark.asyncio
async def test_all_black_reflection_level_is_zero():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=np.zeros((100, 100, 3), dtype=np.uint8)))
    assert diag.reflection_level == 0.0


@pytest.mark.asyncio
async def test_all_white_image_returns_success():
    from agents.image_analysis_agent import ImageAnalysisAgent
    result = await ImageAnalysisAgent().run(image=np.full((100, 100, 3), 255, dtype=np.uint8))
    assert result.status == "success"


@pytest.mark.asyncio
async def test_all_white_contrast_is_zero():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=np.full((100, 100, 3), 255, dtype=np.uint8)))
    assert diag.contrast == 0.0


@pytest.mark.asyncio
async def test_all_white_reflection_level_is_one():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=np.full((100, 100, 3), 255, dtype=np.uint8)))
    assert diag.reflection_level == 1.0


# ── depth/material defaults (filled by later agents) ─────────────────────────

@pytest.mark.asyncio
async def test_surface_type_is_str():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_uniform_image()))
    assert isinstance(diag.surface_type, str)


@pytest.mark.asyncio
async def test_depth_complexity_is_float():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_uniform_image()))
    assert isinstance(diag.depth_complexity, float)


@pytest.mark.asyncio
async def test_has_shadow_region_is_bool():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_uniform_image()))
    assert isinstance(diag.has_shadow_region, bool)


# ── directive passing ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_directive_kwarg_does_not_break_execution():
    from agents.image_analysis_agent import ImageAnalysisAgent
    agent = ImageAnalysisAgent(directive="focus on edges")
    result = await agent.run(image=_gradient_image(), directive="override")
    assert result.status == "success"


# ── optimal_color_space ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_optimal_color_space_is_valid_string():
    from agents.image_analysis_agent import ImageAnalysisAgent
    valid = {"gray", "hsv_s", "lab_l", "bgr"}
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_gradient_image()))
    assert diag.optimal_color_space in valid


@pytest.mark.asyncio
async def test_color_image_optimal_color_space_not_gray():
    from agents.image_analysis_agent import ImageAnalysisAgent
    diag = _get_diagnosis(await ImageAnalysisAgent().run(image=_color_image()))
    assert diag.optimal_color_space != "gray"
