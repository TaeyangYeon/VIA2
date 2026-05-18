"""Tests for agents/scene_context.py — build_scene_context() function."""
import numpy as np
import pytest

from agents.models import AgentResult, ImageDiagnosis, SceneContext
from agents.scene_context import build_scene_context


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_diagnosis(**overrides) -> ImageDiagnosis:
    defaults = dict(
        contrast=0.5,
        noise_level=10.0,
        edge_density=0.2,
        lighting_uniformity=0.1,
        illumination_type="uniform",
        noise_frequency="low_freq",
        reflection_level=0.05,
        surface_type="",
        depth_complexity=0.0,
        has_shadow_region=False,
        blob_feasibility=0.7,
        blob_count_estimate=5,
        color_discriminability=0.3,
        dominant_channel_ratio=0.4,
        structural_regularity=0.6,
        pattern_repetition=0.1,
        optimal_color_space="bgr",
        threshold_candidate=128.0,
        edge_sharpness=15.0,
    )
    defaults.update(overrides)
    return ImageDiagnosis(**defaults)


def _ia_ok(diagnosis=None) -> AgentResult:
    return AgentResult(
        status="success",
        data={"diagnosis": diagnosis or _make_diagnosis()},
    )


def _ia_err() -> AgentResult:
    return AgentResult(status="error", data={}, error_message="image analysis failed")


def _depth_ok(depth_complexity=0.4, has_shadow_region=True) -> AgentResult:
    depth_map = np.zeros((10, 10), dtype=np.float32)
    return AgentResult(
        status="success",
        data={
            "depth_map": depth_map,
            "depth_stats": {
                "depth_complexity": depth_complexity,
                "has_shadow_region": has_shadow_region,
                "depth_range": 0.8,
                "depth_mean": 0.5,
                "depth_gradient_max": 0.6,
            },
        },
    )


def _depth_err() -> AgentResult:
    return AgentResult(status="error", data={}, error_message="depth failed")


def _mat_ok(surface_type="metal") -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "surface_type": surface_type,
            "material_map": {"metal": {"type": "metal", "confidence": 0.9, "bbox": []}},
            "confidence": 0.9,
            "regions": [],
            "feature_stats": {"feature_dim": 768, "feature_norm": 1.0, "top_similarities": {}},
        },
    )


def _mat_err() -> AgentResult:
    return AgentResult(status="error", data={}, error_message="material failed")


def _roi_manual(roi=None) -> AgentResult:
    r = roi or {"x1": 10, "y1": 10, "x2": 100, "y2": 100}
    return AgentResult(
        status="success",
        data={
            "mode": "manual",
            "roi": r,
            "roi_stats": {"area_ratio": 0.5, "aspect_ratio": 1.0},
        },
    )


def _roi_auto(recommended_roi=None) -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "mode": "auto",
            "query": "inspect target",
            "detections": [],
            "recommended_roi": recommended_roi,
            "masks": [],
            "confidence": 0.8,
        },
    )


def _roi_err() -> AgentResult:
    return AgentResult(status="error", data={}, error_message="roi failed")


# ── basic ──────────────────────────────────────────────────────────────────────

class TestBasic:
    def test_returns_scene_context(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual())
        assert isinstance(result, SceneContext)

    def test_image_diagnosis_fields_preserved(self):
        diag = _make_diagnosis(contrast=0.75, edge_density=0.33)
        result = build_scene_context(_ia_ok(diag), _depth_ok(), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.contrast == pytest.approx(0.75)
        assert result.image_diagnosis.edge_density == pytest.approx(0.33)

    def test_depth_map_is_ndarray(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual())
        assert isinstance(result.depth_map, np.ndarray)

    def test_material_map_is_dict(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual())
        assert isinstance(result.material_map, dict)

    def test_roi_populated_from_manual(self):
        roi = {"x1": 10, "y1": 10, "x2": 100, "y2": 100}
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual(roi))
        assert result.roi == roi


# ── depth merging ──────────────────────────────────────────────────────────────

class TestDepthMerging:
    def test_depth_complexity_overrides_default(self):
        result = build_scene_context(_ia_ok(), _depth_ok(depth_complexity=0.77), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.77)

    def test_has_shadow_region_true_overrides_false_default(self):
        result = build_scene_context(_ia_ok(), _depth_ok(has_shadow_region=True), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.has_shadow_region is True

    def test_has_shadow_region_false_stays_false(self):
        result = build_scene_context(_ia_ok(), _depth_ok(has_shadow_region=False), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.has_shadow_region is False

    def test_depth_complexity_zero_stays_zero(self):
        result = build_scene_context(_ia_ok(), _depth_ok(depth_complexity=0.0), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.0)


# ── material merging ──────────────────────────────────────────────────────────

class TestMaterialMerging:
    def test_surface_type_overrides_empty_default(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(surface_type="plastic"), _roi_manual())
        assert result.image_diagnosis.surface_type == "plastic"

    def test_surface_type_metal(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(surface_type="metal"), _roi_manual())
        assert result.image_diagnosis.surface_type == "metal"


# ── ROI normalization ─────────────────────────────────────────────────────────

class TestROINormalization:
    def test_manual_roi_used_directly(self):
        roi = {"x1": 5, "y1": 10, "x2": 50, "y2": 80}
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual(roi))
        assert result.roi == roi

    def test_auto_recommended_roi_used(self):
        recommended = {"x1": 20, "y1": 30, "x2": 200, "y2": 300}
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_auto(recommended))
        assert result.roi == recommended

    def test_auto_no_recommended_roi_gives_none(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_auto(recommended_roi=None))
        assert result.roi is None

    def test_roi_error_gives_none(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_err())
        assert result.roi is None


