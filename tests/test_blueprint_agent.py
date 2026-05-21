"""Tests for BlueprintAgent — mock adapters, no real LLM calls."""
import pytest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock

from agents.blueprint_agent import BlueprintAgent
from agents.models import (
    AgentResult,
    Blueprint,
    BlueprintEdge,
    BlueprintNode,
    InspectionItem,
    InspectionPlan,
    PipelineBlock,
    ProcessingPipeline,
)
from agents.base_agent import BaseAgent
from backend.services.ai_adapter.base import BaseAIAdapter
from agents.prompts.blueprint_prompt import build_blueprint_prompt


# ── helpers ────────────────────────────────────────────────────────────────────

KOREAN_DESC = "이 알고리즘은 색상 공간 변환 후 임계값 처리를 통해 불량을 검출합니다."


def _make_adapter(response: str = KOREAN_DESC) -> BaseAIAdapter:
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(return_value=response)
    return adapter


def _make_pipeline(blocks=None) -> ProcessingPipeline:
    if blocks is None:
        blocks = [
            PipelineBlock(block_id="b1", block_type="color_space", params={"mode": "BGR2GRAY"}),
            PipelineBlock(block_id="b2", block_type="threshold", params={"value": 128}),
        ]
    return ProcessingPipeline(pipeline_id="pipe-001", blocks=blocks)


def _make_plan(items=None) -> InspectionPlan:
    if items is None:
        items = [
            InspectionItem(item_id=1, name="Hole Detection", category="blob"),
            InspectionItem(item_id=2, name="Edge Check", category="edge_detection", depends_on=[1]),
        ]
    return InspectionPlan(items=items, inspection_purpose="test inspection")


def _get_node_types(result) -> list:
    return [n["node_type"] for n in result.data["blueprint"]["nodes"]]


# ── Constructor ───────────────────────────────────────────────────────────────

def test_blueprint_agent_is_base_agent():
    agent = BlueprintAgent(adapter=_make_adapter())
    assert isinstance(agent, BaseAgent)


def test_blueprint_agent_default_model():
    agent = BlueprintAgent(adapter=_make_adapter())
    assert agent.model == "qwen2.5-coder:7b"


def test_blueprint_agent_custom_model():
    agent = BlueprintAgent(adapter=_make_adapter(), model="llama3")
    assert agent.model == "llama3"


def test_blueprint_agent_name():
    agent = BlueprintAgent(adapter=_make_adapter())
    assert agent.name == "blueprint"


def test_blueprint_agent_default_directive_empty():
    agent = BlueprintAgent(adapter=_make_adapter())
    assert agent.directive == ""


def test_blueprint_agent_constructor_directive_stored():
    agent = BlueprintAgent(adapter=_make_adapter(), directive="custom directive")
    assert agent.directive == "custom directive"


# ── Input validation ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_pipeline_none_returns_error_status():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=None, inspection_plan=_make_plan())
    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_pipeline_none_error_message():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=None, inspection_plan=_make_plan())
    assert result.error_message == "Pipeline is required"


@pytest.mark.asyncio
async def test_run_inspection_plan_none_returns_error_status():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=None)
    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_inspection_plan_none_error_message():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=None)
    assert result.error_message == "InspectionPlan is required"


@pytest.mark.asyncio
async def test_run_empty_blocks_returns_error_status():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(blocks=[]), inspection_plan=_make_plan())
    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_empty_blocks_error_message():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(blocks=[]), inspection_plan=_make_plan())
    assert result.error_message == "Pipeline has no blocks"


@pytest.mark.asyncio
async def test_run_empty_plan_items_returns_error_status():
    agent = BlueprintAgent(adapter=_make_adapter())
    plan = InspectionPlan(items=[], inspection_purpose="test")
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=plan)
    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_empty_plan_items_error_message():
    agent = BlueprintAgent(adapter=_make_adapter())
    plan = InspectionPlan(items=[], inspection_purpose="test")
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=plan)
    assert result.error_message == "InspectionPlan has no items"


@pytest.mark.asyncio
async def test_run_validation_none_pipeline_does_not_call_adapter():
    adapter = _make_adapter()
    agent = BlueprintAgent(adapter=adapter)
    await agent.run(pipeline=None, inspection_plan=_make_plan())
    adapter.generate_text.assert_not_called()


