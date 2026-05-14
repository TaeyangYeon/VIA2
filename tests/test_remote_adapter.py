import asyncio
import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from backend.services.ai_adapter import BaseAIAdapter, RemoteAdapter

BASE_URL = "http://example-colab.ngrok.io"
AUTH_TOKEN = "secret-token-123"
_PATCH = "backend.services.ai_adapter.remote_adapter.httpx.AsyncClient"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resp(status: int = 200, body: dict | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = body or {}
    return r


def _client(*side_effects) -> AsyncMock:
    mock = AsyncMock()
    if len(side_effects) == 1:
        mock.post.return_value = side_effects[0]
        mock.get.return_value = side_effects[0]
    else:
        mock.post.side_effect = list(side_effects)
        mock.get.side_effect = list(side_effects)
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = False
    return mock


# ── Class contract ────────────────────────────────────────────────────────────

def test_remote_adapter_is_subclass_of_base():
    adapter = RemoteAdapter(BASE_URL)
    assert isinstance(adapter, BaseAIAdapter)


def test_remote_adapter_implements_all_abstract_methods():
    adapter = RemoteAdapter(BASE_URL)
    assert callable(adapter.generate_text)
    assert callable(adapter.generate_json)
    assert callable(adapter.analyze_image)
    assert callable(adapter.health_check)


def test_name_property_returns_remote():
    assert RemoteAdapter(BASE_URL).name == "remote"


def test_constructor_stores_base_url():
    assert RemoteAdapter(BASE_URL).base_url == BASE_URL


def test_constructor_stores_auth_token():
    assert RemoteAdapter(BASE_URL, auth_token=AUTH_TOKEN).auth_token == AUTH_TOKEN


def test_constructor_stores_timeout():
    assert RemoteAdapter(BASE_URL, timeout=60.0).timeout == 60.0


def test_constructor_defaults_auth_token_to_none():
    assert RemoteAdapter(BASE_URL).auth_token is None


def test_constructor_defaults_timeout_to_300():
    assert RemoteAdapter(BASE_URL).timeout == 300.0


# ── generate_text ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_text_returns_response_string():
    mock = _client(_resp(200, {"response": "hello world"}))
    with patch(_PATCH, return_value=mock):
        result = await RemoteAdapter(BASE_URL).generate_text("Say hello", "gpt-4")
    assert result == "hello world"


@pytest.mark.asyncio
async def test_generate_text_sends_correct_payload():
    mock = _client(_resp(200, {"response": "ok"}))
    with patch(_PATCH, return_value=mock):
        await RemoteAdapter(BASE_URL).generate_text(
            prompt="test prompt",
            model="gpt-4",
            system_prompt="You are helpful",
            temperature=0.5,
            max_tokens=1024,
        )
    payload = mock.post.call_args.kwargs["json"]
    assert payload["prompt"] == "test prompt"
    assert payload["model"] == "gpt-4"
    assert payload["system_prompt"] == "You are helpful"
    assert payload["temperature"] == 0.5
    assert payload["max_tokens"] == 1024


@pytest.mark.asyncio
async def test_generate_text_includes_auth_header_when_token_provided():
    mock = _client(_resp(200, {"response": "ok"}))
    with patch(_PATCH, return_value=mock):
        await RemoteAdapter(BASE_URL, auth_token=AUTH_TOKEN).generate_text("test", "gpt-4")
    headers = mock.post.call_args.kwargs.get("headers", {})
    assert headers.get("Authorization") == f"Bearer {AUTH_TOKEN}"


@pytest.mark.asyncio
async def test_generate_text_no_auth_header_when_no_token():
    mock = _client(_resp(200, {"response": "ok"}))
    with patch(_PATCH, return_value=mock):
        await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
    headers = mock.post.call_args.kwargs.get("headers", {})
    assert "Authorization" not in headers


# ── generate_json ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_json_sends_format_json_in_payload():
    expected = {"status": "ok"}
    mock = _client(_resp(200, {"response": json.dumps(expected)}))
    with patch(_PATCH, return_value=mock):
        await RemoteAdapter(BASE_URL).generate_json("Return JSON", "gpt-4")
    assert mock.post.call_args.kwargs["json"]["format"] == "json"


@pytest.mark.asyncio
async def test_generate_json_returns_parsed_dict():
    expected = {"key": "value", "num": 42}
    mock = _client(_resp(200, {"response": json.dumps(expected)}))
    with patch(_PATCH, return_value=mock):
        result = await RemoteAdapter(BASE_URL).generate_json("Return JSON", "gpt-4")
    assert result == expected


@pytest.mark.asyncio
async def test_generate_json_raises_value_error_on_invalid_json():
    mock = _client(_resp(200, {"response": "this is not json {{"}))
    with patch(_PATCH, return_value=mock):
        with pytest.raises(ValueError):
            await RemoteAdapter(BASE_URL).generate_json("Return JSON", "gpt-4")


# ── analyze_image ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_image_returns_response_string():
    mock = _client(_resp(200, {"response": "A dog sitting"}))
    with patch(_PATCH, return_value=mock):
        result = await RemoteAdapter(BASE_URL).analyze_image(b"image", "Describe", "gpt-4v")
    assert result == "A dog sitting"


@pytest.mark.asyncio
async def test_analyze_image_sends_base64_encoded_image():
    image_data = b"fake image bytes"
    expected_b64 = base64.b64encode(image_data).decode("utf-8")
    mock = _client(_resp(200, {"response": "a cat"}))
    with patch(_PATCH, return_value=mock):
        await RemoteAdapter(BASE_URL).analyze_image(image_data, "Describe this", "gpt-4v")
    payload = mock.post.call_args.kwargs["json"]
    assert expected_b64 in payload["images"]


# ── health_check ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_returns_true_on_200():
    mock = _client(_resp(200))
    with patch(_PATCH, return_value=mock):
        result = await RemoteAdapter(BASE_URL).health_check()
    assert result is True


@pytest.mark.asyncio
async def test_health_check_returns_false_on_non_200():
    mock = _client(_resp(503))
    with patch(_PATCH, return_value=mock):
        result = await RemoteAdapter(BASE_URL).health_check()
    assert result is False


@pytest.mark.asyncio
async def test_health_check_returns_false_on_connect_error():
    mock = AsyncMock()
    mock.get.side_effect = httpx.ConnectError("Connection refused")
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = False
    with patch(_PATCH, return_value=mock):
        result = await RemoteAdapter(BASE_URL).health_check()
    assert result is False


@pytest.mark.asyncio
async def test_health_check_uses_short_timeout():
    mock_instance = AsyncMock()
    mock_instance.get.return_value = _resp(200)
    mock_instance.__aenter__.return_value = mock_instance
    mock_instance.__aexit__.return_value = False
    mock_class = MagicMock(return_value=mock_instance)

    with patch(_PATCH, mock_class):
        await RemoteAdapter(BASE_URL, timeout=300.0).health_check()

    timeout_used = mock_class.call_args.kwargs.get("timeout")
    assert timeout_used == 15.0


# ── Retry logic ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_on_5xx_succeeds_after_two_failures():
    mock = _client(_resp(500), _resp(503), _resp(200, {"response": "success"}))
    with patch(_PATCH, return_value=mock):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
    assert result == "success"
    assert mock.post.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_5xx_raises_runtime_error_after_max_retries():
    mock = _client(_resp(500), _resp(502), _resp(503))
    with patch(_PATCH, return_value=mock):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RuntimeError, match="Remote AI server error"):
                await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
    assert mock.post.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_timeout_raises_timeout_error_after_max_retries():
    mock = AsyncMock()
    mock.post.side_effect = httpx.TimeoutException("Timeout")
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = False
    with patch(_PATCH, return_value=mock):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TimeoutError):
                await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
    assert mock.post.call_count == 3


@pytest.mark.asyncio
async def test_no_retry_on_4xx_raises_runtime_error_immediately():
    mock = _client(_resp(404), _resp(200, {"response": "ok"}))
    with patch(_PATCH, return_value=mock):
        with pytest.raises(RuntimeError, match="Remote AI server error"):
            await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
    assert mock.post.call_count == 1


@pytest.mark.asyncio
async def test_retry_uses_exponential_backoff():
    mock = _client(_resp(500), _resp(500), _resp(200, {"response": "ok"}))
    with patch(_PATCH, return_value=mock):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0].args[0] == 1
    assert mock_sleep.call_args_list[1].args[0] == 2


# ── Error handling ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_connect_error_raises_connection_error_with_url():
    mock = AsyncMock()
    mock.post.side_effect = httpx.ConnectError("refused")
    mock.__aenter__.return_value = mock
    mock.__aexit__.return_value = False
    with patch(_PATCH, return_value=mock):
        with pytest.raises(ConnectionError, match=BASE_URL):
            await RemoteAdapter(BASE_URL).generate_text("test", "gpt-4")
