"""Tests for AlgorithmSelector — pure rule-based decision tree (Step 23)."""
import pytest

from agents.models import AlgorithmCategory, ImageDiagnosis, SceneContext


def _make_diagnosis(**overrides) -> ImageDiagnosis:
    """Build an ImageDiagnosis with neutral defaults; override specific fields as needed."""
    defaults = dict(
        contrast=0.2,
        noise_level=0.1,
        edge_density=0.1,
        lighting_uniformity=0.8,
        illumination_type="uniform",
        noise_frequency="low",
        reflection_level=0.1,
        surface_type="flat",
        depth_complexity=0.2,
        has_shadow_region=False,
        blob_feasibility=0.3,
        blob_count_estimate=5,
        color_discriminability=0.2,
        dominant_channel_ratio=0.4,
        structural_regularity=0.2,
        pattern_repetition=0.3,
        optimal_color_space="RGB",
        threshold_candidate=128.0,
        edge_sharpness=0.5,
    )
    defaults.update(overrides)
    return ImageDiagnosis(**defaults)


def _make_scene(**diag_overrides) -> SceneContext:
    return SceneContext(
        image_diagnosis=_make_diagnosis(**diag_overrides),
        depth_map=None,
        material_map=None,
    )


# ── Instantiation ──────────────────────────────────────────────────────────────

class TestInstantiation:
    def test_default_name_and_no_directive(self):
        from agents.algorithm_selector import AlgorithmSelector
        sel = AlgorithmSelector()
        assert sel.name == "algorithm_selector"
        assert sel.directive == ""

    def test_accepts_directive_kwarg(self):
        from agents.algorithm_selector import AlgorithmSelector
        sel = AlgorithmSelector(directive="prefer edge detection")
        assert sel.directive == "prefer edge detection"


# ── AgentResult structure ──────────────────────────────────────────────────────

