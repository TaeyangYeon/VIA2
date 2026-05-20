"""Tests for InspectionPlanAgent — all adapter calls are mocked, no real LLM invocations."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.inspection_plan_agent import InspectionPlanAgent
from agents.models import AgentResult, AlgorithmCategory, SceneContext, ImageDiagnosis
from agents.base_agent import BaseAgent
from backend.services.ai_adapter.base import BaseAIAdapter
from agents.prompts.inspection_plan_prompt import build_inspection_plan_prompt


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_adapter(response: str) -> BaseAIAdapter:
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(return_value=response)
    return adapter


def _make_scene_context() -> SceneContext:
    diag = ImageDiagnosis(
        contrast=0.7, noise_level=0.2, edge_density=0.5,
        lighting_uniformity=0.8, illumination_type="uniform",
        noise_frequency="low", reflection_level=0.1,
        surface_type="metal", depth_complexity=0.3,
        has_shadow_region=False, blob_feasibility=0.6,
        blob_count_estimate=10, color_discriminability=0.8,
        dominant_channel_ratio=0.9, structural_regularity=0.7,
        pattern_repetition=0.5, optimal_color_space="BGR",
        threshold_candidate=0.5, edge_sharpness=0.8,
    )
    return SceneContext(image_diagnosis=diag, depth_map=None, material_map=None)


def _item(
    item_id=1,
    name="Test Item",
    category="blob",
    depends_on=None,
    safety_role=False,
    success_criteria=None,
) -> dict:
    return {
        "item_id": item_id,
        "name": name,
        "category": category,
        "depends_on": depends_on if depends_on is not None else [],
        "safety_role": safety_role,
        "success_criteria": success_criteria or {"metric": "count", "threshold": 0},
    }


def _items_json(items: list) -> str:
    return json.dumps(items)


def _prompt_arg(adapter) -> str:
    call_kwargs = adapter.generate_text.call_args
    if call_kwargs.args:
        return call_kwargs.args[0]
    return call_kwargs.kwargs.get("prompt", "")


# ── Class instantiation ───────────────────────────────────────────────────────

def test_inspection_plan_agent_is_base_agent():
    agent = InspectionPlanAgent(adapter=_make_adapter("[]"))
    assert isinstance(agent, BaseAgent)


def test_inspection_plan_agent_default_model():
    agent = InspectionPlanAgent(adapter=_make_adapter("[]"))
    assert agent.model == "qwen2.5-coder:7b"


def test_inspection_plan_agent_custom_model():
    agent = InspectionPlanAgent(adapter=_make_adapter("[]"), model="llama3")
    assert agent.model == "llama3"


def test_inspection_plan_agent_name():
    agent = InspectionPlanAgent(adapter=_make_adapter("[]"))
    assert agent.name == "inspection_plan"


def test_inspection_plan_agent_constructor_directive_stored():
    agent = InspectionPlanAgent(adapter=_make_adapter("[]"), directive="strict mode")
    assert agent.directive == "strict mode"


def test_inspection_plan_agent_default_directive_is_empty():
    agent = InspectionPlanAgent(adapter=_make_adapter("[]"))
    assert agent.directive == ""


# ── AgentResult structure on success ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_returns_agent_result_instance():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)
    scene = _make_scene_context()

    result = await agent.run(purpose="scratch inspection", scene_context=scene, algorithm_category=AlgorithmCategory.EDGE_DETECTION)

    assert isinstance(result, AgentResult)


@pytest.mark.asyncio
async def test_run_success_status():
    adapter = _make_adapter(_items_json([_item(1, "Scratch Detection", "edge_detection")]))
    agent = InspectionPlanAgent(adapter=adapter)
    scene = _make_scene_context()

    result = await agent.run(purpose="scratch inspection", scene_context=scene, algorithm_category=AlgorithmCategory.EDGE_DETECTION)

    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_success_has_plan_in_data():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert "plan" in result.data


@pytest.mark.asyncio
async def test_run_success_has_raw_response_in_data():
    raw = _items_json([_item()])
    adapter = _make_adapter(raw)
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert "raw_response" in result.data
    assert isinstance(result.data["raw_response"], str)


@pytest.mark.asyncio
async def test_run_success_execution_time_positive():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_run_success_error_message_is_none():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.error_message is None


# ── InspectionPlan / InspectionItem fields ────────────────────────────────────

@pytest.mark.asyncio
async def test_run_plan_inspection_purpose_matches_arg():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)
    purpose = "scratch inspection"

    result = await agent.run(purpose=purpose, scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.EDGE_DETECTION)

    assert result.data["plan"]["inspection_purpose"] == purpose


@pytest.mark.asyncio
async def test_run_plan_total_items_matches_count():
    items = [_item(1), _item(2, "Item2", "edge_detection"), _item(3, "Item3", "color_filter")]
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    plan = result.data["plan"]
    assert plan["total_items"] == 3
    assert len(plan["items"]) == 3


@pytest.mark.asyncio
async def test_run_plan_item_has_all_required_fields():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    plan_item = result.data["plan"]["items"][0]
    for field_name in ("item_id", "name", "category", "depends_on", "safety_role", "success_criteria"):
        assert field_name in plan_item


@pytest.mark.asyncio
async def test_run_plan_item_id_preserved():
    adapter = _make_adapter(_items_json([_item(42, "Special Item", "blob")]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="special inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.data["plan"]["items"][0]["item_id"] == 42


@pytest.mark.asyncio
async def test_run_plan_item_name_preserved():
    adapter = _make_adapter(_items_json([_item(1, "Hole Detector", "blob")]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="hole inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.data["plan"]["items"][0]["name"] == "Hole Detector"


@pytest.mark.asyncio
async def test_run_plan_item_category_preserved():
    adapter = _make_adapter(_items_json([_item(1, "Blob Check", "blob")]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="blob inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.data["plan"]["items"][0]["category"] == "blob"


@pytest.mark.asyncio
async def test_run_plan_item_safety_role_is_bool():
    adapter = _make_adapter(_items_json([_item(1, "Safety Item", "blob", safety_role=True)]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="safety inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert isinstance(result.data["plan"]["items"][0]["safety_role"], bool)


@pytest.mark.asyncio
async def test_run_plan_item_safety_role_true_preserved():
    adapter = _make_adapter(_items_json([_item(1, "Critical Check", "blob", safety_role=True)]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="critical inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.data["plan"]["items"][0]["safety_role"] is True


@pytest.mark.asyncio
async def test_run_plan_item_safety_role_false_preserved():
    adapter = _make_adapter(_items_json([_item(1, "Normal Check", "blob", safety_role=False)]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="normal inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.data["plan"]["items"][0]["safety_role"] is False


@pytest.mark.asyncio
async def test_run_plan_item_success_criteria_is_dict():
    criteria = {"metric": "count", "threshold": 5}
    adapter = _make_adapter(_items_json([_item(1, "Check", "blob", success_criteria=criteria)]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="inspection", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert isinstance(result.data["plan"]["items"][0]["success_criteria"], dict)


# ── depends_on validation ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_valid_depends_on_preserved():
    items = [_item(1, "Preprocessor", "blob"), _item(2, "Detector", "blob", depends_on=[1])]
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert 1 in result.data["plan"]["items"][1]["depends_on"]


@pytest.mark.asyncio
async def test_run_invalid_depends_on_removed():
    items = [_item(1, "Detector", "blob", depends_on=[999])]  # 999 does not exist
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert 999 not in result.data["plan"]["items"][0]["depends_on"]


@pytest.mark.asyncio
async def test_run_mixed_depends_on_keeps_valid_removes_invalid():
    items = [_item(1, "Item1", "blob"), _item(2, "Item2", "blob", depends_on=[1, 999])]
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    item2_deps = result.data["plan"]["items"][1]["depends_on"]
    assert 1 in item2_deps
    assert 999 not in item2_deps


@pytest.mark.asyncio
async def test_run_invalid_depends_on_does_not_cause_error():
    items = [_item(1, "Detector", "blob", depends_on=[999])]
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "success"


# ── Different purposes produce different parsed results ───────────────────────

@pytest.mark.asyncio
async def test_run_purpose_included_in_prompt():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)
    purpose = "타공 결함 검사"

    await agent.run(purpose=purpose, scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert purpose in _prompt_arg(adapter)


@pytest.mark.asyncio
async def test_run_different_mock_responses_yield_different_results():
    scene = _make_scene_context()
    hole_items = [_item(1, "Hole Detection", "blob")]
    scratch_items = [_item(1, "Scratch Detection", "edge_detection")]

    result_hole = await InspectionPlanAgent(adapter=_make_adapter(_items_json(hole_items))).run(
        purpose="hole inspection", scene_context=scene, algorithm_category=AlgorithmCategory.BLOB
    )
    result_scratch = await InspectionPlanAgent(adapter=_make_adapter(_items_json(scratch_items))).run(
        purpose="scratch inspection", scene_context=scene, algorithm_category=AlgorithmCategory.EDGE_DETECTION
    )

    hole_name = result_hole.data["plan"]["items"][0]["name"]
    scratch_name = result_scratch.data["plan"]["items"][0]["name"]
    assert hole_name != scratch_name


@pytest.mark.asyncio
async def test_run_multiple_items_all_parsed():
    items = [_item(1, "A", "blob"), _item(2, "B", "edge_detection"), _item(3, "C", "color_filter")]
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="multi-step", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.data["plan"]["total_items"] == 3


# ── Error handling ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_empty_purpose_returns_error_status():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_empty_purpose_error_message():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert "Inspection purpose is required" in result.error_message


@pytest.mark.asyncio
async def test_run_empty_purpose_does_not_call_adapter():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    await agent.run(purpose="", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    adapter.generate_text.assert_not_called()


@pytest.mark.asyncio
async def test_run_none_scene_context_returns_error_status():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=None, algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_none_scene_context_error_message():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=None, algorithm_category=AlgorithmCategory.BLOB)

    assert "SceneContext is required" in result.error_message


@pytest.mark.asyncio
async def test_run_none_scene_context_does_not_call_adapter():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    await agent.run(purpose="test", scene_context=None, algorithm_category=AlgorithmCategory.BLOB)

    adapter.generate_text.assert_not_called()


@pytest.mark.asyncio
async def test_run_none_algorithm_category_returns_error_status():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=None)

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_none_algorithm_category_error_message():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=None)

    assert "AlgorithmCategory is required" in result.error_message


@pytest.mark.asyncio
async def test_run_adapter_runtime_error_returns_error_status():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("connection failed"))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_run_adapter_timeout_returns_error_status():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=TimeoutError("timed out"))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_invalid_json_returns_error_status():
    adapter = _make_adapter("this is not JSON {broken")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_invalid_json_error_message():
    adapter = _make_adapter("this is not JSON {broken")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert "Failed to parse inspection plan from LLM response" in result.error_message


@pytest.mark.asyncio
async def test_run_empty_items_list_returns_error_status():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_empty_items_list_error_message():
    adapter = _make_adapter("[]")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert "LLM returned empty inspection plan" in result.error_message


@pytest.mark.asyncio
async def test_run_fenced_empty_list_returns_error():
    adapter = _make_adapter("```json\n[]\n```")
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "error"


# ── Directive handling ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_constructor_directive_appears_in_prompt():
    items = [_item()]
    adapter = _make_adapter(_items_json(items))
    directive = "엄격한 기준 적용"
    agent = InspectionPlanAgent(adapter=adapter, directive=directive)

    await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert directive in _prompt_arg(adapter)


@pytest.mark.asyncio
async def test_run_call_directive_overrides_constructor():
    items = [_item()]
    adapter = _make_adapter(_items_json(items))
    agent = InspectionPlanAgent(adapter=adapter, directive="constructor directive")

    await agent.run(
        purpose="test",
        scene_context=_make_scene_context(),
        algorithm_category=AlgorithmCategory.BLOB,
        directive="call directive",
    )

    assert "call directive" in _prompt_arg(adapter)


@pytest.mark.asyncio
async def test_run_call_directive_none_falls_back_to_constructor():
    items = [_item()]
    adapter = _make_adapter(_items_json(items))
    constructor_directive = "constructor directive"
    agent = InspectionPlanAgent(adapter=adapter, directive=constructor_directive)

    await agent.run(
        purpose="test",
        scene_context=_make_scene_context(),
        algorithm_category=AlgorithmCategory.BLOB,
        directive=None,
    )

    assert constructor_directive in _prompt_arg(adapter)


@pytest.mark.asyncio
async def test_run_no_directive_succeeds():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "success"


# ── AlgorithmCategory in prompt ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_blob_category_in_prompt():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert "blob" in _prompt_arg(adapter).lower()


@pytest.mark.asyncio
async def test_run_edge_detection_category_in_prompt():
    adapter = _make_adapter(_items_json([_item(1, "Edge", "edge_detection")]))
    agent = InspectionPlanAgent(adapter=adapter)

    await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.EDGE_DETECTION)

    prompt = _prompt_arg(adapter).lower()
    assert "edge" in prompt


@pytest.mark.asyncio
async def test_run_adapter_called_once():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert adapter.generate_text.call_count == 1


@pytest.mark.asyncio
async def test_run_adapter_called_with_correct_model():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter, model="custom-model")

    await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    call_kwargs = adapter.generate_text.call_args
    model_arg = call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs.get("model", "")
    assert model_arg == "custom-model"


@pytest.mark.asyncio
async def test_run_adapter_called_with_system_prompt():
    adapter = _make_adapter(_items_json([_item()]))
    agent = InspectionPlanAgent(adapter=adapter)

    await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    system_prompt = adapter.generate_text.call_args.kwargs.get("system_prompt")
    assert system_prompt is not None
    assert len(system_prompt) > 0


# ── JSON parsing robustness ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_parses_markdown_fenced_json():
    items = [_item(1, "Test", "blob")]
    fenced = f"```json\n{json.dumps(items)}\n```"
    adapter = _make_adapter(fenced)
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_parses_backtick_fenced_no_language_tag():
    items = [_item(1, "Test", "blob")]
    fenced = f"```\n{json.dumps(items)}\n```"
    adapter = _make_adapter(fenced)
    agent = InspectionPlanAgent(adapter=adapter)

    result = await agent.run(purpose="test", scene_context=_make_scene_context(), algorithm_category=AlgorithmCategory.BLOB)

    assert result.status == "success"


# ── build_inspection_plan_prompt tests ───────────────────────────────────────

def test_build_prompt_returns_tuple_of_two_strings():
    scene = _make_scene_context()
    result = build_inspection_plan_prompt("test purpose", scene, AlgorithmCategory.BLOB, None)
    assert isinstance(result, tuple)
    assert len(result) == 2
    system_prompt, user_prompt = result
    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)


def test_build_prompt_system_mentions_json():
    scene = _make_scene_context()
    system_prompt, _ = build_inspection_plan_prompt("test", scene, AlgorithmCategory.BLOB, None)
    assert "json" in system_prompt.lower() or "JSON" in system_prompt


def test_build_prompt_system_mentions_item_fields():
    scene = _make_scene_context()
    system_prompt, _ = build_inspection_plan_prompt("test", scene, AlgorithmCategory.BLOB, None)
    assert "item_id" in system_prompt


def test_build_prompt_user_contains_purpose():
    scene = _make_scene_context()
    purpose = "hole detection inspection"
    _, user_prompt = build_inspection_plan_prompt(purpose, scene, AlgorithmCategory.BLOB, None)
    assert purpose in user_prompt


def test_build_prompt_user_contains_algorithm_category():
    scene = _make_scene_context()
    _, user_prompt = build_inspection_plan_prompt("test", scene, AlgorithmCategory.EDGE_DETECTION, None)
    assert "edge_detection" in user_prompt.lower() or "edge" in user_prompt.lower()


def test_build_prompt_with_directive_includes_directive():
    scene = _make_scene_context()
    directive = "strict quality check"
    _, user_prompt = build_inspection_plan_prompt("test", scene, AlgorithmCategory.BLOB, directive)
    assert directive in user_prompt


def test_build_prompt_without_directive_no_none_literal():
    scene = _make_scene_context()
    _, user_prompt = build_inspection_plan_prompt("test", scene, AlgorithmCategory.BLOB, None)
    assert "None" not in user_prompt


def test_build_prompt_user_contains_scene_surface_type():
    scene = _make_scene_context()
    _, user_prompt = build_inspection_plan_prompt("test", scene, AlgorithmCategory.BLOB, None)
    assert "metal" in user_prompt


def test_build_prompt_system_mentions_array_output():
    scene = _make_scene_context()
    system_prompt, _ = build_inspection_plan_prompt("test", scene, AlgorithmCategory.BLOB, None)
    assert "array" in system_prompt.lower() or "[" in system_prompt
