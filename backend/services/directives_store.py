import threading

from backend.models.directives import AgentDirectives

_lock = threading.Lock()
_directives = AgentDirectives()


def get() -> AgentDirectives:
    with _lock:
        return _directives


def update(directives: AgentDirectives) -> AgentDirectives:
    global _directives
    with _lock:
        _directives = directives
        return _directives


def reset() -> None:
    global _directives
    with _lock:
        _directives = AgentDirectives()
