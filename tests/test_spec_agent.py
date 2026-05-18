"""Tests for SpecAgent — all adapter calls are mocked, no real LLM invocations."""
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.spec_agent import SpecAgent
from agents.models import AgentResult
from backend.services.ai_adapter.base import BaseAIAdapter
from agents.prompts.spec_prompt import build_spec_prompt


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_adapter(response: str) -> BaseAIAdapter:
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(return_value=response)
    return adapter


def _clean_json(data: dict) -> str:
    return json.dumps(data)


def _inspection_payload(goal: str = "스크래치 검사") -> dict:
    return {
        "mode": "inspection",
        "goal": goal,
        "success_criteria": {
            "accuracy": 0.98,
            "fp_rate": 0.02,
            "fn_rate": 0.01,
            "coord_error": None,
        },
        "raw_input": goal,
    }


def _align_payload(goal: str = "part alignment") -> dict:
    return {
        "mode": "align",
        "goal": goal,
        "success_criteria": {
            "accuracy": None,
            "fp_rate": None,
            "fn_rate": None,
            "coord_error": 0.5,
        },
        "raw_input": goal,
    }


# ── SpecAgent instantiation ──────────────────────────────────────────────────

def test_spec_agent_is_a_base_agent():
    from agents.base_agent import BaseAgent
    adapter = _make_adapter("{}")
    agent = SpecAgent(adapter=adapter)
    assert isinstance(agent, BaseAgent)


def test_spec_agent_default_model():
    adapter = _make_adapter("{}")
    agent = SpecAgent(adapter=adapter)
    assert agent.model == "qwen2.5-coder:7b"


def test_spec_agent_custom_model():
    adapter = _make_adapter("{}")
    agent = SpecAgent(adapter=adapter, model="llama3")
    assert agent.model == "llama3"


def test_spec_agent_has_name_spec():
    adapter = _make_adapter("{}")
    agent = SpecAgent(adapter=adapter)
    assert agent.name == "spec"


# ── Korean inspection request ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_korean_inspection_returns_inspection_mode():
    payload = _inspection_payload("스크래치 결함 검사")
    adapter = _make_adapter(_clean_json(payload))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="표면 스크래치 결함 검사해줘")

    assert result.status == "success"
    assert result.data["mode"] == "inspection"


@pytest.mark.asyncio
async def test_run_korean_inspection_goal_is_present():
    payload = _inspection_payload("스크래치 결함 검사")
    adapter = _make_adapter(_clean_json(payload))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="표면 스크래치 결함 검사해줘")

    assert isinstance(result.data["goal"], str)
    assert len(result.data["goal"]) > 0


# ── English align request ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_english_align_returns_align_mode():
    payload = _align_payload("align PCB component to target position")
    adapter = _make_adapter(_clean_json(payload))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="Align the PCB component to the reference mark")

    assert result.status == "success"
    assert result.data["mode"] == "align"


@pytest.mark.asyncio
async def test_run_english_align_has_coord_error():
    payload = _align_payload("align PCB component")
    adapter = _make_adapter(_clean_json(payload))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="Align the PCB component")

    assert "coord_error" in result.data["success_criteria"]


# ── AgentResult fields ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_result_has_raw_input_field():
    user_text = "inspect surface for defects"
    payload = {
        "mode": "inspection",
        "goal": "defect inspection",
        "success_criteria": {"accuracy": None, "fp_rate": None, "fn_rate": None, "coord_error": None},
        "raw_input": user_text,
    }
    adapter = _make_adapter(_clean_json(payload))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text=user_text)

    assert result.data["raw_input"] == user_text


@pytest.mark.asyncio
async def test_run_result_has_success_criteria_dict():
    payload = _inspection_payload()
    adapter = _make_adapter(_clean_json(payload))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="검사")

    sc = result.data["success_criteria"]
    assert isinstance(sc, dict)
    for key in ("accuracy", "fp_rate", "fn_rate", "coord_error"):
        assert key in sc


@pytest.mark.asyncio
async def test_run_result_execution_time_is_positive():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect")

    assert result.execution_time_ms > 0


@pytest.mark.asyncio
async def test_run_success_result_has_no_error_message():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect")

    assert result.error_message is None


# ── JSON parsing robustness ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_parses_markdown_fenced_json():
    payload = _inspection_payload("scratch inspection")
    fenced = f"```json\n{json.dumps(payload)}\n```"
    adapter = _make_adapter(fenced)
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect for scratches")

    assert result.status == "success"
    assert result.data["mode"] == "inspection"


@pytest.mark.asyncio
async def test_run_parses_json_with_leading_trailing_whitespace():
    payload = _align_payload()
    spaced = f"   \n{json.dumps(payload)}\n   "
    adapter = _make_adapter(spaced)
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="align part")

    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_parses_backtick_fenced_without_language_tag():
    payload = _inspection_payload()
    fenced = f"```\n{json.dumps(payload)}\n```"
    adapter = _make_adapter(fenced)
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect")

    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_malformed_json_returns_error_status():
    adapter = _make_adapter("this is not JSON at all {broken}")
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect surface")

    assert result.status == "error"
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_run_empty_response_returns_error_status():
    adapter = _make_adapter("")
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect surface")

    assert result.status == "error"


@pytest.mark.asyncio
async def test_run_whitespace_only_response_returns_error_status():
    adapter = _make_adapter("   \n\t  ")
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect")

    assert result.status == "error"


# ── Error handling: adapter exceptions ───────────────────────────────────────