@pytest.mark.asyncio
async def test_run_validation_none_plan_does_not_call_adapter():
    adapter = _make_adapter()
    agent = BlueprintAgent(adapter=adapter)
    await agent.run(pipeline=_make_pipeline(), inspection_plan=None)
    adapter.generate_text.assert_not_called()


# ── Success path — AgentResult structure ─────────────────────────────────────

@pytest.mark.asyncio
async def test_run_returns_agent_result_instance():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert isinstance(result, AgentResult)


@pytest.mark.asyncio
async def test_run_success_status():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_success_error_message_is_none():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.error_message is None


@pytest.mark.asyncio
async def test_run_success_execution_time_non_negative():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_run_success_data_has_blueprint_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "blueprint" in result.data


@pytest.mark.asyncio
async def test_run_success_data_has_svg_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "svg" in result.data


@pytest.mark.asyncio
async def test_run_success_data_has_description_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "description" in result.data


@pytest.mark.asyncio
async def test_run_success_data_has_node_count_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "node_count" in result.data


@pytest.mark.asyncio
async def test_run_success_data_has_edge_count_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "edge_count" in result.data


# ── Blueprint structure — nodes ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_blueprint_is_dict():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert isinstance(result.data["blueprint"], dict)


@pytest.mark.asyncio
async def test_run_blueprint_has_nodes_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "nodes" in result.data["blueprint"]


@pytest.mark.asyncio
async def test_run_blueprint_has_edges_key():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "edges" in result.data["blueprint"]


@pytest.mark.asyncio
async def test_run_color_space_block_creates_preprocessing_node():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="pre1", block_type="color_space", params={}),
        PipelineBlock(block_id="feat1", block_type="threshold", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())
    assert "preprocessing" in _get_node_types(result)


@pytest.mark.asyncio
async def test_run_denoise_block_creates_preprocessing_node():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="d1", block_type="denoise", params={}),
        PipelineBlock(block_id="f1", block_type="threshold", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())
    assert "preprocessing" in _get_node_types(result)


@pytest.mark.asyncio
async def test_run_threshold_block_creates_feature_node():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="f1", block_type="threshold", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())
    assert "feature" in _get_node_types(result)


@pytest.mark.asyncio
async def test_run_morphology_block_creates_feature_node():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="m1", block_type="morphology", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())
    assert "feature" in _get_node_types(result)


@pytest.mark.asyncio
async def test_run_inspection_items_create_inspection_nodes():
    plan = _make_plan(items=[
        InspectionItem(item_id=1, name="Hole Detection", category="blob"),
        InspectionItem(item_id=2, name="Size Check", category="geometric"),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=plan)
    assert _get_node_types(result).count("inspection") == 2


@pytest.mark.asyncio
async def test_run_decision_node_always_present():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "decision" in _get_node_types(result)


@pytest.mark.asyncio
async def test_run_node_count_matches_data_field():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    actual = len(result.data["blueprint"]["nodes"])
    assert result.data["node_count"] == actual


@pytest.mark.asyncio
async def test_run_edge_count_matches_data_field():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    actual = len(result.data["blueprint"]["edges"])
    assert result.data["edge_count"] == actual


@pytest.mark.asyncio
async def test_run_inspection_node_label_matches_item_name():
    plan = _make_plan(items=[InspectionItem(item_id=1, name="HoleScanner", category="blob")])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=plan)
    insp_nodes = [n for n in result.data["blueprint"]["nodes"] if n["node_type"] == "inspection"]
    assert any("HoleScanner" in n["label"] for n in insp_nodes)


# ── Blueprint structure — edges ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_edges_are_list():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert isinstance(result.data["blueprint"]["edges"], list)


@pytest.mark.asyncio
async def test_run_edges_have_source_id_and_target_id():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    for edge in result.data["blueprint"]["edges"]:
        assert "source_id" in edge
        assert "target_id" in edge


@pytest.mark.asyncio
async def test_run_at_least_one_edge_leads_to_decision():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    decision_nodes = [n for n in result.data["blueprint"]["nodes"] if n["node_type"] == "decision"]
    assert len(decision_nodes) == 1
    decision_id = decision_nodes[0]["node_id"]
    assert any(e["target_id"] == decision_id for e in result.data["blueprint"]["edges"])


