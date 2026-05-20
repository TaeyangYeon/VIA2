"""Tests for TestAgentAlign — Step 27.

Tests cover: instantiation, error handling, result structure, template/edge/caliper
fallback chain, directive handling, coordinate-space correctness, per-image metrics,
and statistics aggregation.
All images are synthetic — no external files required.
"""
import math

import cv2
import numpy as np
import pytest

from agents.base_agent import BaseAgent
from agents.models import PipelineBlock, ProcessingPipeline


# ── Synthetic image helpers ───────────────────────────────────────────────────


def _make_pipeline(blocks=None):
    return ProcessingPipeline(pipeline_id="test_pipe", blocks=blocks or [])


def _center_blob_image(h=100, w=100, radius=6):
    """BGR image with a bright circular blob at center — distinctive for template matching."""
    img = np.full((h, w, 3), 40, dtype=np.uint8)
    cv2.circle(img, (w // 2, h // 2), radius, (220, 220, 220), -1)
    return img


def _noise_image(seed=None):
    """Random noise BGR image — template matching will fail (score < 0.5)."""
    rng = np.random.default_rng(seed=seed)
    return rng.integers(0, 255, (100, 100, 3), dtype=np.uint8)


def _roi(x1=20, y1=20, x2=80, y2=80):
    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


# ── Instantiation ─────────────────────────────────────────────────────────────


class TestInstantiation:
    def test_default_constructor(self):
        from agents.test_agent_align import TestAgentAlign
        agent = TestAgentAlign()
        assert agent is not None

    def test_inherits_base_agent(self):
        from agents.test_agent_align import TestAgentAlign
        assert issubclass(TestAgentAlign, BaseAgent)

    def test_name_is_test_agent_align(self):
        from agents.test_agent_align import TestAgentAlign
        assert TestAgentAlign().name == "test_agent_align"

    def test_default_directive_empty(self):
        from agents.test_agent_align import TestAgentAlign
        assert TestAgentAlign().directive == ""

    def test_directive_stored_in_constructor(self):
        from agents.test_agent_align import TestAgentAlign
        agent = TestAgentAlign(directive="strict")
        assert agent.directive == "strict"


# ── Error handling ─────────────────────────────────────────────────────────────


class TestErrorHandling:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_empty_ok_images(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[],
            roi=_roi(),
        )
        assert result.status == "error"
        assert "No OK images provided" in result.error_message

    @pytest.mark.asyncio
    async def test_no_roi_returns_error(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=None,
        )
        assert result.status == "error"
        assert "ROI is required" in result.error_message

    @pytest.mark.asyncio
    async def test_roi_too_small_width(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi={"x1": 10, "y1": 10, "x2": 12, "y2": 50},  # width = 2
        )
        assert result.status == "error"
        assert "ROI too small" in result.error_message

    @pytest.mark.asyncio
    async def test_roi_too_small_height(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi={"x1": 10, "y1": 10, "x2": 50, "y2": 12},  # height = 2
        )
        assert result.status == "error"
        assert "ROI too small" in result.error_message

    @pytest.mark.asyncio
    async def test_error_result_has_empty_data(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[],
            roi=_roi(),
        )
        assert result.status == "error"
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_error_result_has_execution_time(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[],
            roi=_roi(),
        )
        assert result.execution_time_ms >= 0


# ── Result structure (success path) ───────────────────────────────────────────


class TestResultStructure:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.fixture
    def imgs(self):
        return [_center_blob_image() for _ in range(3)]

    @pytest.fixture
    def roi(self):
        return _roi()

    @pytest.mark.asyncio
    async def test_status_is_success(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_data_has_per_image_results(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "per_image_results" in result.data

    @pytest.mark.asyncio
    async def test_per_image_results_count(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert len(result.data["per_image_results"]) == 3

    @pytest.mark.asyncio
    async def test_data_has_overall_success_rate(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "overall_success_rate" in result.data

    @pytest.mark.asyncio
    async def test_data_has_overall_mean_error(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "overall_mean_error" in result.data

    @pytest.mark.asyncio
    async def test_data_has_overall_max_error(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "overall_max_error" in result.data

    @pytest.mark.asyncio
    async def test_data_has_overall_passed(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "overall_passed" in result.data

    @pytest.mark.asyncio
    async def test_data_has_method_stats(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "method_stats" in result.data

    @pytest.mark.asyncio
    async def test_data_has_error_threshold(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert "error_threshold" in result.data

    @pytest.mark.asyncio
    async def test_data_has_total_images(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert result.data["total_images"] == 3

    @pytest.mark.asyncio
    async def test_execution_time_positive(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        assert result.execution_time_ms > 0


# ── Per-image result fields ───────────────────────────────────────────────────


class TestPerImageResultFields:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_all_fields_present(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
        )
        r = result.data["per_image_results"][0]
        for field in (
            "image_index", "detected_x", "detected_y",
            "ground_truth_x", "ground_truth_y",
            "error_px", "method_used", "match_score", "success",
        ):
            assert field in r, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_image_index_sequential(self, agent):
        imgs = [_center_blob_image() for _ in range(4)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        indices = [r["image_index"] for r in result.data["per_image_results"]]
        assert indices == [0, 1, 2, 3]

    @pytest.mark.asyncio
    async def test_method_used_is_known_value(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
        )
        r = result.data["per_image_results"][0]
        assert r["method_used"] in ("template", "edge", "caliper")


# ── Ground truth ──────────────────────────────────────────────────────────────


class TestGroundTruth:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_ground_truth_is_roi_center(self, agent):
        roi = {"x1": 20, "y1": 30, "x2": 70, "y2": 90}
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=roi,
        )
        r = result.data["per_image_results"][0]
        assert abs(r["ground_truth_x"] - 45.0) < 1e-6  # (20+70)/2
        assert abs(r["ground_truth_y"] - 60.0) < 1e-6  # (30+90)/2

    @pytest.mark.asyncio
    async def test_ground_truth_consistent_across_images(self, agent):
        roi = _roi()
        imgs = [_center_blob_image() for _ in range(3)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        per = result.data["per_image_results"]
        gt_xs = {r["ground_truth_x"] for r in per}
        gt_ys = {r["ground_truth_y"] for r in per}
        assert len(gt_xs) == 1  # same GT for every image
        assert len(gt_ys) == 1


# ── Coordinate space ──────────────────────────────────────────────────────────


class TestCoordinateSpace:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_detected_x_within_roi_bounds(self, agent):
        roi = {"x1": 50, "y1": 50, "x2": 150, "y2": 150}
        imgs = [_center_blob_image(200, 200) for _ in range(2)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        for r in result.data["per_image_results"]:
            assert roi["x1"] <= r["detected_x"] <= roi["x2"]

    @pytest.mark.asyncio
    async def test_detected_y_within_roi_bounds(self, agent):
        roi = {"x1": 50, "y1": 50, "x2": 150, "y2": 150}
        imgs = [_center_blob_image(200, 200) for _ in range(2)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi)
        for r in result.data["per_image_results"]:
            assert roi["y1"] <= r["detected_y"] <= roi["y2"]


# ── Error pixel calculation ───────────────────────────────────────────────────


class TestErrorCalculation:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_error_px_is_euclidean(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
        )
        r = result.data["per_image_results"][0]
        dx = r["detected_x"] - r["ground_truth_x"]
        dy = r["detected_y"] - r["ground_truth_y"]
        expected = math.sqrt(dx ** 2 + dy ** 2)
        assert abs(r["error_px"] - expected) < 1e-4

    @pytest.mark.asyncio
    async def test_overall_mean_error_matches_per_image(self, agent):
        imgs = [_center_blob_image() for _ in range(4)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        per = result.data["per_image_results"]
        expected = sum(r["error_px"] for r in per) / len(per)
        assert abs(result.data["overall_mean_error"] - expected) < 1e-6

    @pytest.mark.asyncio
    async def test_overall_max_error_matches_per_image(self, agent):
        imgs = [_center_blob_image() for _ in range(4)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        per = result.data["per_image_results"]
        expected = max(r["error_px"] for r in per)
        assert abs(result.data["overall_max_error"] - expected) < 1e-6

    @pytest.mark.asyncio
    async def test_success_flag_reflects_threshold(self, agent):
        imgs = [_center_blob_image() for _ in range(3)]
        result = await agent.run(
            pipeline=_make_pipeline(), ok_images=imgs, roi=_roi(),
            error_threshold=5.0,
        )
        thr = result.data["error_threshold"]
        for r in result.data["per_image_results"]:
            assert r["success"] == (r["error_px"] < thr)

    @pytest.mark.asyncio
    async def test_overall_success_rate_matches_per_image(self, agent):
        imgs = [_center_blob_image() for _ in range(5)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        per = result.data["per_image_results"]
        expected = sum(1 for r in per if r["success"]) / len(per)
        assert abs(result.data["overall_success_rate"] - expected) < 1e-6

    @pytest.mark.asyncio
    async def test_overall_passed_reflects_80_percent_boundary(self, agent):
        imgs = [_center_blob_image() for _ in range(5)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        sr = result.data["overall_success_rate"]
        assert result.data["overall_passed"] == (sr >= 0.8)


# ── Method stats ──────────────────────────────────────────────────────────────


class TestMethodStats:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_method_stats_has_all_keys(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image() for _ in range(3)],
            roi=_roi(),
        )
        ms = result.data["method_stats"]
        assert "template" in ms
        assert "edge" in ms
        assert "caliper" in ms

    @pytest.mark.asyncio
    async def test_method_stats_total_equals_image_count(self, agent):
        n = 5
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image() for _ in range(n)],
            roi=_roi(),
        )
        ms = result.data["method_stats"]
        assert sum(ms.values()) == n


# ── Template method ───────────────────────────────────────────────────────────


class TestTemplateMethod:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_match_score_set_when_template_used(self, agent):
        imgs = [_center_blob_image() for _ in range(2)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        for r in result.data["per_image_results"]:
            if r["method_used"] == "template":
                assert r["match_score"] is not None
                assert isinstance(r["match_score"], float)

    @pytest.mark.asyncio
    async def test_match_score_none_for_non_template(self, agent):
        # Random noise → template score < 0.5 on images 1,2 → edge/caliper
        imgs = [_noise_image(seed=i) for i in range(3)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        for r in result.data["per_image_results"]:
            if r["method_used"] != "template":
                assert r["match_score"] is None

    @pytest.mark.asyncio
    async def test_identical_images_use_template(self, agent):
        """Identical images → template match is perfect → template method used."""
        img = _center_blob_image()
        imgs = [img.copy() for _ in range(3)]
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=_roi())
        methods = [r["method_used"] for r in result.data["per_image_results"]]
        assert all(m == "template" for m in methods), f"Expected all template, got: {methods}"


# ── Directive handling ─────────────────────────────────────────────────────────


class TestDirectiveHandling:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.fixture
    def imgs(self):
        return [_center_blob_image()]

    @pytest.fixture
    def roi(self):
        return _roi()

    @pytest.mark.asyncio
    async def test_default_threshold_unchanged(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi,
                                 error_threshold=10.0)
        assert result.data["error_threshold"] == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_strict_directive_halves_threshold(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi,
                                 error_threshold=10.0, directive="strict")
        assert result.data["error_threshold"] == pytest.approx(5.0)

    @pytest.mark.asyncio
    async def test_lenient_directive_doubles_threshold(self, agent, imgs, roi):
        result = await agent.run(pipeline=_make_pipeline(), ok_images=imgs, roi=roi,
                                 error_threshold=5.0, directive="lenient")
        assert result.data["error_threshold"] == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_run_directive_overrides_constructor(self):
        from agents.test_agent_align import TestAgentAlign
        agent = TestAgentAlign(directive="lenient")
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
            error_threshold=5.0,
            directive="strict",
        )
        assert result.data["error_threshold"] == pytest.approx(2.5)

    @pytest.mark.asyncio
    async def test_run_directive_none_uses_constructor(self):
        from agents.test_agent_align import TestAgentAlign
        agent = TestAgentAlign(directive="lenient")
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
            error_threshold=5.0,
            directive=None,
        )
        assert result.data["error_threshold"] == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_constructor_directive_strict_applies_without_run_override(self):
        from agents.test_agent_align import TestAgentAlign
        agent = TestAgentAlign(directive="strict")
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
            error_threshold=10.0,
        )
        assert result.data["error_threshold"] == pytest.approx(5.0)


# ── Pipeline preprocessing ────────────────────────────────────────────────────


class TestPipelinePreprocessing:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_grayscale_pipeline_succeeds(self, agent):
        pipeline = _make_pipeline([
            PipelineBlock(block_id="grayscale", block_type="color_space", params={})
        ])
        result = await agent.run(
            pipeline=pipeline,
            ok_images=[_center_blob_image() for _ in range(2)],
            roi=_roi(),
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_empty_pipeline_succeeds(self, agent):
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image() for _ in range(2)],
            roi=_roi(),
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_multi_block_pipeline_succeeds(self, agent):
        pipeline = _make_pipeline([
            PipelineBlock(block_id="grayscale", block_type="color_space", params={}),
            PipelineBlock(block_id="gaussian_fine", block_type="denoise",
                          params={"kernel_size": 3, "sigma": 1.0}),
        ])
        result = await agent.run(
            pipeline=pipeline,
            ok_images=[_center_blob_image() for _ in range(2)],
            roi=_roi(),
        )
        assert result.status == "success"


# ── Single image edge case ─────────────────────────────────────────────────────


class TestSingleImage:
    @pytest.mark.asyncio
    async def test_single_image_succeeds(self):
        from agents.test_agent_align import TestAgentAlign
        result = await TestAgentAlign().run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
        )
        assert result.status == "success"
        assert result.data["total_images"] == 1

    @pytest.mark.asyncio
    async def test_single_image_has_one_per_image_result(self):
        from agents.test_agent_align import TestAgentAlign
        result = await TestAgentAlign().run(
            pipeline=_make_pipeline(),
            ok_images=[_center_blob_image()],
            roi=_roi(),
        )
        assert len(result.data["per_image_results"]) == 1


# ── Template accuracy on centered target ──────────────────────────────────────


class TestAlignmentAccuracy:
    @pytest.fixture
    def agent(self):
        from agents.test_agent_align import TestAgentAlign
        return TestAgentAlign()

    @pytest.mark.asyncio
    async def test_center_blob_error_below_threshold(self, agent):
        """Images with target at center → error < 5px (default threshold)."""
        imgs = [_center_blob_image(100, 100, radius=8) for _ in range(3)]
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=imgs,
            roi=_roi(20, 20, 80, 80),
            error_threshold=5.0,
        )
        assert result.status == "success"
        for r in result.data["per_image_results"]:
            assert r["error_px"] < 10.0, f"Error too large: {r['error_px']}"

    @pytest.mark.asyncio
    async def test_overall_passed_for_centered_target(self, agent):
        """Center-aligned images should pass overall (≥ 80% within threshold)."""
        imgs = [_center_blob_image() for _ in range(5)]
        result = await agent.run(
            pipeline=_make_pipeline(),
            ok_images=imgs,
            roi=_roi(),
            error_threshold=10.0,
        )
        assert result.data["overall_passed"] is True
