"""build_scene_context — merges results from 4 vision agents into SceneContext."""
from typing import Any, Optional

from agents.models import AgentResult, ImageDiagnosis, SceneContext


def _default_diagnosis() -> ImageDiagnosis:
    return ImageDiagnosis(
        contrast=0.0,
        noise_level=0.0,
        edge_density=0.0,
        lighting_uniformity=0.0,
        illumination_type="",
        noise_frequency="",
        reflection_level=0.0,
        surface_type="",
        depth_complexity=0.0,
        has_shadow_region=False,
        blob_feasibility=0.0,
        blob_count_estimate=0,
        color_discriminability=0.0,
        dominant_channel_ratio=0.0,
        structural_regularity=0.0,
        pattern_repetition=0.0,
        optimal_color_space="",
        threshold_candidate=0.0,
        edge_sharpness=0.0,
    )


def _extract_diagnosis(result: AgentResult) -> ImageDiagnosis:
    if result.status != "success":
        return _default_diagnosis()
    return result.data.get("diagnosis") or _default_diagnosis()


def _merge_depth(diagnosis: ImageDiagnosis, result: AgentResult) -> Optional[Any]:
    if result.status != "success":
        return None
    depth_stats = result.data.get("depth_stats")
    if depth_stats:
        diagnosis.depth_complexity = depth_stats.get("depth_complexity", 0.0)
        diagnosis.has_shadow_region = depth_stats.get("has_shadow_region", False)
    return result.data.get("depth_map")


def _merge_material(diagnosis: ImageDiagnosis, result: AgentResult) -> Optional[dict]:
    if result.status != "success":
        return None
    surface_type = result.data.get("surface_type")
    if surface_type is not None:
        diagnosis.surface_type = surface_type
    return result.data.get("material_map")


def _extract_roi(result: AgentResult) -> Optional[dict]:
    if result.status != "success":
        return None
    mode = result.data.get("mode")
    if mode == "manual":
        return result.data.get("roi")
    if mode == "auto":
        return result.data.get("recommended_roi")
    return None


def build_scene_context(
    image_analysis_result: AgentResult,
    depth_result: AgentResult,
    material_result: AgentResult,
    roi_result: AgentResult,
) -> SceneContext:
    diagnosis = _extract_diagnosis(image_analysis_result)
    depth_map = _merge_depth(diagnosis, depth_result)
    material_map = _merge_material(diagnosis, material_result)
    roi = _extract_roi(roi_result)
    return SceneContext(
        image_diagnosis=diagnosis,
        depth_map=depth_map,
        material_map=material_map,
        roi=roi,
    )