@pytest.mark.asyncio
async def test_run_depends_on_creates_inspection_to_inspection_edge():
    plan = InspectionPlan(
        items=[
            InspectionItem(item_id=1, name="Step1", category="blob"),
            InspectionItem(item_id=2, name="Step2", category="blob", depends_on=[1]),
        ],
        inspection_purpose="test",
    )
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=plan)

    nodes = result.data["blueprint"]["nodes"]
    edges = result.data["blueprint"]["edges"]
    node1 = next((n for n in nodes if n["node_type"] == "inspection" and "Step1" in n["label"]), None)
    node2 = next((n for n in nodes if n["node_type"] == "inspection" and "Step2" in n["label"]), None)

    assert node1 is not None and node2 is not None
    assert any(e["source_id"] == node1["node_id"] and e["target_id"] == node2["node_id"] for e in edges)


@pytest.mark.asyncio
async def test_run_preprocessing_connects_to_feature():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="p1", block_type="color_space", params={}),
        PipelineBlock(block_id="f1", block_type="threshold", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())

    nodes = result.data["blueprint"]["nodes"]
    edges = result.data["blueprint"]["edges"]
    pre_node = next((n for n in nodes if n["node_type"] == "preprocessing"), None)
    feat_node = next((n for n in nodes if n["node_type"] == "feature"), None)

    assert pre_node is not None and feat_node is not None
    assert any(e["source_id"] == pre_node["node_id"] and e["target_id"] == feat_node["node_id"] for e in edges)


# ── SVG generation ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_svg_is_string():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert isinstance(result.data["svg"], str)


@pytest.mark.asyncio
async def test_run_svg_starts_with_svg_tag():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.data["svg"].strip().startswith("<svg")


@pytest.mark.asyncio
async def test_run_svg_ends_with_closing_tag():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.data["svg"].strip().endswith("</svg>")


@pytest.mark.asyncio
async def test_run_svg_non_empty():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert len(result.data["svg"]) > 100


@pytest.mark.asyncio
async def test_run_svg_contains_preprocessing_color():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="p1", block_type="color_space", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())
    assert "#4ade80" in result.data["svg"]


@pytest.mark.asyncio
async def test_run_svg_contains_feature_color():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="f1", block_type="threshold", params={}),
    ])
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=pipeline, inspection_plan=_make_plan())
    assert "#60a5fa" in result.data["svg"]


@pytest.mark.asyncio
async def test_run_svg_contains_inspection_color():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "#facc15" in result.data["svg"]


@pytest.mark.asyncio
async def test_run_svg_contains_decision_color():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert "#f87171" in result.data["svg"]


@pytest.mark.asyncio
async def test_run_svg_matches_blueprint_svg_content():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.data["svg"] == result.data["blueprint"]["svg_content"]


# ── Korean description (LLM) ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_description_is_string():
    agent = BlueprintAgent(adapter=_make_adapter(KOREAN_DESC))
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert isinstance(result.data["description"], str)


@pytest.mark.asyncio
async def test_run_description_non_empty():
    agent = BlueprintAgent(adapter=_make_adapter(KOREAN_DESC))
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert len(result.data["description"]) > 0


@pytest.mark.asyncio
async def test_run_description_matches_llm_response():
    agent = BlueprintAgent(adapter=_make_adapter(KOREAN_DESC))
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.data["description"] == KOREAN_DESC


@pytest.mark.asyncio
async def test_run_description_matches_blueprint_algorithm_description():
    agent = BlueprintAgent(adapter=_make_adapter(KOREAN_DESC))
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.data["description"] == result.data["blueprint"]["algorithm_description"]


@pytest.mark.asyncio
async def test_run_adapter_called_once_for_description():
    adapter = _make_adapter(KOREAN_DESC)
    agent = BlueprintAgent(adapter=adapter)
    await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert adapter.generate_text.call_count == 1


# ── LLM graceful degradation ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_llm_failure_returns_success_status():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("LLM connection failed"))
    agent = BlueprintAgent(adapter=adapter)
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_llm_failure_error_message_still_none():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("LLM connection failed"))
    agent = BlueprintAgent(adapter=adapter)
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.error_message is None