@pytest.mark.asyncio
async def test_run_adapter_timeout_returns_error_status():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=TimeoutError("adapter timed out"))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect surface")

    assert result.status == "error"
    assert "timeout" in result.error_message.lower()


@pytest.mark.asyncio
async def test_run_adapter_runtime_error_returns_error_status():
    adapter = MagicMock(spec=BaseAIAdapter)
    adapter.generate_text = AsyncMock(side_effect=RuntimeError("connection failed"))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect")

    assert result.status == "error"
    assert result.error_message is not None


# ── Directive injection ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_with_directive_calls_adapter_with_directive_in_prompt():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)
    directive = "정확도 기준을 99% 이상으로 설정하라"

    await agent.run(user_text="inspect surface", directive=directive)

    call_kwargs = adapter.generate_text.call_args
    prompt_arg = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("prompt", "")
    assert directive in prompt_arg


@pytest.mark.asyncio
async def test_run_without_directive_does_not_fail():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)

    result = await agent.run(user_text="inspect surface")

    assert result.status == "success"


@pytest.mark.asyncio
async def test_run_directive_from_constructor_used_when_not_overridden():
    constructor_directive = "생산성 최우선으로 설정"
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter, directive=constructor_directive)

    await agent.run(user_text="inspect surface")

    call_kwargs = adapter.generate_text.call_args
    prompt_arg = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("prompt", "")
    assert constructor_directive in prompt_arg


@pytest.mark.asyncio
async def test_run_call_directive_overrides_constructor_directive():
    constructor_directive = "생산성 최우선"
    call_directive = "품질 최우선"
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter, directive=constructor_directive)

    await agent.run(user_text="inspect surface", directive=call_directive)

    call_kwargs = adapter.generate_text.call_args
    prompt_arg = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("prompt", "")
    assert call_directive in prompt_arg


# ── ROI coordinate inclusion ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_with_roi_includes_roi_in_prompt():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)
    roi = {"x": 100, "y": 200, "width": 300, "height": 400}

    await agent.run(user_text="inspect surface", roi=roi)

    call_kwargs = adapter.generate_text.call_args
    prompt_arg = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("prompt", "")
    assert "100" in prompt_arg
    assert "200" in prompt_arg


@pytest.mark.asyncio
async def test_run_without_roi_does_not_include_roi_section():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)

    await agent.run(user_text="inspect surface")

    call_kwargs = adapter.generate_text.call_args
    prompt_arg = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs.get("prompt", "")
    assert "ROI" not in prompt_arg or "ROI: None" not in prompt_arg


@pytest.mark.asyncio
async def test_run_with_roi_adapter_called_once():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)

    await agent.run(user_text="inspect surface", roi={"x": 0, "y": 0, "width": 640, "height": 480})

    assert adapter.generate_text.call_count == 1


# ── build_spec_prompt utility ─────────────────────────────────────────────────

def test_build_spec_prompt_returns_two_strings():
    system_prompt, user_prompt = build_spec_prompt(user_text="inspect surface")
    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)


def test_build_spec_prompt_system_prompt_mentions_json():
    system_prompt, _ = build_spec_prompt(user_text="inspect surface")
    assert "json" in system_prompt.lower() or "JSON" in system_prompt


def test_build_spec_prompt_user_prompt_contains_user_text():
    user_text = "세라믹 기판 균열 검사"
    _, user_prompt = build_spec_prompt(user_text=user_text)
    assert user_text in user_prompt


def test_build_spec_prompt_with_roi_includes_coordinates():
    roi = {"x": 50, "y": 75, "width": 200, "height": 150}
    _, user_prompt = build_spec_prompt(user_text="inspect", roi=roi)
    assert "50" in user_prompt
    assert "75" in user_prompt


def test_build_spec_prompt_without_roi_no_coordinate_noise():
    _, user_prompt = build_spec_prompt(user_text="inspect")
    assert "width" not in user_prompt.lower() or "ROI" not in user_prompt


def test_build_spec_prompt_with_directive_includes_directive():
    directive = "엄격한 기준 적용"
    _, user_prompt = build_spec_prompt(user_text="inspect", directive=directive)
    assert directive in user_prompt


def test_build_spec_prompt_without_directive_no_empty_section():
    _, user_prompt = build_spec_prompt(user_text="inspect")
    assert "None" not in user_prompt


def test_build_spec_prompt_system_prompt_mentions_mode():
    system_prompt, _ = build_spec_prompt(user_text="inspect")
    assert "inspection" in system_prompt.lower() or "align" in system_prompt.lower()


def test_build_spec_prompt_system_prompt_mentions_success_criteria():
    system_prompt, _ = build_spec_prompt(user_text="inspect")
    assert "success_criteria" in system_prompt or "criteria" in system_prompt.lower()


# ── Adapter is called with correct model ──────────────────────────────────────

@pytest.mark.asyncio
async def test_run_adapter_called_with_correct_model():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter, model="custom-model")

    await agent.run(user_text="inspect")

    call_kwargs = adapter.generate_text.call_args
    model_arg = call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs.get("model", "")
    assert model_arg == "custom-model"


@pytest.mark.asyncio
async def test_run_adapter_called_with_system_prompt():
    adapter = _make_adapter(_clean_json(_inspection_payload()))
    agent = SpecAgent(adapter=adapter)

    await agent.run(user_text="inspect")

    call_kwargs = adapter.generate_text.call_args
    system_prompt = call_kwargs.kwargs.get("system_prompt")
    assert system_prompt is not None
    assert len(system_prompt) > 0
