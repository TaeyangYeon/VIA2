import json
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import structlog

_buffer: deque = deque(maxlen=1000)
_lock = threading.Lock()
_log_file_path: Path = Path("logs/via2.log")


def configure_log_file(path) -> None:
    global _log_file_path
    _log_file_path = Path(path)


def _write_to_file(entry: dict) -> None:
    try:
        _log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _add_timestamp(logger, method, event_dict):
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return event_dict


def _process_to_entry(logger, method, event_dict):
    entry = {
        "timestamp": event_dict.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "agent_name": event_dict.get("agent_name", "unknown"),
        "level": method,
        "message": event_dict.get("event", ""),
        "extra": {
            k: v
            for k, v in event_dict.items()
            if k not in ("timestamp", "agent_name", "event")
        },
    }
    with _lock:
        _buffer.append(entry)
    _write_to_file(entry)
    raise structlog.DropEvent()


structlog.configure(
    processors=[
        _add_timestamp,
        _process_to_entry,
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)


def get_agent_logger(agent_name: str):
    return structlog.get_logger().bind(agent_name=agent_name)


def get_logs(
    agent_name: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
) -> list:
    with _lock:
        logs = list(_buffer)
    if agent_name:
        logs = [e for e in logs if e["agent_name"] == agent_name]
    if level:
        logs = [e for e in logs if e["level"] == level.lower()]
    return logs[-limit:] if len(logs) > limit else logs


def get_agent_names() -> list:
    with _lock:
        names = list({e["agent_name"] for e in _buffer})
    return names


def clear_logs() -> None:
    with _lock:
        _buffer.clear()
    if _log_file_path.exists():
        _log_file_path.write_text("")