# ── partial failure ────────────────────────────────────────────────────────────

class TestPartialFailure:
    def test_depth_error_keeps_diagnosis_defaults(self):
        result = build_scene_context(_ia_ok(), _depth_err(), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.0)
        assert result.image_diagnosis.has_shadow_region is False

    def test_depth_error_depth_map_is_none(self):
        result = build_scene_context(_ia_ok(), _depth_err(), _mat_ok(), _roi_manual())
        assert result.depth_map is None

    def test_material_error_keeps_surface_type_default(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_err(), _roi_manual())
        assert result.image_diagnosis.surface_type == ""

    def test_material_error_material_map_is_none(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_err(), _roi_manual())
        assert result.material_map is None

    def test_roi_error_roi_is_none(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_err())
        assert result.roi is None

    def test_image_analysis_error_still_builds(self):
        result = build_scene_context(_ia_err(), _depth_ok(), _mat_ok(), _roi_manual())
        assert isinstance(result, SceneContext)
        assert result.image_diagnosis is not None

    def test_image_analysis_error_depth_still_merged(self):
        result = build_scene_context(_ia_err(), _depth_ok(depth_complexity=0.55), _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.55)

    def test_image_analysis_error_material_still_merged(self):
        result = build_scene_context(_ia_err(), _depth_ok(), _mat_ok(surface_type="rubber"), _roi_manual())
        assert result.image_diagnosis.surface_type == "rubber"


# ── all agents failed ─────────────────────────────────────────────────────────

class TestAllFailed:
    def test_builds_scene_context(self):
        result = build_scene_context(_ia_err(), _depth_err(), _mat_err(), _roi_err())
        assert isinstance(result, SceneContext)

    def test_depth_map_is_none(self):
        result = build_scene_context(_ia_err(), _depth_err(), _mat_err(), _roi_err())
        assert result.depth_map is None

    def test_material_map_is_none(self):
        result = build_scene_context(_ia_err(), _depth_err(), _mat_err(), _roi_err())
        assert result.material_map is None

    def test_roi_is_none(self):
        result = build_scene_context(_ia_err(), _depth_err(), _mat_err(), _roi_err())
        assert result.roi is None

    def test_diagnosis_has_depth_defaults(self):
        result = build_scene_context(_ia_err(), _depth_err(), _mat_err(), _roi_err())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.0)
        assert result.image_diagnosis.has_shadow_region is False

    def test_diagnosis_has_surface_type_default(self):
        result = build_scene_context(_ia_err(), _depth_err(), _mat_err(), _roi_err())
        assert result.image_diagnosis.surface_type == ""


# ── validation ─────────────────────────────────────────────────────────────────

class TestValidation:
    def test_all_scene_context_attributes_present(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual())
        assert result.image_diagnosis is not None
        assert hasattr(result, "depth_map")
        assert hasattr(result, "material_map")
        assert hasattr(result, "roi")
        assert hasattr(result, "spec")

    def test_spec_defaults_to_empty_dict(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual())
        assert result.spec == {}

    def test_image_diagnosis_is_image_diagnosis_instance(self):
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), _roi_manual())
        assert isinstance(result.image_diagnosis, ImageDiagnosis)


# ── edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_data_depth_result_keeps_defaults(self):
        empty_depth = AgentResult(status="success", data={})
        result = build_scene_context(_ia_ok(), empty_depth, _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.0)
        assert result.depth_map is None

    def test_depth_result_missing_depth_stats_key(self):
        no_stats = AgentResult(
            status="success",
            data={"depth_map": np.zeros((5, 5), dtype=np.float32)},
        )
        result = build_scene_context(_ia_ok(), no_stats, _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.0)

    def test_empty_data_material_result_keeps_defaults(self):
        empty_mat = AgentResult(status="success", data={})
        result = build_scene_context(_ia_ok(), _depth_ok(), empty_mat, _roi_manual())
        assert result.image_diagnosis.surface_type == ""
        assert result.material_map is None

    def test_empty_data_roi_result_gives_none(self):
        empty_roi = AgentResult(status="success", data={})
        result = build_scene_context(_ia_ok(), _depth_ok(), _mat_ok(), empty_roi)
        assert result.roi is None

    def test_missing_diagnosis_key_in_image_analysis_data(self):
        no_diag = AgentResult(status="success", data={})
        result = build_scene_context(no_diag, _depth_ok(), _mat_ok(), _roi_manual())
        assert isinstance(result, SceneContext)
        assert result.image_diagnosis is not None

    def test_depth_stats_partial_keys_use_defaults(self):
        partial_stats = AgentResult(
            status="success",
            data={"depth_stats": {"depth_complexity": 0.6}},
        )
        result = build_scene_context(_ia_ok(), partial_stats, _mat_ok(), _roi_manual())
        assert result.image_diagnosis.depth_complexity == pytest.approx(0.6)
        assert result.image_diagnosis.has_shadow_region is False
