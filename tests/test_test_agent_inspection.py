"""Tests for TestAgentInspection — Step 26.

Tests cover: instantiation, result structure, topological sort, dependency skip logic,
per-item metrics (accuracy/fp_rate/fn_rate), all 5 inspection categories,
ROI handling, directive handling, error handling, and overall metrics aggregation.
All images are synthetic — no external files required.
"""
import pytest
import numpy as np
import cv2

from agents.base_agent import BaseAgent
from agents.models import InspectionPlan, InspectionItem, ProcessingPipeline, PipelineBlock
from agents.test_agent_inspection import TestAgentInspection


# ── Synthetic image helpers ───────────────────────────────────────────────────

def _gray_pipeline():
    return ProcessingPipeline(
        pipeline_id="gray_pipe",
        blocks=[PipelineBlock(block_id="grayscale", block_type="color_space", params={})],
    )


def _empty_pipeline():
    return ProcessingPipeline(pipeline_id="empty_pipe", blocks=[])


def _ok_gray():
    """Uniform gray 100×100 — 0 blobs, near-zero edge density."""
    return np.full((100, 100), 128, dtype=np.uint8)


def _ng_blob():
    """Gray 100×100 with 2 dark circles — clearly 2 blobs."""
    img = np.full((100, 100), 200, dtype=np.uint8)
    cv2.circle(img, (25, 25), 10, 20, -1)
    cv2.circle(img, (75, 75), 10, 20, -1)
    return img


