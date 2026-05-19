"""Tests for agents/pipeline_composer.py — PipelineComposer rule-based pipeline generation."""
import pytest

from agents.base_agent import BaseAgent
from agents.models import (
    AgentResult,
    ImageDiagnosis,
    PipelineBlock,
    ProcessingPipeline,
    SceneContext,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_diagnosis(**overrides) -> ImageDiagnosis:
    defaults = dict(
        contrast=0.5,
        noise_level=12.0,
        edge_density=0.15,
        lighting_uniformity=0.1,
        illumination_type="uniform",
        noise_frequency="low_freq",
        reflection_level=0.05,
        surface_type="",
        depth_complexity=0.0,
        has_shadow_region=False,
        blob_feasibility=0.6,
        blob_count_estimate=5,
        color_discriminability=0.35,
        dominant_channel_ratio=0.4,
        structural_regularity=0.6,
        pattern_repetition=0.1,
        optimal_color_space="bgr",
        threshold_candidate=128.0,
        edge_sharpness=0.15,
    )
    defaults.update(overrides)
    return ImageDiagnosis(**defaults)


def _make_scene_context(**diag_overrides) -> SceneContext:
    return SceneContext(
        image_diagnosis=_make_diagnosis(**diag_overrides),
        depth_map=None,
        material_map=None,
        roi=None,
        spec={},
    )


CATEGORY_ORDER = {"color_space": 0, "denoise": 1, "threshold": 2, "morphology": 3, "edge": 4}


# ── class instantiation ────────────────────────────────────────────────────────

class TestInstantiation:
    def test_pipeline_composer_is_base_agent(self):
        from agents.pipeline_composer import PipelineComposer
        agent = PipelineComposer()
        assert isinstance(agent, BaseAgent)

    def test_default_directive_is_empty_string(self):
        from agents.pipeline_composer import PipelineComposer
        agent = PipelineComposer()
        assert agent.directive == ""

    def test_custom_directive_is_stored(self):
        from agents.pipeline_composer import PipelineComposer
        agent = PipelineComposer(directive="CLAHE 우선")
        assert agent.directive == "CLAHE 우선"

    def test_agent_has_name(self):
        from agents.pipeline_composer import PipelineComposer
        agent = PipelineComposer()
        assert isinstance(agent.name, str) and len(agent.name) > 0

    def test_agent_has_run_method(self):
        from agents.pipeline_composer import PipelineComposer
        agent = PipelineComposer()
        assert callable(agent.run)


# ── AgentResult structure ──────────────────────────────────────────────────────

class TestAgentResultStructure:
    @pytest.mark.asyncio
    async def test_run_returns_agent_result(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_run_returns_success_status(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_run_data_has_pipelines_key(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert "pipelines" in result.data

    @pytest.mark.asyncio
    async def test_run_data_has_num_candidates_key(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert "num_candidates" in result.data

    @pytest.mark.asyncio
    async def test_run_data_has_matching_blocks_summary_key(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert "matching_blocks_summary" in result.data

    @pytest.mark.asyncio
    async def test_run_no_error_message_on_success(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_run_num_candidates_matches_pipelines_count(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert result.data["num_candidates"] == len(result.data["pipelines"])

    @pytest.mark.asyncio
    async def test_matching_blocks_summary_is_dict(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert isinstance(result.data["matching_blocks_summary"], dict)


# ── pipeline count ─────────────────────────────────────────────────────────────

class TestPipelineCount:
    @pytest.mark.asyncio
    async def test_pipeline_count_at_least_3(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert len(result.data["pipelines"]) >= 3

    @pytest.mark.asyncio
    async def test_pipeline_count_at_most_5(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        assert len(result.data["pipelines"]) <= 5

    @pytest.mark.asyncio
    async def test_minimal_diagnosis_still_generates_3_pipelines(self):
        from agents.pipeline_composer import PipelineComposer
        # Only grayscale + dynamic_threshold match with all-zero diagnosis
        sc = _make_scene_context(
            contrast=0.0,
            noise_level=0.0,
            edge_density=0.0,
            lighting_uniformity=0.0,
            color_discriminability=0.0,
            edge_sharpness=0.0,
        )
        result = await PipelineComposer().run(scene_context=sc)
        assert result.status == "success"
        assert len(result.data["pipelines"]) >= 3

    @pytest.mark.asyncio
    async def test_extreme_diagnosis_at_most_5_pipelines(self):
        from agents.pipeline_composer import PipelineComposer
        # Everything triggers — should still cap at 5
        sc = _make_scene_context(
            contrast=0.9,
            noise_level=40.0,
            edge_density=0.9,
            lighting_uniformity=0.9,
            color_discriminability=0.9,
            dominant_channel_ratio=0.3,
            edge_sharpness=0.9,
        )
        result = await PipelineComposer().run(scene_context=sc)
        assert len(result.data["pipelines"]) <= 5


# ── pipeline structure ─────────────────────────────────────────────────────────

class TestPipelineStructure:
    @pytest.mark.asyncio
    async def test_each_pipeline_is_processing_pipeline_instance(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            assert isinstance(pipeline, ProcessingPipeline)

    @pytest.mark.asyncio
    async def test_each_pipeline_has_nonempty_pipeline_id(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            assert isinstance(pipeline.pipeline_id, str)
            assert len(pipeline.pipeline_id) > 0

    @pytest.mark.asyncio
    async def test_each_pipeline_has_blocks(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            assert isinstance(pipeline.blocks, list)
            assert len(pipeline.blocks) > 0

    @pytest.mark.asyncio
    async def test_each_pipeline_has_description_string(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            assert isinstance(pipeline.description, str)

    @pytest.mark.asyncio
    async def test_pipeline_ids_are_unique(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        ids = [p.pipeline_id for p in result.data["pipelines"]]
        assert len(ids) == len(set(ids))


# ── block structure ────────────────────────────────────────────────────────────

class TestBlockStructure:
    @pytest.mark.asyncio
    async def test_each_block_is_pipeline_block_instance(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            for block in pipeline.blocks:
                assert isinstance(block, PipelineBlock)

    @pytest.mark.asyncio
    async def test_each_block_has_nonempty_block_id(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            for block in pipeline.blocks:
                assert isinstance(block.block_id, str)
                assert len(block.block_id) > 0

    @pytest.mark.asyncio
    async def test_each_block_has_valid_block_type(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        valid_types = {"color_space", "denoise", "threshold", "morphology", "edge"}
        for pipeline in result.data["pipelines"]:
            for block in pipeline.blocks:
                assert block.block_type in valid_types, f"Invalid block_type: {block.block_type}"

    @pytest.mark.asyncio
    async def test_each_block_params_is_dict(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            for block in pipeline.blocks:
                assert isinstance(block.params, dict)

    @pytest.mark.asyncio
    async def test_block_params_match_block_definition_params(self):
        from agents.pipeline_composer import PipelineComposer
        from agents.pipeline_blocks import get_block
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            for block in pipeline.blocks:
                definition = get_block(block.block_id)
                if definition is not None:
                    assert block.params == definition.params


# ── block ordering ─────────────────────────────────────────────────────────────

class TestBlockOrdering:
    @pytest.mark.asyncio
    async def test_first_block_of_each_pipeline_is_color_space(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            assert pipeline.blocks[0].block_type == "color_space"

    @pytest.mark.asyncio
    async def test_blocks_follow_category_order(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            orders = [CATEGORY_ORDER[b.block_type] for b in pipeline.blocks]
            assert orders == sorted(orders), (
                f"Pipeline '{pipeline.pipeline_id}' blocks not in order: "
                f"{[b.block_id for b in pipeline.blocks]}"
            )

    @pytest.mark.asyncio
    async def test_each_pipeline_has_exactly_one_color_space_block(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            cs_blocks = [b for b in pipeline.blocks if b.block_type == "color_space"]
            assert len(cs_blocks) == 1, (
                f"Pipeline '{pipeline.pipeline_id}' has {len(cs_blocks)} color_space blocks"
            )

    @pytest.mark.asyncio
    async def test_each_pipeline_has_exactly_one_threshold_block(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            thresh_blocks = [b for b in pipeline.blocks if b.block_type == "threshold"]
            assert len(thresh_blocks) == 1, (
                f"Pipeline '{pipeline.pipeline_id}' has {len(thresh_blocks)} threshold blocks"
            )

    @pytest.mark.asyncio
    async def test_threshold_comes_after_denoise_when_present(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            types = [b.block_type for b in pipeline.blocks]
            if "denoise" in types and "threshold" in types:
                assert types.index("denoise") < types.index("threshold")

    @pytest.mark.asyncio
    async def test_morphology_comes_after_threshold_when_present(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            types = [b.block_type for b in pipeline.blocks]
            if "morphology" in types and "threshold" in types:
                assert types.index("threshold") < types.index("morphology")

    @pytest.mark.asyncio
    async def test_edge_comes_last_when_present(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        for pipeline in result.data["pipelines"]:
            types = [b.block_type for b in pipeline.blocks]
            if "edge" in types:
                assert types.index("edge") == max(
                    CATEGORY_ORDER[t] for t in types
                ) or types[-1] == "edge"


# ── CLAHE for uneven lighting ──────────────────────────────────────────────────

class TestClaheLighting:
    @pytest.mark.asyncio
    async def test_at_least_one_pipeline_includes_clahe_for_uneven_lighting(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context(lighting_uniformity=0.3)
        result = await PipelineComposer().run(scene_context=sc)
        all_block_ids = [
            b.block_id
            for p in result.data["pipelines"]
            for b in p.blocks
        ]
        assert "clahe" in all_block_ids, "Expected 'clahe' in at least one pipeline for uneven lighting"

    @pytest.mark.asyncio
    async def test_uniform_lighting_does_not_force_clahe(self):
        from agents.pipeline_composer import PipelineComposer
        # lighting_uniformity=0.1 < 0.25, CLAHE condition is False
        sc = _make_scene_context(lighting_uniformity=0.1)
        result = await PipelineComposer().run(scene_context=sc)
        # Should still succeed (CLAHE not mandatory)
        assert result.status == "success"


# ── directive handling ─────────────────────────────────────────────────────────

class TestDirectiveHandling:
    @pytest.mark.asyncio
    async def test_clahe_directive_includes_clahe_in_all_pipelines(self):
        from agents.pipeline_composer import PipelineComposer
        # Even with low lighting_uniformity, directive forces CLAHE
        sc = _make_scene_context(lighting_uniformity=0.1)
        result = await PipelineComposer(directive="CLAHE 우선").run(scene_context=sc)
        assert result.status == "success"
        for pipeline in result.data["pipelines"]:
            block_ids = [b.block_id for b in pipeline.blocks]
            assert "clahe" in block_ids, (
                f"Directive 'CLAHE 우선' should force CLAHE in pipeline '{pipeline.pipeline_id}'"
            )

    @pytest.mark.asyncio
    async def test_directive_does_not_break_block_ordering(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context()
        result = await PipelineComposer(directive="CLAHE 우선").run(scene_context=sc)
        for pipeline in result.data["pipelines"]:
            orders = [CATEGORY_ORDER[b.block_type] for b in pipeline.blocks]
            assert orders == sorted(orders)

    @pytest.mark.asyncio
    async def test_directive_does_not_break_color_space_first_rule(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context()
        result = await PipelineComposer(directive="CLAHE 우선").run(scene_context=sc)
        for pipeline in result.data["pipelines"]:
            assert pipeline.blocks[0].block_type == "color_space"

    @pytest.mark.asyncio
    async def test_empty_directive_behaves_same_as_no_directive(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context()
        result_no_directive = await PipelineComposer().run(scene_context=sc)
        result_empty_directive = await PipelineComposer(directive="").run(scene_context=sc)
        assert result_no_directive.status == result_empty_directive.status
        assert len(result_no_directive.data["pipelines"]) == len(result_empty_directive.data["pipelines"])


# ── pipeline diversity ─────────────────────────────────────────────────────────

class TestPipelineDiversity:
    @pytest.mark.asyncio
    async def test_no_two_pipelines_have_identical_block_id_lists(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        block_id_tuples = [
            tuple(b.block_id for b in pipeline.blocks)
            for pipeline in result.data["pipelines"]
        ]
        assert len(block_id_tuples) == len(set(block_id_tuples)), (
            "Duplicate pipelines found: " + str(block_id_tuples)
        )

    @pytest.mark.asyncio
    async def test_pipelines_use_different_color_spaces_when_possible(self):
        from agents.pipeline_composer import PipelineComposer
        # color_discriminability=0.5 makes hsv_s, hsv_v available
        sc = _make_scene_context(color_discriminability=0.5, dominant_channel_ratio=0.3)
        result = await PipelineComposer().run(scene_context=sc)
        first_blocks = [p.blocks[0].block_id for p in result.data["pipelines"]]
        # At least 2 different color spaces across pipelines
        assert len(set(first_blocks)) >= 2

    @pytest.mark.asyncio
    async def test_minimal_diagnosis_pipelines_still_diverse(self):
        from agents.pipeline_composer import PipelineComposer
        # Only grayscale + dynamic_threshold available — still no exact duplicates
        sc = _make_scene_context(
            contrast=0.0,
            noise_level=0.0,
            edge_density=0.0,
            lighting_uniformity=0.0,
            color_discriminability=0.0,
            edge_sharpness=0.0,
        )
        result = await PipelineComposer().run(scene_context=sc)
        block_id_tuples = [
            tuple(b.block_id for b in p.blocks)
            for p in result.data["pipelines"]
        ]
        assert len(block_id_tuples) == len(set(block_id_tuples))


# ── error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_none_scene_context_returns_error(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=None)
        assert result.status == "error"
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_none_scene_context_error_message_is_string(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=None)
        assert isinstance(result.error_message, str)
        assert len(result.error_message) > 0

    @pytest.mark.asyncio
    async def test_scene_context_missing_image_diagnosis_returns_error(self):
        from agents.pipeline_composer import PipelineComposer
        sc = SceneContext(
            image_diagnosis=None,
            depth_map=None,
            material_map=None,
        )
        result = await PipelineComposer().run(scene_context=sc)
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_error_result_data_is_dict(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=None)
        assert isinstance(result.data, dict)


# ── matching_blocks_summary content ───────────────────────────────────────────

class TestMatchingBlocksSummary:
    @pytest.mark.asyncio
    async def test_summary_contains_category_counts(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        summary = result.data["matching_blocks_summary"]
        # Should contain at least the categories
        assert any(k in summary for k in ["color_space", "denoise", "threshold", "morphology", "edge"])

    @pytest.mark.asyncio
    async def test_summary_color_space_count_positive(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        summary = result.data["matching_blocks_summary"]
        assert summary.get("color_space", 0) >= 1

    @pytest.mark.asyncio
    async def test_summary_threshold_count_positive(self):
        from agents.pipeline_composer import PipelineComposer
        result = await PipelineComposer().run(scene_context=_make_scene_context())
        summary = result.data["matching_blocks_summary"]
        assert summary.get("threshold", 0) >= 1


# ── edge case: high noise diagnosis ───────────────────────────────────────────

class TestHighNoiseDiagnosis:
    @pytest.mark.asyncio
    async def test_high_noise_generates_denoise_blocks(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context(noise_level=25.0, edge_sharpness=0.2)
        result = await PipelineComposer().run(scene_context=sc)
        all_types = [
            b.block_type
            for p in result.data["pipelines"]
            for b in p.blocks
        ]
        assert "denoise" in all_types

    @pytest.mark.asyncio
    async def test_high_noise_status_is_success(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context(noise_level=35.0)
        result = await PipelineComposer().run(scene_context=sc)
        assert result.status == "success"


# ── edge case: uneven lighting full diagnosis ──────────────────────────────────

class TestUnevenLightingDiagnosis:
    @pytest.mark.asyncio
    async def test_adaptive_threshold_used_for_uneven_lighting(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context(lighting_uniformity=0.3, noise_level=15.0)
        result = await PipelineComposer().run(scene_context=sc)
        all_block_ids = [
            b.block_id
            for p in result.data["pipelines"]
            for b in p.blocks
        ]
        adaptive_blocks = {"adaptive_mean", "adaptive_gauss"}
        assert adaptive_blocks & set(all_block_ids), "Expected at least one adaptive threshold block"

    @pytest.mark.asyncio
    async def test_pipeline_count_still_valid_for_uneven_lighting(self):
        from agents.pipeline_composer import PipelineComposer
        sc = _make_scene_context(lighting_uniformity=0.4)
        result = await PipelineComposer().run(scene_context=sc)
        assert 3 <= len(result.data["pipelines"]) <= 5
