from backend.services.ai_adapter.base import BaseAIAdapter
from backend.services.ai_adapter.ollama_adapter import OllamaAdapter
from backend.services.ai_adapter.remote_adapter import RemoteAdapter
from backend.services.ai_adapter.factory import create_adapter, get_current_adapter

__all__ = [
    "BaseAIAdapter",
    "OllamaAdapter",
    "RemoteAdapter",
    "create_adapter",
    "get_current_adapter",
]
