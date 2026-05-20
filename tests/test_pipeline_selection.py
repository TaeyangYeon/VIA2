"""Tests for PipelineSelector (Step 25)."""
import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock

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
def tiny_image():
    return np.zeros((2, 2), dtype=np.uint8)


def _make_pipeline(pipeline_id: str, block_id: str = "grayscale") -> ProcessingPipeline:
    return ProcessingPipeline(
        pipeline_id=pipeline_id,
        blocks=[PipelineBlock(block_id=block_id, block_type="color_space", params={})],
    )


def _make_quality_result(overall: float = 0.7, pipeline_id: str = "pipe_opt") -> AgentResult:
    return AgentResult(
        status="success",
        data={
            "optimized_pipeline": _make_pipeline(pipeline_id),
            "quality_score": {
                "contrast_score": 0.6,
                "noise_score": 0.7,
                "edge_score": 0.8,
                "overall_score": overall,
                "details": {},
            },
            "search_summary": {"total_combinations": 1, "evaluated": 1, "best_score": overall},
        },
    )


def _make_judge_result(vis: float = 0.8, sep: float = 0.7, meas: float = 0.6) -> AgentResult:
    overall = 0.4 * vis + 0.35 * sep + 0.25 * meas
    return AgentResult(
        status="success",
        data={
            "judgement": {
                "visibility_score": vis,
                "separability_score": sep,
                "measurability_score": meas,
                "overall_score": overall,
                "problems": [],
                "next_suggestion": "",
            }
        },
    )


def _make_mocks(quality_result=None, judge_result=None):
    mock_searcher = MagicMock()
    mock_searcher.run = AsyncMock(return_value=quality_result or _make_quality_result())
    mock_judge = MagicMock()
    mock_judge.run = AsyncMock(return_value=judge_result or _make_judge_result())
    return mock_searcher, mock_judge


# ── Instantiation ──────────────────────────────────────────────────────────────

class TestInstantiation:
    def test_can_be_instantiated(self):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        assert selector is not None

    def test_is_base_agent(self):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        assert isinstance(selector, BaseAgent)

    def test_name_is_pipeline_selection(self):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        assert selector.name == "pipeline_selection"

    def test_default_directive_is_empty(self):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        assert selector.directive == ""

    def test_accepts_directive(self):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(
            parameter_searcher=mock_searcher, vision_judge=mock_judge, directive="fast"
        )
        assert selector.directive == "fast"

    def test_has_run_method(self):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        assert callable(selector.run)


# ── AgentResult Structure ──────────────────────────────────────────────────────

