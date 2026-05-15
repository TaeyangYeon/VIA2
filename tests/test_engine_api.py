import pytest
import httpx
from backend.main import app
from backend.models.engine import EngineSettings, EngineMode
from backend.services import engine_store
from backend.services.ai_adapter.factory import create_adapter, get_current_adapter
from backend.services.ai_adapter.ollama_adapter import OllamaAdapter
from backend.services.ai_adapter.remote_adapter import RemoteAdapter


@pytest.fixture(autouse=True)
def reset_engine_store():
    engine_store.update_settings(EngineSettings())
    yield
    engine_store.update_settings(EngineSettings())


@pytest.mark.asyncio
async def test_get_engine_returns_default_settings():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/engine")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "local"
    assert data["local_ollama_url"] == "http://127.0.0.1:11434"


@pytest.mark.asyncio
async def test_post_engine_local_mode_succeeds():
    payload = {"mode": "local", "model_name": "qwen2.5-coder:7b"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/engine", json=payload)
    assert response.status_code == 200
    assert response.json()["mode"] == "local"


@pytest.mark.asyncio
async def test_post_engine_remote_mode_with_url_succeeds():
    payload = {
        "mode": "remote",
        "remote_url": "https://colab.example.com",
        "model_name": "qwen2.5-coder:7b",
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/engine", json=payload)
    assert response.status_code == 200
    assert response.json()["mode"] == "remote"
    assert response.json()["remote_url"] == "https://colab.example.com"


@pytest.mark.asyncio
async def test_post_engine_remote_mode_missing_url_returns_422():
    payload = {"mode": "remote"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/engine", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_engine_updates_persist_to_get():
    payload = {
        "mode": "remote",
        "remote_url": "https://azure.example.com",
        "model_name": "my-model",
        "remote_type": "azure",
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        post_response = await client.post("/api/engine", json=payload)
        assert post_response.status_code == 200
        get_response = await client.get("/api/engine")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["mode"] == "remote"
    assert data["remote_url"] == "https://azure.example.com"
    assert data["model_name"] == "my-model"
    assert data["remote_type"] == "azure"


@pytest.mark.asyncio
async def test_post_engine_invalid_mode_returns_422():
    payload = {"mode": "invalid_mode"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/engine", json=payload)
    assert response.status_code == 422


def test_factory_creates_ollama_adapter_for_local_mode():
    settings = EngineSettings(mode=EngineMode.local)
    adapter = create_adapter(settings)
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.base_url == settings.local_ollama_url


def test_factory_creates_remote_adapter_for_remote_mode():
    settings = EngineSettings(
        mode=EngineMode.remote,
        remote_url="https://colab.example.com",
        remote_auth_token="my-token",
    )
    adapter = create_adapter(settings)
    assert isinstance(adapter, RemoteAdapter)
    assert adapter.base_url == "https://colab.example.com"
    assert adapter.auth_token == "my-token"


def test_get_current_adapter_returns_adapter_matching_current_settings():
    engine_store.update_settings(EngineSettings(mode=EngineMode.local))
    adapter = get_current_adapter()
    assert isinstance(adapter, OllamaAdapter)


def test_engine_settings_model_default_values():
    settings = EngineSettings()
    assert settings.mode == EngineMode.local
    assert settings.local_ollama_url == "http://127.0.0.1:11434"
    assert settings.remote_url is None
    assert settings.remote_type == "colab"
    assert settings.remote_auth_token is None
    assert settings.model_name == "qwen2.5-coder:7b"