@pytest.mark.asyncio
async def test_run_llm_failure_blueprint_still_has_nodes():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("LLM connection failed"))
    agent = BlueprintAgent(adapter=adapter)
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert len(result.data["blueprint"]["nodes"]) > 0


@pytest.mark.asyncio
async def test_run_llm_failure_svg_still_valid():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("LLM connection failed"))
    agent = BlueprintAgent(adapter=adapter)
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.data["svg"].strip().startswith("<svg")


@pytest.mark.asyncio
async def test_run_llm_failure_description_is_fallback_korean_string():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("LLM connection failed"))
    agent = BlueprintAgent(adapter=adapter)
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert isinstance(result.data["description"], str)
    assert len(result.data["description"]) > 0


# ── Directive handling ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_constructor_directive_appears_in_prompt():
    adapter = _make_adapter(KOREAN_DESC)
    agent = BlueprintAgent(adapter=adapter, directive="focus on defects")
    await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    call_args = adapter.generate_text.call_args
    prompt_text = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt", "")
    assert "focus on defects" in prompt_text


@pytest.mark.asyncio
async def test_run_call_directive_overrides_constructor():
    adapter = _make_adapter(KOREAN_DESC)
    agent = BlueprintAgent(adapter=adapter, directive="constructor directive")
    await agent.run(
        pipeline=_make_pipeline(),
        inspection_plan=_make_plan(),
        directive="call directive",
    )
    call_args = adapter.generate_text.call_args
    prompt_text = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt", "")
    assert "call directive" in prompt_text


@pytest.mark.asyncio
async def test_run_directive_none_falls_back_to_constructor():
    adapter = _make_adapter(KOREAN_DESC)
    agent = BlueprintAgent(adapter=adapter, directive="constructor directive")
    await agent.run(
        pipeline=_make_pipeline(),
        inspection_plan=_make_plan(),
        directive=None,
    )
    call_args = adapter.generate_text.call_args
    prompt_text = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt", "")
    assert "constructor directive" in prompt_text


@pytest.mark.asyncio
async def test_run_no_directive_succeeds():
    agent = BlueprintAgent(adapter=_make_adapter())
    result = await agent.run(pipeline=_make_pipeline(), inspection_plan=_make_plan())
    assert result.status == "success"


# ── Prompt builder ────────────────────────────────────────────────────────────

def test_build_blueprint_prompt_returns_tuple_of_two_strings():
    result = build_blueprint_prompt(_make_pipeline(), _make_plan())
    assert isinstance(result, tuple)
    assert len(result) == 2
    system_prompt, user_prompt = result
    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)


def test_build_blueprint_prompt_system_prompt_non_empty():
    system_prompt, _ = build_blueprint_prompt(_make_pipeline(), _make_plan())
    assert len(system_prompt) > 20


def test_build_blueprint_prompt_system_mentions_korean():
    system_prompt, _ = build_blueprint_prompt(_make_pipeline(), _make_plan())
    assert "한국어" in system_prompt or "korean" in system_prompt.lower()


def test_build_blueprint_prompt_user_contains_block_type():
    pipeline = _make_pipeline(blocks=[
        PipelineBlock(block_id="b1", block_type="threshold", params={}),
    ])
    _, user_prompt = build_blueprint_prompt(pipeline, _make_plan())
    assert "threshold" in user_prompt.lower()


def test_build_blueprint_prompt_user_contains_inspection_item_name():
    plan = _make_plan(items=[InspectionItem(item_id=1, name="HoleScan", category="blob")])
    _, user_prompt = build_blueprint_prompt(_make_pipeline(), plan)
    assert "HoleScan" in user_prompt


def test_build_blueprint_prompt_with_directive_includes_directive():
    _, user_prompt = build_blueprint_prompt(_make_pipeline(), _make_plan(), directive="strict check")
    assert "strict check" in user_prompt


def test_build_blueprint_prompt_without_directive_no_none_literal():
    _, user_prompt = build_blueprint_prompt(_make_pipeline(), _make_plan(), directive=None)
    assert "None" not in user_prompt
