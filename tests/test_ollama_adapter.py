import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from backend.services.ai_adapter import BaseAIAdapter, OllamaAdapter


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_mock_client(response_json: dict) -> AsyncMock:
    mock_response = MagicMock()
    mock_response.json.return_value = response_json
    mock_response.raise_for_status = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False
    return mock_client


# ── BaseAIAdapter abstract contract ──────────────────────────────────────────

def test_base_ai_adapter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseAIAdapter()


def test_ollama_adapter_is_a_subclass_of_base():
    adapter = OllamaAdapter()
    assert isinstance(adapter, BaseAIAdapter)


def test_ollama_adapter_implements_all_abstract_methods():
    adapter = OllamaAdapter()
    assert callable(adapter.generate_text)
    assert callable(adapter.generate_json)
    assert callable(adapter.analyze_image)
    assert callable(adapter.health_check)


def test_ollama_adapter_name_property_returns_ollama():
    adapter = OllamaAdapter()
    assert adapter.name == "ollama"


# ── OllamaAdapter configuration ──────────────────────────────────────────────

def test_default_base_url_is_localhost_11434():
    adapter = OllamaAdapter()
    assert adapter.base_url == "http://127.0.0.1:11434"


def test_custom_base_url_is_stored():
    adapter = OllamaAdapter(base_url="http://192.168.1.100:11434")
    assert adapter.base_url == "http://192.168.1.100:11434"


def test_custom_timeout_is_stored():
    adapter = OllamaAdapter(timeout=60.0)
    assert adapter.timeout == 60.0


# ── generate_text ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_text_returns_response_string():
    mock_client = _make_mock_client({"response": "def add(a, b): return a + b"})

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        result = await OllamaAdapter().generate_text("Write an add function", "qwen2.5-coder:7b")

    assert result == "def add(a, b): return a + b"


@pytest.mark.asyncio
async def test_generate_text_payload_contains_model_prompt_and_stream_false():
    mock_client = _make_mock_client({"response": "ok"})

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        await OllamaAdapter().generate_text(
            prompt="test prompt",
            model="qwen2.5-coder:7b",
            system_prompt="You are helpful",
            temperature=0.5,
            max_tokens=1024,
        )

    payload = mock_client.post.call_args.kwargs["json"]
    assert payload["model"] == "qwen2.5-coder:7b"
    assert payload["prompt"] == "test prompt"
    assert payload["stream"] is False


# ── generate_json ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_json_returns_parsed_dict():
    expected = {"status": "ok", "value": 42}
    mock_client = _make_mock_client({"response": json.dumps(expected)})

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        result = await OllamaAdapter().generate_json("Return JSON", "qwen2.5-coder:7b")

    assert result == expected


@pytest.mark.asyncio
async def test_generate_json_raises_value_error_on_invalid_json_response():
    mock_client = _make_mock_client({"response": "this is not json"})

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="Invalid JSON"):
            await OllamaAdapter().generate_json("Return JSON", "qwen2.5-coder:7b")


# ── analyze_image ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_image_returns_description_string():
    mock_client = _make_mock_client({"response": "A red circle on white"})
    image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        result = await OllamaAdapter().analyze_image(image_bytes, "Describe this image", "llava")

    assert result == "A red circle on white"


@pytest.mark.asyncio
async def test_analyze_image_encodes_image_as_base64_in_payload():
    image_bytes = b"fake_image_data"
    expected_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mock_client = _make_mock_client({"response": "description"})

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        await OllamaAdapter().analyze_image(image_bytes, "Describe", "llava")

    payload = mock_client.post.call_args.kwargs["json"]
    assert expected_b64 in payload["images"]


# ── health_check ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_returns_true_when_ollama_responds_200():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        result = await OllamaAdapter().health_check()

    assert result is True


@pytest.mark.asyncio
async def test_health_check_returns_false_on_connection_error():
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        result = await OllamaAdapter().health_check()

    assert result is False


# ── timeout handling ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_text_raises_timeout_error_on_httpx_timeout():
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = False

    with patch("backend.services.ai_adapter.ollama_adapter.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(TimeoutError):
            await OllamaAdapter().generate_text("test", "qwen2.5-coder:7b")


# ── integration (requires real Ollama) ───────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_generate_text_with_qwen_coder():
    """Calls real Ollama with qwen2.5-coder:7b. Skipped if Ollama is not available."""
    adapter = OllamaAdapter()

    try:
        available = await adapter.health_check()
    except Exception:
        available = False

    if not available:
        pytest.skip("Ollama not available at http://127.0.0.1:11434")

    result = await adapter.generate_text(
        prompt="Write a one-line Python function that adds two numbers. Return only the code.",
        model="qwen2.5-coder:7b",
        max_tokens=64,
    )
    assert isinstance(result, str)
    assert len(result.strip()) > 0
