from backend.models.engine import EngineMode, EngineSettings
from backend.services.ai_adapter.base import BaseAIAdapter
from backend.services.ai_adapter.ollama_adapter import OllamaAdapter
from backend.services.ai_adapter.remote_adapter import RemoteAdapter
from backend.services import engine_store


def create_adapter(settings: EngineSettings) -> BaseAIAdapter:
    if settings.mode == EngineMode.local:
        return OllamaAdapter(base_url=settings.local_ollama_url)
    return RemoteAdapter(
        base_url=settings.remote_url,
        auth_token=settings.remote_auth_token,
    )


def get_current_adapter() -> BaseAIAdapter:
    return create_adapter(engine_store.get_settings())
