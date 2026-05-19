"""Tests for ProcessingQualityEvaluator and ParameterSearcher (Step 22)."""
import numpy as np
import pytest
from dataclasses import asdict

from agents.models import AgentResult, PipelineBlock, ProcessingPipeline
from agents.base_agent import BaseAgent


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def gray_image():
    rng = np.random.default_rng(42)
    return rng.integers(50, 200, size=(100, 100), dtype=np.uint8)


@pytest.fixture
def bgr_image():
    rng = np.random.default_rng(42)
    return rng.integers(50, 200, size=(100, 100, 3), dtype=np.uint8)


@pytest.fixture
def black_image():
    return np.zeros((100, 100), dtype=np.uint8)


@pytest.fixture
def white_image():
    return np.full((100, 100), 255, dtype=np.uint8)


@pytest.fixture
def tiny_image():
    return np.zeros((2, 2), dtype=np.uint8)


def _single_block_pipeline(block_id: str, block_type: str, params: dict = None) -> ProcessingPipeline:
    return ProcessingPipeline(
        pipeline_id="test_pipe_01",
        blocks=[PipelineBlock(block_id=block_id, block_type=block_type, params=params or {})],
    )


def _multi_block_pipeline() -> ProcessingPipeline:
    return ProcessingPipeline(
        pipeline_id="test_pipe_02",
        blocks=[
            PipelineBlock(block_id="grayscale", block_type="color_space", params={}),
            PipelineBlock(
                block_id="gaussian_fine",
                block_type="denoise",
                params={"kernel_size": [3, 5], "sigma": [0.5, 1.0]},
            ),
        ],
    )


def _large_search_pipeline() -> ProcessingPipeline:
    """gaussian_mid (3*3=9) × bilateral (3*3*3=27) = 243 combos."""
    return ProcessingPipeline(
        pipeline_id="large_search",
        blocks=[
            PipelineBlock(
                block_id="gaussian_mid",
                block_type="denoise",
                params={"kernel_size": [5, 7, 9], "sigma": [1.0, 1.5, 2.0]},
            ),
            PipelineBlock(
                block_id="bilateral",
                block_type="denoise",
                params={"d": [5, 7, 9], "sigma_color": [50, 75, 100], "sigma_space": [50, 75, 100]},
            ),
        ],
    )


# ── ProcessingQualityEvaluator: Instantiation ──────────────────────────────────

class TestEvaluatorInstantiation:
    def test_can_be_instantiated(self):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        assert ProcessingQualityEvaluator() is not None

    def test_has_evaluate_method(self):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        assert callable(ProcessingQualityEvaluator().evaluate)


# ── QualityScore: Structure ────────────────────────────────────────────────────