class TestAgentResultStructure:
    @pytest.mark.asyncio
    async def test_returns_agent_result(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_success_status(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_data_has_selected_pipeline(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "selected_pipeline" in result.data

    @pytest.mark.asyncio
    async def test_data_has_selected_index(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "selected_index" in result.data

    @pytest.mark.asyncio
    async def test_data_has_combined_score(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "combined_score" in result.data

    @pytest.mark.asyncio
    async def test_data_has_quality_score(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "quality_score" in result.data

    @pytest.mark.asyncio
    async def test_data_has_judgement(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "judgement" in result.data

    @pytest.mark.asyncio
    async def test_data_has_all_candidates(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "all_candidates" in result.data

    @pytest.mark.asyncio
    async def test_selected_pipeline_is_processing_pipeline(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result.data["selected_pipeline"], ProcessingPipeline)

    @pytest.mark.asyncio
    async def test_selected_index_is_int(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result.data["selected_index"], int)

    @pytest.mark.asyncio
    async def test_combined_score_is_float(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result.data["combined_score"], float)

    @pytest.mark.asyncio
    async def test_all_candidates_is_list(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result.data["all_candidates"], list)

    @pytest.mark.asyncio
    async def test_quality_score_is_dict(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result.data["quality_score"], dict)

    @pytest.mark.asyncio
    async def test_judgement_is_dict(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert isinstance(result.data["judgement"], dict)


# ── Score Weighting ────────────────────────────────────────────────────────────

class TestScoreWeighting:
    @pytest.mark.asyncio
    async def test_combined_score_formula(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        quality_overall = 0.6
        vis, sep, meas = 0.8, 0.7, 0.6
        judgement_overall = (vis + sep + meas) / 3.0
        expected_combined = 0.4 * quality_overall + 0.6 * judgement_overall

        mock_searcher, mock_judge = _make_mocks(
            quality_result=_make_quality_result(overall=quality_overall),
            judge_result=_make_judge_result(vis=vis, sep=sep, meas=meas),
        )
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert abs(result.data["combined_score"] - expected_combined) < 1e-6

    @pytest.mark.asyncio
    async def test_quality_weight_0_4_higher_quality_wins(self, gray_image):
        """pipe_a has quality=0.9, pipe_b has quality=0.3 — equal judgement — pipe_a wins."""
        from agents.pipeline_selection import PipelineSelector
        vis, sep, meas = 0.5, 0.5, 0.5
        judge_result = _make_judge_result(vis=vis, sep=sep, meas=meas)

        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(side_effect=[
            _make_quality_result(overall=0.9),
            _make_quality_result(overall=0.3),
        ])
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=judge_result)

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["selected_index"] == 0

    @pytest.mark.asyncio
    async def test_judgement_weight_0_6_higher_judgement_wins(self, gray_image):
        """pipe_b has higher judgement — equal quality — pipe_b wins."""
        from agents.pipeline_selection import PipelineSelector
        quality_result = _make_quality_result(overall=0.5)

        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(return_value=quality_result)
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(side_effect=[
            _make_judge_result(vis=0.3, sep=0.3, meas=0.3),
            _make_judge_result(vis=0.9, sep=0.9, meas=0.9),
        ])

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["selected_index"] == 1

    @pytest.mark.asyncio
    async def test_judgement_overall_is_average_of_three_scores(self, gray_image):
        """Verify judgement_overall = (vis + sep + meas) / 3, not overall_score from judge."""
        from agents.pipeline_selection import PipelineSelector
        vis, sep, meas = 0.6, 0.9, 0.3
        quality_overall = 0.0
        expected_judgement_overall = (vis + sep + meas) / 3.0
        expected_combined = 0.4 * quality_overall + 0.6 * expected_judgement_overall

        mock_searcher, mock_judge = _make_mocks(
            quality_result=_make_quality_result(overall=quality_overall),
            judge_result=_make_judge_result(vis=vis, sep=sep, meas=meas),
        )
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert abs(result.data["combined_score"] - expected_combined) < 1e-6


# ── Pipeline Selection Logic ───────────────────────────────────────────────────

class TestPipelineSelectionLogic:
    @pytest.mark.asyncio
    async def test_single_candidate_selected_at_index_0(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["selected_index"] == 0

    @pytest.mark.asyncio
    async def test_best_pipeline_selected_among_three(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        quality_result = _make_quality_result(overall=0.5)

        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(return_value=quality_result)
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(side_effect=[
            _make_judge_result(vis=0.2, sep=0.2, meas=0.2),
            _make_judge_result(vis=0.9, sep=0.9, meas=0.9),
            _make_judge_result(vis=0.4, sep=0.4, meas=0.4),
        ])

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[
                _make_pipeline("pipe_a"),
                _make_pipeline("pipe_b"),
                _make_pipeline("pipe_c"),
            ],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["selected_index"] == 1

    @pytest.mark.asyncio
    async def test_all_candidates_length_matches_input(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert len(result.data["all_candidates"]) == 2

    @pytest.mark.asyncio
    async def test_all_candidates_has_pipeline_id(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "pipeline_id" in result.data["all_candidates"][0]

    @pytest.mark.asyncio
    async def test_all_candidates_has_combined_score(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "combined_score" in result.data["all_candidates"][0]

    @pytest.mark.asyncio
    async def test_all_candidates_has_quality_score(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "quality_score" in result.data["all_candidates"][0]

    @pytest.mark.asyncio
    async def test_all_candidates_has_judgement_score(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "judgement_score" in result.data["all_candidates"][0]

    @pytest.mark.asyncio
    async def test_all_candidates_has_status(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert "status" in result.data["all_candidates"][0]

    @pytest.mark.asyncio
    async def test_selected_pipeline_is_optimized_from_searcher(self, gray_image):
        """selected_pipeline should be the optimized pipeline returned by ParameterSearcher."""
        from agents.pipeline_selection import PipelineSelector
        quality_result = _make_quality_result(overall=0.7, pipeline_id="pipe_optimized_xyz")

        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(return_value=quality_result)
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["selected_pipeline"].pipeline_id == "pipe_optimized_xyz"

    @pytest.mark.asyncio
    async def test_successful_candidate_status_in_all_candidates(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["all_candidates"][0]["status"] == "success"

    @pytest.mark.asyncio
    async def test_all_candidates_pipeline_id_matches_input(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("my_pipe_123")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.data["all_candidates"][0]["pipeline_id"] == "my_pipe_123"


# ── Candidate Failure Handling ─────────────────────────────────────────────────

class TestCandidateFailureHandling:
    @pytest.mark.asyncio
    async def test_searcher_failure_marks_candidate_skipped(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(side_effect=[
            AgentResult(status="error", data={}, error_message="searcher failed"),
            _make_quality_result(overall=0.7),
        ])
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.status == "success"
        failed = next(c for c in result.data["all_candidates"] if c["pipeline_id"] == "pipe_a")
        assert failed["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_judge_failure_marks_candidate_skipped(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(side_effect=[
            _make_quality_result(overall=0.7),
            _make_quality_result(overall=0.5),
        ])
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(side_effect=[
            AgentResult(status="error", data={}, error_message="judge failed"),
            _make_judge_result(vis=0.8, sep=0.8, meas=0.8),
        ])

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.status == "success"
        failed = next(c for c in result.data["all_candidates"] if c["pipeline_id"] == "pipe_a")
        assert failed["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_failed_candidate_skipped_next_selected(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(side_effect=[
            AgentResult(status="error", data={}, error_message="searcher failed"),
            _make_quality_result(overall=0.7),
        ])
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.status == "success"
        assert result.data["selected_index"] == 1

    @pytest.mark.asyncio
    async def test_all_failed_returns_error(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="always fails"
        ))
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_all_failed_error_message(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(return_value=AgentResult(
            status="error", data={}, error_message="always fails"
        ))
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.error_message is not None
        assert "All candidate pipelines" in result.error_message

    @pytest.mark.asyncio
    async def test_exception_in_searcher_marks_candidate_skipped(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(side_effect=[
            RuntimeError("unexpected crash"),
            _make_quality_result(overall=0.7),
        ])
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        assert result.status == "success"
        failed = next(c for c in result.data["all_candidates"] if c["pipeline_id"] == "pipe_a")
        assert failed["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_all_candidates_includes_skipped_and_successful(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher = MagicMock()
        mock_searcher.run = AsyncMock(side_effect=[
            AgentResult(status="error", data={}, error_message="fail"),
            _make_quality_result(overall=0.7),
        ])
        mock_judge = MagicMock()
        mock_judge.run = AsyncMock(return_value=_make_judge_result())

        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_a"), _make_pipeline("pipe_b")],
            image=gray_image,
            purpose="defect detection",
        )
        statuses = {c["pipeline_id"]: c["status"] for c in result.data["all_candidates"]}
        assert statuses["pipe_a"] == "skipped"
        assert statuses["pipe_b"] == "success"


# ── Error Handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_pipelines_returns_error(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(pipelines=[], image=gray_image, purpose="defect detection")
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_empty_pipelines_error_message(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(pipelines=[], image=gray_image, purpose="defect detection")
        assert result.error_message is not None
        assert "No candidate pipelines" in result.error_message

    @pytest.mark.asyncio
    async def test_image_too_small_returns_error(self, tiny_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=tiny_image,
            purpose="defect detection",
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_image_too_small_error_message(self, tiny_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=tiny_image,
            purpose="defect detection",
        )
        assert result.error_message is not None
        assert "Image too small" in result.error_message

    @pytest.mark.asyncio
    async def test_empty_purpose_returns_error(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="",
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_empty_purpose_error_message(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="",
        )
        assert result.error_message is not None
        assert "Purpose is required" in result.error_message

    @pytest.mark.asyncio
    async def test_error_result_data_is_dict(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(pipelines=[], image=gray_image, purpose="defect detection")
        assert isinstance(result.data, dict)


# ── ROI Handling ───────────────────────────────────────────────────────────────

class TestROIHandling:
    @pytest.mark.asyncio
    async def test_roi_none_succeeds(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
            roi=None,
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_roi_dict_succeeds(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
            roi={"x1": 10, "y1": 10, "x2": 80, "y2": 80},
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_roi_passed_to_parameter_searcher(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        roi = {"x1": 10, "y1": 10, "x2": 80, "y2": 80}
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
            roi=roi,
        )
        assert mock_searcher.run.called
        call_kwargs = mock_searcher.run.call_args.kwargs
        assert "roi" in call_kwargs

    @pytest.mark.asyncio
    async def test_roi_crop_produces_output(self, bgr_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        result = await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=bgr_image,
            purpose="defect detection",
            roi={"x1": 5, "y1": 5, "x2": 50, "y2": 50},
        )
        assert result.status == "success"


# ── Pipeline Execution ─────────────────────────────────────────────────────────

class TestPipelineExecution:
    @pytest.mark.asyncio
    async def test_judge_called_with_processed_image(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        await selector.run(
            pipelines=[_make_pipeline("pipe_01", "grayscale")],
            image=gray_image,
            purpose="defect detection",
        )
        assert mock_judge.run.called
        call_kwargs = mock_judge.run.call_args.kwargs
        assert call_kwargs["processed_image"] is not None

    @pytest.mark.asyncio
    async def test_judge_called_with_original_image(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert np.array_equal(call_kwargs["original_image"], gray_image)

    @pytest.mark.asyncio
    async def test_judge_called_with_purpose(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="crack detection",
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert call_kwargs["purpose"] == "crack detection"

    @pytest.mark.asyncio
    async def test_processed_image_is_numpy_array(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert isinstance(call_kwargs["processed_image"], np.ndarray)


# ── Directive Handling ─────────────────────────────────────────────────────────

class TestDirectiveHandling:
    @pytest.mark.asyncio
    async def test_constructor_directive_passed_to_judge(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(
            parameter_searcher=mock_searcher,
            vision_judge=mock_judge,
            directive="fast",
        )
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert call_kwargs.get("directive") == "fast"

    @pytest.mark.asyncio
    async def test_run_directive_overrides_constructor(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(
            parameter_searcher=mock_searcher,
            vision_judge=mock_judge,
            directive="fast",
        )
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
            directive="thorough",
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert call_kwargs.get("directive") == "thorough"

    @pytest.mark.asyncio
    async def test_run_directive_none_falls_back_to_constructor(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(
            parameter_searcher=mock_searcher,
            vision_judge=mock_judge,
            directive="fast",
        )
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
            directive=None,
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert call_kwargs.get("directive") == "fast"

    @pytest.mark.asyncio
    async def test_empty_directive_passed_when_no_directive_set(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(parameter_searcher=mock_searcher, vision_judge=mock_judge)
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        call_kwargs = mock_judge.run.call_args.kwargs
        assert call_kwargs.get("directive") == ""

    @pytest.mark.asyncio
    async def test_directive_passed_to_parameter_searcher(self, gray_image):
        from agents.pipeline_selection import PipelineSelector
        mock_searcher, mock_judge = _make_mocks()
        selector = PipelineSelector(
            parameter_searcher=mock_searcher,
            vision_judge=mock_judge,
            directive="fast",
        )
        await selector.run(
            pipelines=[_make_pipeline("pipe_01")],
            image=gray_image,
            purpose="defect detection",
        )
        assert mock_searcher.run.called
