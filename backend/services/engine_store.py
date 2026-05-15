import threading

from backend.models.engine import EngineSettings

_lock = threading.Lock()
_settings = EngineSettings()


def get_settings() -> EngineSettings:
    with _lock:
        return _settings


def update_settings(settings: EngineSettings) -> EngineSettings:
    global _settings
    with _lock:
        _settings = settings
        return _settings
