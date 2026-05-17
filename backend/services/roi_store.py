import threading
from typing import Optional

from backend.models.roi import ROICoordinates

_lock = threading.Lock()
_roi: Optional[ROICoordinates] = None


def get() -> Optional[ROICoordinates]:
    with _lock:
        return _roi


def set(roi: ROICoordinates) -> ROICoordinates:
    global _roi
    with _lock:
        _roi = roi
        return _roi


def clear() -> None:
    global _roi
    with _lock:
        _roi = None