class TestQualityScoreStructure:
    def test_evaluate_returns_quality_score(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator, QualityScore
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert isinstance(score, QualityScore)

    def test_has_contrast_score_field(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert hasattr(score, "contrast_score")

    def test_has_noise_score_field(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert hasattr(score, "noise_score")

    def test_has_edge_score_field(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert hasattr(score, "edge_score")

    def test_has_overall_score_field(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert hasattr(score, "overall_score")

    def test_details_is_dict(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert isinstance(score.details, dict)

    def test_is_dataclass_convertible(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        d = asdict(score)
        for field in ("contrast_score", "noise_score", "edge_score", "overall_score", "details"):
            assert field in d


# ── QualityScore: Range Validation ────────────────────────────────────────────

class TestQualityScoreRange:
    def test_contrast_score_in_0_1(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert 0.0 <= score.contrast_score <= 1.0

    def test_noise_score_in_0_1(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert 0.0 <= score.noise_score <= 1.0

    def test_edge_score_in_0_1(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert 0.0 <= score.edge_score <= 1.0

    def test_overall_score_in_0_1(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert 0.0 <= score.overall_score <= 1.0

    def test_bgr_image_all_scores_in_range(self, bgr_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(bgr_image, bgr_image)
        assert 0.0 <= score.contrast_score <= 1.0
        assert 0.0 <= score.noise_score <= 1.0
        assert 0.0 <= score.edge_score <= 1.0
        assert 0.0 <= score.overall_score <= 1.0


# ── QualityScore: Degenerate Detection ────────────────────────────────────────

class TestDegenerateDetection:
    def test_all_black_processed_overall_zero(self, gray_image, black_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, black_image)
        assert score.overall_score == 0.0

    def test_all_white_processed_overall_zero(self, gray_image, white_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, white_image)
        assert score.overall_score == 0.0

    def test_both_black_overall_zero(self, black_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(black_image, black_image)
        assert score.overall_score == 0.0


# ── QualityScore: Scoring Logic ────────────────────────────────────────────────

class TestScoringLogic:
    def test_higher_contrast_processed_scores_at_least_equal(self):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        rng = np.random.default_rng(0)
        original = rng.integers(100, 150, size=(100, 100), dtype=np.uint8)
        stretched = np.clip(original.astype(np.int32) * 2 - 100, 0, 255).astype(np.uint8)
        ev = ProcessingQualityEvaluator()
        score_same = ev.evaluate(original, original)
        score_stretched = ev.evaluate(original, stretched)
        assert score_stretched.contrast_score >= score_same.contrast_score

    def test_overall_is_weighted_combination(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        expected = 0.3 * score.contrast_score + 0.3 * score.noise_score + 0.4 * score.edge_score
        assert abs(score.overall_score - expected) < 1e-6

    def test_identical_images_overall_positive(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert score.overall_score > 0.0

    def test_purpose_param_accepted(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image, purpose="defect")
        from agents.processing_quality_evaluator import QualityScore
        assert isinstance(score, QualityScore)

    def test_details_non_empty(self, gray_image):
        from agents.processing_quality_evaluator import ProcessingQualityEvaluator
        score = ProcessingQualityEvaluator().evaluate(gray_image, gray_image)
        assert len(score.details) > 0


# ── ParameterSearcher: Instantiation ──────────────────────────────────────────

class TestSearcherInstantiation:
    def test_can_be_instantiated(self):
        from agents.parameter_searcher import ParameterSearcher
        assert ParameterSearcher() is not None

    def test_is_base_agent(self):
        from agents.parameter_searcher import ParameterSearcher
        assert isinstance(ParameterSearcher(), BaseAgent)

    def test_accepts_directive(self):
        from agents.parameter_searcher import ParameterSearcher
        s = ParameterSearcher(directive="fast")
        assert s.directive == "fast"

    def test_has_run_method(self):
        from agents.parameter_searcher import ParameterSearcher
        assert callable(ParameterSearcher().run)


# ── AgentResult: Structure ─────────────────────────────────────────────────────

class TestAgentResultStructure:
    @pytest.mark.asyncio
    async def test_returns_agent_result(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_success_status(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_data_has_optimized_pipeline(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "optimized_pipeline" in result.data

    @pytest.mark.asyncio
    async def test_data_has_quality_score(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "quality_score" in result.data

    @pytest.mark.asyncio
    async def test_data_has_search_summary(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "search_summary" in result.data

    @pytest.mark.asyncio
    async def test_optimized_pipeline_is_processing_pipeline(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert isinstance(result.data["optimized_pipeline"], ProcessingPipeline)

    @pytest.mark.asyncio
    async def test_quality_score_is_dict(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert isinstance(result.data["quality_score"], dict)

    @pytest.mark.asyncio
    async def test_quality_score_dict_has_overall_score(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "overall_score" in result.data["quality_score"]


# ── Search Summary ─────────────────────────────────────────────────────────────

class TestSearchSummary:
    @pytest.mark.asyncio
    async def test_has_total_combinations(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "total_combinations" in result.data["search_summary"]

    @pytest.mark.asyncio
    async def test_has_evaluated(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "evaluated" in result.data["search_summary"]

    @pytest.mark.asyncio
    async def test_has_best_score(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        assert "best_score" in result.data["search_summary"]

    @pytest.mark.asyncio
    async def test_evaluated_le_total(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _single_block_pipeline(
            "gaussian_fine", "denoise", {"kernel_size": [3, 5], "sigma": [0.5, 1.0]}
        )
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        s = result.data["search_summary"]
        assert s["evaluated"] <= s["total_combinations"]

    @pytest.mark.asyncio
    async def test_best_score_in_0_1(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image)
        best = result.data["search_summary"]["best_score"]
        assert 0.0 <= best <= 1.0


# ── Pipeline Optimization ──────────────────────────────────────────────────────

class TestPipelineOptimization:
    @pytest.mark.asyncio
    async def test_single_block_block_id_preserved(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _single_block_pipeline("grayscale", "color_space")
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        opt = result.data["optimized_pipeline"]
        assert opt.blocks[0].block_id == "grayscale"

    @pytest.mark.asyncio
    async def test_multi_block_count_preserved(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _multi_block_pipeline()
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        assert len(result.data["optimized_pipeline"].blocks) == len(pipeline.blocks)

    @pytest.mark.asyncio
    async def test_multi_block_ids_preserved(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _multi_block_pipeline()
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        opt = result.data["optimized_pipeline"]
        assert [b.block_id for b in opt.blocks] == [b.block_id for b in pipeline.blocks]

    @pytest.mark.asyncio
    async def test_optimized_params_are_specific_values(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _single_block_pipeline(
            "gaussian_fine", "denoise", {"kernel_size": [3, 5], "sigma": [0.5, 1.0]}
        )
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        opt = result.data["optimized_pipeline"]
        for block in opt.blocks:
            for v in block.params.values():
                assert not isinstance(v, list)

    @pytest.mark.asyncio
    async def test_pipeline_id_preserved(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _single_block_pipeline("grayscale", "color_space")
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        assert result.data["optimized_pipeline"].pipeline_id == pipeline.pipeline_id


# ── ROI Handling ───────────────────────────────────────────────────────────────

class TestROIHandling:
    @pytest.mark.asyncio
    async def test_roi_dict_accepted(self, bgr_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _single_block_pipeline("grayscale", "color_space")
        result = await ParameterSearcher().run(
            pipeline=pipeline, image=bgr_image, roi={"x": 10, "y": 10, "width": 50, "height": 50}
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_roi_none_succeeds(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = _single_block_pipeline("grayscale", "color_space")
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image, roi=None)
        assert result.status == "success"


# ── Error Handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_pipeline_status_error(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(
            pipeline=ProcessingPipeline(pipeline_id="empty", blocks=[]), image=gray_image
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_empty_pipeline_has_error_message(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(
            pipeline=ProcessingPipeline(pipeline_id="empty", blocks=[]), image=gray_image
        )
        assert result.error_message and len(result.error_message) > 0

    @pytest.mark.asyncio
    async def test_image_too_small_status_error(self, tiny_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(
            pipeline=_single_block_pipeline("grayscale", "color_space"), image=tiny_image
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_image_too_small_has_error_message(self, tiny_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(
            pipeline=_single_block_pipeline("grayscale", "color_space"), image=tiny_image
        )
        assert result.error_message and len(result.error_message) > 0


# ── Directive Handling ─────────────────────────────────────────────────────────

class TestDirectiveHandling:
    @pytest.mark.asyncio
    async def test_fast_directive_limits_to_30(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher(directive="fast").run(
            pipeline=_large_search_pipeline(), image=gray_image
        )
        assert result.status == "success"
        assert result.data["search_summary"]["evaluated"] <= 30

    @pytest.mark.asyncio
    async def test_thorough_directive_succeeds(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher(directive="thorough").run(
            pipeline=_single_block_pipeline("grayscale", "color_space"), image=gray_image
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_default_caps_at_100(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        result = await ParameterSearcher().run(pipeline=_large_search_pipeline(), image=gray_image)
        assert result.status == "success"
        assert result.data["search_summary"]["evaluated"] <= 100


# ── Registry Fallback ──────────────────────────────────────────────────────────

class TestRegistryFallback:
    @pytest.mark.asyncio
    async def test_unknown_block_id_does_not_crash(self, gray_image):
        from agents.parameter_searcher import ParameterSearcher
        pipeline = ProcessingPipeline(
            pipeline_id="fallback_pipe",
            blocks=[
                PipelineBlock(block_id="grayscale", block_type="color_space", params={}),
                PipelineBlock(block_id="unknown_block_xyz", block_type="denoise", params={}),
            ],
        )
        result = await ParameterSearcher().run(pipeline=pipeline, image=gray_image)
        assert result.status in ("success", "error")