class TestAgentResultStructure:
    @pytest.mark.asyncio
    async def test_status_is_success(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_data_has_category_key(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert "category" in result.data

    @pytest.mark.asyncio
    async def test_data_has_reason_key(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert "reason" in result.data

    @pytest.mark.asyncio
    async def test_data_has_scores_key(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert "scores" in result.data

    @pytest.mark.asyncio
    async def test_data_has_decision_path_key(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert "decision_path" in result.data

    @pytest.mark.asyncio
    async def test_execution_time_ms_is_set(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_reason_is_non_empty_string(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert isinstance(result.data["reason"], str)
        assert len(result.data["reason"]) > 0

    @pytest.mark.asyncio
    async def test_decision_path_is_non_empty_list(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert isinstance(result.data["decision_path"], list)
        assert len(result.data["decision_path"]) > 0

    @pytest.mark.asyncio
    async def test_scores_is_non_empty_dict(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert isinstance(result.data["scores"], dict)
        assert len(result.data["scores"]) > 0

    @pytest.mark.asyncio
    async def test_category_value_is_string(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=_make_scene())
        assert isinstance(result.data["category"], str)


# ── Decision tree paths ────────────────────────────────────────────────────────

class TestDecisionTreePaths:
    @pytest.mark.asyncio
    async def test_blob_path_high_contrast_and_blob_feasibility(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(contrast=0.5, blob_feasibility=0.7)
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_color_filter_path_high_color_discriminability(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(color_discriminability=0.6)
        )
        assert result.data["category"] == AlgorithmCategory.COLOR_FILTER.value

    @pytest.mark.asyncio
    async def test_edge_detection_path_high_edge_density_and_regularity(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(edge_density=0.4, structural_regularity=0.6)
        )
        assert result.data["category"] == AlgorithmCategory.EDGE_DETECTION.value

    @pytest.mark.asyncio
    async def test_template_matching_path_high_pattern_repetition(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(pattern_repetition=0.8)
        )
        assert result.data["category"] == AlgorithmCategory.TEMPLATE_MATCHING.value

    @pytest.mark.asyncio
    async def test_default_fallback_returns_blob(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(
                contrast=0.1,
                blob_feasibility=0.1,
                color_discriminability=0.1,
                edge_density=0.1,
                structural_regularity=0.1,
                pattern_repetition=0.1,
            )
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value


# ── Decision priority (first match wins) ──────────────────────────────────────

class TestDecisionPriority:
    @pytest.mark.asyncio
    async def test_blob_beats_color_filter_when_both_conditions_met(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(
                contrast=0.5,
                blob_feasibility=0.7,
                color_discriminability=0.6,
            )
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_blob_beats_edge_detection_when_both_conditions_met(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(
                contrast=0.5,
                blob_feasibility=0.7,
                edge_density=0.4,
                structural_regularity=0.6,
            )
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_color_filter_beats_edge_detection_when_both_conditions_met(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(
                color_discriminability=0.6,
                edge_density=0.4,
                structural_regularity=0.6,
            )
        )
        assert result.data["category"] == AlgorithmCategory.COLOR_FILTER.value

    @pytest.mark.asyncio
    async def test_color_filter_beats_template_matching_when_both_conditions_met(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(
                color_discriminability=0.6,
                pattern_repetition=0.8,
            )
        )
        assert result.data["category"] == AlgorithmCategory.COLOR_FILTER.value

    @pytest.mark.asyncio
    async def test_edge_detection_beats_template_matching_when_both_conditions_met(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(
                edge_density=0.4,
                structural_regularity=0.6,
                pattern_repetition=0.8,
            )
        )
        assert result.data["category"] == AlgorithmCategory.EDGE_DETECTION.value


# ── Boundary values (strict > not >=) ─────────────────────────────────────────

class TestBoundaryValues:
    @pytest.mark.asyncio
    async def test_contrast_exactly_at_threshold_does_not_trigger_blob(self):
        """contrast=0.4 is NOT > 0.4; BLOB explicit condition not triggered."""
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(contrast=0.4, blob_feasibility=0.7)
        )
        # All other metrics are neutral defaults; falls through to default BLOB
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_blob_feasibility_exactly_at_threshold_does_not_trigger_blob(self):
        """blob_feasibility=0.6 is NOT > 0.6."""
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(contrast=0.5, blob_feasibility=0.6)
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_color_discriminability_exactly_at_threshold_does_not_trigger_color(self):
        """color_discriminability=0.5 is NOT > 0.5."""
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(color_discriminability=0.5)
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_pattern_repetition_exactly_at_threshold_does_not_trigger_template(self):
        """pattern_repetition=0.7 is NOT > 0.7."""
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(pattern_repetition=0.7)
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_blob_just_above_both_thresholds_triggers_blob(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(contrast=0.41, blob_feasibility=0.61)
        )
        assert result.data["category"] == AlgorithmCategory.BLOB.value

    @pytest.mark.asyncio
    async def test_color_just_above_threshold_triggers_color_filter(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(color_discriminability=0.51)
        )
        assert result.data["category"] == AlgorithmCategory.COLOR_FILTER.value

    @pytest.mark.asyncio
    async def test_pattern_just_above_threshold_triggers_template_matching(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(
            scene_context=_make_scene(pattern_repetition=0.71)
        )
        assert result.data["category"] == AlgorithmCategory.TEMPLATE_MATCHING.value


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_none_scene_context_returns_error_status(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=None)
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_none_scene_context_error_message(self):
        from agents.algorithm_selector import AlgorithmSelector
        result = await AlgorithmSelector().run(scene_context=None)
        assert "SceneContext is required" in result.error_message

    @pytest.mark.asyncio
    async def test_none_image_diagnosis_returns_error_status(self):
        from agents.algorithm_selector import AlgorithmSelector
        scene = SceneContext(image_diagnosis=None, depth_map=None, material_map=None)
        result = await AlgorithmSelector().run(scene_context=scene)
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_none_image_diagnosis_error_message(self):
        from agents.algorithm_selector import AlgorithmSelector
        scene = SceneContext(image_diagnosis=None, depth_map=None, material_map=None)
        result = await AlgorithmSelector().run(scene_context=scene)
        assert "ImageDiagnosis is required" in result.error_message


# ── Directive handling ─────────────────────────────────────────────────────────

class TestDirectiveHandling:
    @pytest.mark.asyncio
    async def test_directive_does_not_change_blob_decision(self):
        from agents.algorithm_selector import AlgorithmSelector
        ctx = _make_scene(contrast=0.5, blob_feasibility=0.7)
        result_plain = await AlgorithmSelector().run(scene_context=ctx)
        result_directed = await AlgorithmSelector(
            directive="always use edge detection"
        ).run(scene_context=ctx)
        assert result_plain.data["category"] == result_directed.data["category"]

    @pytest.mark.asyncio
    async def test_directive_does_not_change_color_filter_decision(self):
        from agents.algorithm_selector import AlgorithmSelector
        ctx = _make_scene(color_discriminability=0.6)
        result_plain = await AlgorithmSelector().run(scene_context=ctx)
        result_directed = await AlgorithmSelector(
            directive="use blob detection"
        ).run(scene_context=ctx)
        assert result_plain.data["category"] == result_directed.data["category"]
