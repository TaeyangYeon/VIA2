import threading

from backend.models.config import InspectionConfig

_lock = threading.Lock()
_config = InspectionConfig()


def get() -> InspectionConfig:
    with _lock:
        return _config


def update(config: InspectionConfig) -> InspectionConfig:
    global _config
    with _lock:
        _config = config
        return _config


def reset() -> None:
    global _config
    with _lock:
        _config = InspectionConfig()