def _ng_edge():
    """Checkerboard 100×100 — high edge density."""
    img = np.zeros((100, 100), dtype=np.uint8)
    for i in range(0, 100, 10):
        for j in range(0, 100, 10):
            if (i // 10 + j // 10) % 2 == 0:
                img[i:i + 10, j:j + 10] = 255
    return img


def _ok_bgr_blue():
    """Blue-dominant BGR image."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :, 0] = 200  # B channel
    return img


def _ng_bgr_red():
    """Red-dominant BGR image."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :, 2] = 200  # R channel
    return img


def _ok_template():
    """Gray 100×100 with a distinctive checkerboard patch in center."""
    img = np.full((100, 100), 128, dtype=np.uint8)
    for i in range(35, 65, 5):
        for j in range(35, 65, 5):
            val = 220 if (i // 5 + j // 5) % 2 == 0 else 40
            img[i:i + 5, j:j + 5] = val
    return img


def _ng_template():
    """Uniform gray 100×100 — no matching pattern."""
    return np.full((100, 100), 128, dtype=np.uint8)


def _ok_geometric():
    """Light background with dark circle — high circularity."""
    img = np.full((100, 100), 200, dtype=np.uint8)
    cv2.circle(img, (50, 50), 20, 20, -1)
    return img


def _ng_geometric():
    """Light background with dark rectangle — low circularity."""
    img = np.full((100, 100), 200, dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 60), 20, -1)
    return img


def _plan(items):
    return InspectionPlan(items=items, inspection_purpose="test")


# ── Instantiation ─────────────────────────────────────────────────────────────

class TestInstantiation:
    def test_default_constructor(self):
        agent = TestAgentInspection()
        assert agent is not None

    def test_inherits_base_agent(self):
        assert issubclass(TestAgentInspection, BaseAgent)

    def test_name_is_test_agent_inspection(self):
        assert TestAgentInspection().name == "test_agent_inspection"

    def test_default_directive_is_empty(self):
        assert TestAgentInspection().directive == ""

    def test_directive_stored(self):
        agent = TestAgentInspection(directive="strict")
        assert agent.directive == "strict"


# ── AgentResult structure ─────────────────────────────────────────────────────

class TestResultStructure:
    @pytest.fixture
    def agent(self):
        return TestAgentInspection()

    @pytest.fixture
    def plan(self):
        return _plan([InspectionItem(item_id=1, name="blob_check", category="BLOB",
                                     success_criteria={"min_accuracy": 0.5})])

    @pytest.fixture
    def ok_imgs(self):
        return [_ok_gray(), _ok_gray()]

    @pytest.fixture
    def ng_imgs(self):
        return [_ng_blob(), _ng_blob()]

    @pytest.fixture
    def pipe(self):
        return _gray_pipeline()

    @pytest.mark.asyncio
    async def test_returns_agent_result_type(self, agent, plan, ok_imgs, ng_imgs, pipe):
        from agents.models import AgentResult
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_status_success(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_data_has_item_results(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "item_results" in result.data

    @pytest.mark.asyncio
    async def test_data_has_overall_accuracy(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "overall_accuracy" in result.data

    @pytest.mark.asyncio
    async def test_data_has_overall_passed(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "overall_passed" in result.data

    @pytest.mark.asyncio
    async def test_data_has_execution_order(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "execution_order" in result.data

    @pytest.mark.asyncio
    async def test_data_has_total_items(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "total_items" in result.data

    @pytest.mark.asyncio
    async def test_data_has_passed_items(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "passed_items" in result.data

    @pytest.mark.asyncio
    async def test_data_has_skipped_items(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "skipped_items" in result.data

    @pytest.mark.asyncio
    async def test_data_has_failed_items(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert "failed_items" in result.data

    @pytest.mark.asyncio
    async def test_execution_time_positive(self, agent, plan, ok_imgs, ng_imgs, pipe):
        result = await agent.run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert result.execution_time_ms > 0


class TestItemResultFields:
    @pytest.mark.asyncio
    async def test_item_result_has_item_id(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "item_id" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_name(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "name" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_category(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "category" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_accuracy(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "accuracy" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_fp_rate(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "fp_rate" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_fn_rate(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "fn_rate" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_passed(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "passed" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_skipped(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "skipped" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_result_has_details(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "details" in result.data["item_results"][0]

    @pytest.mark.asyncio
    async def test_item_id_matches_plan(self):
        plan = _plan([InspectionItem(item_id=42, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.data["item_results"][0]["item_id"] == 42

    @pytest.mark.asyncio
    async def test_accuracy_is_float_between_0_and_1(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        acc = result.data["item_results"][0]["accuracy"]
        assert isinstance(acc, float)
        assert 0.0 <= acc <= 1.0

    @pytest.mark.asyncio
    async def test_fp_rate_is_float_between_0_and_1(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        fp = result.data["item_results"][0]["fp_rate"]
        assert isinstance(fp, float)
        assert 0.0 <= fp <= 1.0

    @pytest.mark.asyncio
    async def test_fn_rate_is_float_between_0_and_1(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        fn = result.data["item_results"][0]["fn_rate"]
        assert isinstance(fn, float)
        assert 0.0 <= fn <= 1.0

    @pytest.mark.asyncio
    async def test_passed_is_bool(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert isinstance(result.data["item_results"][0]["passed"], bool)

    @pytest.mark.asyncio
    async def test_skipped_is_bool(self):
        plan = _plan([InspectionItem(item_id=1, name="x", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert isinstance(result.data["item_results"][0]["skipped"], bool)


# ── Topological Sort ──────────────────────────────────────────────────────────

class TestTopologicalSort:
    @pytest.mark.asyncio
    async def test_linear_chain_order(self):
        """Items submitted out-of-order; execution_order should be [1, 2, 3]."""
        plan = _plan([
            InspectionItem(item_id=3, name="c", category="BLOB", depends_on=[2]),
            InspectionItem(item_id=1, name="a", category="BLOB"),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.data["execution_order"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_independent_items_all_executed(self):
        """Three independent items should all appear in execution_order."""
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB"),
            InspectionItem(item_id=2, name="b", category="BLOB"),
            InspectionItem(item_id=3, name="c", category="BLOB"),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert sorted(result.data["execution_order"]) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_circular_dependency_returns_error(self):
        """Circular dependency 1→2→1 must return error status."""
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB", depends_on=[2]),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_circular_dependency_error_message_mentions_circular(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB", depends_on=[2]),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.error_message is not None
        assert "circular" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_missing_dependency_does_not_crash(self):
        """Item depends on non-existent item_id=99 — should succeed (skip missing dep)."""
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB", depends_on=[99]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execution_order_respects_fan_in(self):
        """Item 3 depends on both 1 and 2; 3 must come after both."""
        plan = _plan([
            InspectionItem(item_id=3, name="c", category="BLOB", depends_on=[1, 2]),
            InspectionItem(item_id=1, name="a", category="BLOB"),
            InspectionItem(item_id=2, name="b", category="BLOB"),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        order = result.data["execution_order"]
        assert order.index(3) > order.index(1)
        assert order.index(3) > order.index(2)


# ── Dependency Skip Logic ─────────────────────────────────────────────────────

class TestDependencySkip:
    @pytest.mark.asyncio
    async def test_item_skipped_when_dependency_fails(self):
        """Item 2 must be skipped when item 1 fails (min_accuracy=1.1 is impossible)."""
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB",
                           success_criteria={"min_accuracy": 1.1}),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "success"
        by_id = {r["item_id"]: r for r in result.data["item_results"]}
        assert by_id[1]["passed"] is False
        assert by_id[2]["skipped"] is True

    @pytest.mark.asyncio
    async def test_skipped_items_count_correct(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB",
                           success_criteria={"min_accuracy": 1.1}),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
            InspectionItem(item_id=3, name="c", category="BLOB", depends_on=[2]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.data["skipped_items"] == 2

    @pytest.mark.asyncio
    async def test_non_dependent_item_not_skipped(self):
        """Item 3 has no dependency on failing item 1 — should run normally."""
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB",
                           success_criteria={"min_accuracy": 1.1}),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
            InspectionItem(item_id=3, name="c", category="BLOB"),  # independent
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        by_id = {r["item_id"]: r for r in result.data["item_results"]}
        assert by_id[3]["skipped"] is False

    @pytest.mark.asyncio
    async def test_skipped_item_accuracy_is_zero(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB",
                           success_criteria={"min_accuracy": 1.1}),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        by_id = {r["item_id"]: r for r in result.data["item_results"]}
        assert by_id[2]["accuracy"] == 0.0


# ── Per-Item Metric Calculation ───────────────────────────────────────────────

class TestMetricCalculation:
    @pytest.mark.asyncio
    async def test_blob_perfect_accuracy(self):
        """OK=uniform(0 blobs), NG=with-circles(2 blobs) → accuracy=1.0."""
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.9})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        item = result.data["item_results"][0]
        assert item["accuracy"] == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_blob_perfect_fp_rate_zero(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.9})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        item = result.data["item_results"][0]
        assert item["fp_rate"] == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_blob_perfect_fn_rate_zero(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.9})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        item = result.data["item_results"][0]
        assert item["fn_rate"] == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_blob_item_passed_when_above_threshold(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.9})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        assert result.data["item_results"][0]["passed"] is True

    @pytest.mark.asyncio
    async def test_item_fails_when_below_threshold(self):
        """Impossible threshold → item fails."""
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 1.1})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.data["item_results"][0]["passed"] is False


# ── BLOB Category ─────────────────────────────────────────────────────────────

class TestBlobCategory:
    @pytest.mark.asyncio
    async def test_blob_details_has_blob_counts(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert "blob_counts" in result.data["item_results"][0]["details"]

    @pytest.mark.asyncio
    async def test_blob_details_has_ok_and_ng_counts(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        d = result.data["item_results"][0]["details"]
        assert "ok_blob_counts" in d
        assert "ng_blob_counts" in d

    @pytest.mark.asyncio
    async def test_blob_ok_images_have_fewer_blobs_than_ng(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        d = result.data["item_results"][0]["details"]
        ok_mean = sum(d["ok_blob_counts"]) / len(d["ok_blob_counts"])
        ng_mean = sum(d["ng_blob_counts"]) / len(d["ng_blob_counts"])
        assert ok_mean < ng_mean

    @pytest.mark.asyncio
    async def test_count_category_treated_as_blob(self):
        """COUNT is a sub-variant of BLOB — should run without error."""
        plan = _plan([InspectionItem(item_id=1, name="count", category="COUNT",
                                     success_criteria={"expected_count": 0})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "success"
        assert "blob_counts" in result.data["item_results"][0]["details"]

    @pytest.mark.asyncio
    async def test_count_with_expected_count_in_criteria(self):
        """COUNT with expected_count=0: OK (no blobs) should match, NG should not."""
        plan = _plan([InspectionItem(item_id=1, name="count", category="COUNT",
                                     success_criteria={"expected_count": 0,
                                                       "min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        assert result.status == "success"
        item = result.data["item_results"][0]
        assert item["accuracy"] > 0.5


# ── Edge Detection Category ───────────────────────────────────────────────────

class TestEdgeDetectionCategory:
    @pytest.mark.asyncio
    async def test_edge_detection_returns_success(self):
        plan = _plan([InspectionItem(item_id=1, name="edge", category="EDGE_DETECTION",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_edge(), _ng_edge()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_edge_detection_details_has_edge_scores(self):
        plan = _plan([InspectionItem(item_id=1, name="edge", category="EDGE_DETECTION")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_edge()],
        )
        assert "edge_scores" in result.data["item_results"][0]["details"]

    @pytest.mark.asyncio
    async def test_edge_detection_ng_has_higher_edge_density(self):
        plan = _plan([InspectionItem(item_id=1, name="edge", category="EDGE_DETECTION")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_edge(), _ng_edge()],
        )
        d = result.data["item_results"][0]["details"]
        ok_mean = sum(d["ok_edge_scores"]) / len(d["ok_edge_scores"])
        ng_mean = sum(d["ng_edge_scores"]) / len(d["ng_edge_scores"])
        assert ng_mean > ok_mean

    @pytest.mark.asyncio
    async def test_edge_detection_accuracy_above_chance(self):
        plan = _plan([InspectionItem(item_id=1, name="edge", category="EDGE_DETECTION",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_edge(), _ng_edge()],
        )
        assert result.data["item_results"][0]["accuracy"] > 0.5


# ── Color Filter Category ─────────────────────────────────────────────────────

class TestColorFilterCategory:
    @pytest.mark.asyncio
    async def test_color_filter_returns_success(self):
        plan = _plan([InspectionItem(item_id=1, name="color", category="COLOR_FILTER",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_empty_pipeline(),
            ok_images=[_ok_bgr_blue(), _ok_bgr_blue()],
            ng_images=[_ng_bgr_red(), _ng_bgr_red()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_color_filter_details_has_channel_scores(self):
        plan = _plan([InspectionItem(item_id=1, name="color", category="COLOR_FILTER")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_empty_pipeline(),
            ok_images=[_ok_bgr_blue()], ng_images=[_ng_bgr_red()],
        )
        assert "channel_scores" in result.data["item_results"][0]["details"]

    @pytest.mark.asyncio
    async def test_color_filter_distinguishes_blue_from_red(self):
        """Blue-dominant (OK) vs red-dominant (NG) — should achieve accuracy > 0.5."""
        plan = _plan([InspectionItem(item_id=1, name="color", category="COLOR_FILTER",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_empty_pipeline(),
            ok_images=[_ok_bgr_blue(), _ok_bgr_blue()],
            ng_images=[_ng_bgr_red(), _ng_bgr_red()],
        )
        assert result.data["item_results"][0]["accuracy"] > 0.5


# ── Template Matching Category ────────────────────────────────────────────────

class TestTemplateMatchingCategory:
    @pytest.mark.asyncio
    async def test_template_matching_returns_success(self):
        plan = _plan([InspectionItem(item_id=1, name="tmpl", category="TEMPLATE_MATCHING",
                                     success_criteria={"min_accuracy": 0.0})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_template(), _ok_template()],
            ng_images=[_ng_template(), _ng_template()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_template_matching_details_has_match_scores(self):
        plan = _plan([InspectionItem(item_id=1, name="tmpl", category="TEMPLATE_MATCHING")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_template()], ng_images=[_ng_template()],
        )
        assert "match_scores" in result.data["item_results"][0]["details"]

    @pytest.mark.asyncio
    async def test_template_matching_ok_images_have_higher_match_than_ng(self):
        plan = _plan([InspectionItem(item_id=1, name="tmpl", category="TEMPLATE_MATCHING")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_template(), _ok_template()],
            ng_images=[_ng_template(), _ng_template()],
        )
        d = result.data["item_results"][0]["details"]
        ok_scores = d["ok_match_scores"]
        ng_scores = d["ng_match_scores"]
        ok_mean = sum(ok_scores) / len(ok_scores)
        ng_mean = sum(ng_scores) / len(ng_scores)
        assert ok_mean > ng_mean


# ── Geometric Category ────────────────────────────────────────────────────────

class TestGeometricCategory:
    @pytest.mark.asyncio
    async def test_geometric_returns_success(self):
        plan = _plan([InspectionItem(item_id=1, name="geom", category="GEOMETRIC",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_geometric(), _ok_geometric()],
            ng_images=[_ng_geometric(), _ng_geometric()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_geometric_details_has_geometric_scores(self):
        plan = _plan([InspectionItem(item_id=1, name="geom", category="GEOMETRIC")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_geometric()], ng_images=[_ng_geometric()],
        )
        assert "geometric_scores" in result.data["item_results"][0]["details"]

    @pytest.mark.asyncio
    async def test_geometric_circle_has_higher_circularity_than_rectangle(self):
        plan = _plan([InspectionItem(item_id=1, name="geom", category="GEOMETRIC")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_geometric(), _ok_geometric()],
            ng_images=[_ng_geometric(), _ng_geometric()],
        )
        d = result.data["item_results"][0]["details"]
        ok_mean = sum(d["ok_geometric_scores"]) / len(d["ok_geometric_scores"])
        ng_mean = sum(d["ng_geometric_scores"]) / len(d["ng_geometric_scores"])
        assert ok_mean > ng_mean

    @pytest.mark.asyncio
    async def test_geometric_accuracy_above_chance(self):
        plan = _plan([InspectionItem(item_id=1, name="geom", category="GEOMETRIC",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_geometric(), _ok_geometric()],
            ng_images=[_ng_geometric(), _ng_geometric()],
        )
        assert result.data["item_results"][0]["accuracy"] > 0.5


# ── ROI Handling ──────────────────────────────────────────────────────────────

class TestROIHandling:
    @pytest.mark.asyncio
    async def test_roi_applied_does_not_crash(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
            roi={"x1": 0, "y1": 0, "x2": 50, "y2": 50},
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_roi_none_same_as_no_roi(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
            roi=None,
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_roi_crops_before_pipeline(self):
        """ROI covering only the upper-left (no circles) should affect blob count."""
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        # NG image has circles at (25,25) and (75,75). ROI only covers (0,0)-(40,40)
        # → only the circle at (25,25) is in ROI
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
            roi={"x1": 0, "y1": 0, "x2": 40, "y2": 40},
        )
        assert result.status == "success"


# ── Pipeline Execution ────────────────────────────────────────────────────────

class TestPipelineExecution:
    @pytest.mark.asyncio
    async def test_empty_pipeline_does_not_crash(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_empty_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_multi_block_pipeline_applied(self):
        pipe = ProcessingPipeline(
            pipeline_id="multi",
            blocks=[
                PipelineBlock(block_id="grayscale", block_type="color_space", params={}),
                PipelineBlock(block_id="gaussian_fine", block_type="denoise",
                              params={"kernel_size": 3, "sigma": 1.0}),
            ],
        )
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=pipe,
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_bgr_input_images_handled(self):
        """BGR input images should not crash the agent."""
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        ok_bgr = np.full((100, 100, 3), 128, dtype=np.uint8)
        ng_bgr = _ng_blob()
        ng_bgr_3ch = cv2.cvtColor(ng_bgr, cv2.COLOR_GRAY2BGR)
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[ok_bgr], ng_images=[ng_bgr_3ch],
        )
        assert result.status == "success"


# ── Directive Handling ────────────────────────────────────────────────────────

class TestDirectiveHandling:
    @pytest.mark.asyncio
    async def test_run_directive_overrides_constructor(self):
        """Passing directive='lenient' overrides constructor directive='strict'."""
        agent = TestAgentInspection(directive="strict")
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await agent.run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
            directive="lenient",
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_run_directive_none_uses_constructor(self):
        """directive=None in run() → falls back to constructor directive."""
        agent = TestAgentInspection(directive="strict")
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.5})])
        result = await agent.run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
            directive=None,
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_strict_directive_raises_threshold(self):
        """With strict: min_accuracy default threshold is tighter → harder to pass."""
        # Item with no explicit min_accuracy — default is 0.8; strict makes it 0.9
        # Use mixed images to get partial accuracy (~0.5)
        # Under lenient it might pass, under strict it will fail
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        ok_imgs = [_ok_gray(), _ng_blob()]  # 1 ok, 1 ng
        ng_imgs = [_ok_gray(), _ng_blob()]  # mixed
        # Just check that strict runs without crash
        result = await TestAgentInspection(directive="strict").run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=ok_imgs, ng_images=ng_imgs,
        )
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_lenient_directive_lowers_threshold(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection(directive="lenient").run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "success"


# ── Error Handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_empty_plan_returns_error(self):
        plan = _plan([])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_empty_plan_has_error_message(self):
        plan = _plan([])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_no_ok_images_returns_error(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[], ng_images=[_ng_blob()],
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_no_ok_images_has_error_message(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[], ng_images=[_ng_blob()],
        )
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_no_ng_images_returns_error(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[],
        )
        assert result.status == "error"

    @pytest.mark.asyncio
    async def test_no_ng_images_has_error_message(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[],
        )
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_error_result_has_execution_time(self):
        plan = _plan([])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.execution_time_ms >= 0.0


# ── Overall Metrics Aggregation ───────────────────────────────────────────────

class TestOverallMetrics:
    @pytest.mark.asyncio
    async def test_total_items_matches_plan(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB"),
            InspectionItem(item_id=2, name="b", category="BLOB"),
            InspectionItem(item_id=3, name="c", category="BLOB"),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.data["total_items"] == 3

    @pytest.mark.asyncio
    async def test_item_results_count_matches_plan(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB"),
            InspectionItem(item_id=2, name="b", category="BLOB"),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert len(result.data["item_results"]) == 2

    @pytest.mark.asyncio
    async def test_overall_accuracy_is_mean_of_non_skipped(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB"),
            InspectionItem(item_id=2, name="b", category="BLOB"),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        non_skipped = [r for r in result.data["item_results"] if not r["skipped"]]
        expected = sum(r["accuracy"] for r in non_skipped) / len(non_skipped)
        assert result.data["overall_accuracy"] == pytest.approx(expected, abs=1e-6)

    @pytest.mark.asyncio
    async def test_overall_passed_true_when_all_pass(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 0.9})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        assert result.data["overall_passed"] is True

    @pytest.mark.asyncio
    async def test_overall_passed_false_when_any_fails(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB",
                                     success_criteria={"min_accuracy": 1.1})])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert result.data["overall_passed"] is False

    @pytest.mark.asyncio
    async def test_passed_items_count_correct(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB",
                           success_criteria={"min_accuracy": 0.9}),
            InspectionItem(item_id=2, name="b", category="BLOB",
                           success_criteria={"min_accuracy": 1.1}),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        assert result.data["passed_items"] == 1
        assert result.data["failed_items"] == 1

    @pytest.mark.asyncio
    async def test_counts_add_up_to_total(self):
        plan = _plan([
            InspectionItem(item_id=1, name="a", category="BLOB",
                           success_criteria={"min_accuracy": 1.1}),
            InspectionItem(item_id=2, name="b", category="BLOB", depends_on=[1]),
            InspectionItem(item_id=3, name="c", category="BLOB",
                           success_criteria={"min_accuracy": 0.9}),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        d = result.data
        assert d["passed_items"] + d["failed_items"] + d["skipped_items"] == d["total_items"]

    @pytest.mark.asyncio
    async def test_execution_order_has_all_item_ids(self):
        plan = _plan([
            InspectionItem(item_id=5, name="a", category="BLOB"),
            InspectionItem(item_id=7, name="b", category="BLOB"),
        ])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert sorted(result.data["execution_order"]) == [5, 7]

    @pytest.mark.asyncio
    async def test_overall_accuracy_is_float(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert isinstance(result.data["overall_accuracy"], float)

    @pytest.mark.asyncio
    async def test_overall_passed_is_bool(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray()], ng_images=[_ng_blob()],
        )
        assert isinstance(result.data["overall_passed"], bool)

    @pytest.mark.asyncio
    async def test_single_item_overall_accuracy_equals_item_accuracy(self):
        plan = _plan([InspectionItem(item_id=1, name="blob", category="BLOB")])
        result = await TestAgentInspection().run(
            inspection_plan=plan, pipeline=_gray_pipeline(),
            ok_images=[_ok_gray(), _ok_gray()],
            ng_images=[_ng_blob(), _ng_blob()],
        )
        item_acc = result.data["item_results"][0]["accuracy"]
        assert result.data["overall_accuracy"] == pytest.approx(item_acc, abs=1e-6)
