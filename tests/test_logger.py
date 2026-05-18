"""
TDD tests for backend/services/logger.py and backend/routers/logs.py
"""
import pytest
import threading
import time
import json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_log_state(tmp_path):
    """Reset in-memory buffer and redirect log file before each test."""
    from backend.services.logger import clear_logs, configure_log_file
    configure_log_file(tmp_path / "via2.log")
    clear_logs()
    yield
    clear_logs()


@pytest.fixture
def client(tmp_path):
    from backend.main import app
    return TestClient(app)


# ──────────────────────────────────────────────
# 1. Logger factory — get_agent_logger
# ──────────────────────────────────────────────

def test_get_agent_logger_returns_callable():
    from backend.services.logger import get_agent_logger
    logger = get_agent_logger("spec_agent")
    assert callable(logger.info)


def test_get_agent_logger_different_names_are_independent():
    from backend.services.logger import get_agent_logger, get_logs
    logger_a = get_agent_logger("agent_a")
    logger_b = get_agent_logger("agent_b")
    logger_a.info("msg from a")
    logger_b.info("msg from b")
    logs_a = get_logs(agent_name="agent_a")
    logs_b = get_logs(agent_name="agent_b")
    assert len(logs_a) == 1
    assert len(logs_b) == 1
    assert logs_a[0]["agent_name"] == "agent_a"
    assert logs_b[0]["agent_name"] == "agent_b"


# ──────────────────────────────────────────────
# 2. Log entry schema
# ──────────────────────────────────────────────

def test_log_entry_has_required_fields():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("test_agent")
    logger.info("hello world")
    logs = get_logs()
    assert len(logs) == 1
    entry = logs[0]
    assert "timestamp" in entry
    assert "agent_name" in entry
    assert "level" in entry
    assert "message" in entry
    assert "extra" in entry


def test_log_entry_agent_name_matches():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("blueprint_agent")
    logger.info("processing")
    logs = get_logs()
    assert logs[0]["agent_name"] == "blueprint_agent"


def test_log_entry_level_is_lowercase():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("spec_agent")
    logger.warning("watch out")
    logs = get_logs()
    assert logs[0]["level"] == "warning"


def test_log_entry_message_matches():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("spec_agent")
    logger.info("Processing started")
    logs = get_logs()
    assert logs[0]["message"] == "Processing started"


def test_log_entry_extra_dict_stored():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("spec_agent")
    logger.info("Processing started", input_length=150, mode="inspection")
    logs = get_logs()
    entry = logs[0]
    assert entry["extra"]["input_length"] == 150
    assert entry["extra"]["mode"] == "inspection"


def test_log_entry_extra_is_empty_dict_when_no_kwargs():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("spec_agent")
    logger.info("plain message")
    logs = get_logs()
    assert logs[0]["extra"] == {}


def test_log_entry_timestamp_is_iso_string():
    from backend.services.logger import get_agent_logger, get_logs
    from datetime import datetime
    logger = get_agent_logger("spec_agent")
    logger.info("time check")
    logs = get_logs()
    ts = logs[0]["timestamp"]
    # Should parse as ISO datetime without error
    datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ──────────────────────────────────────────────
# 3. Log levels
# ──────────────────────────────────────────────

def test_debug_log_is_recorded():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("debug_agent")
    logger.debug("debug info")
    logs = get_logs()
    assert any(e["level"] == "debug" for e in logs)


def test_info_log_is_recorded():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("info_agent")
    logger.info("info msg")
    logs = get_logs()
    assert any(e["level"] == "info" for e in logs)


def test_warning_log_is_recorded():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("warn_agent")
    logger.warning("warning msg")
    logs = get_logs()
    assert any(e["level"] == "warning" for e in logs)


def test_error_log_is_recorded():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("error_agent")
    logger.error("error msg")
    logs = get_logs()
    assert any(e["level"] == "error" for e in logs)


# ──────────────────────────────────────────────
# 4. Filtering — level
# ──────────────────────────────────────────────

def test_get_logs_filter_by_level_returns_only_matching():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("filter_agent")
    logger.info("info msg")
    logger.error("error msg")
    logger.debug("debug msg")
    info_logs = get_logs(level="info")
    assert all(e["level"] == "info" for e in info_logs)
    assert len(info_logs) == 1


def test_get_logs_filter_by_level_error_excludes_info():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("filter_agent")
    logger.info("info")
    logger.error("error")
    error_logs = get_logs(level="error")
    assert len(error_logs) == 1
    assert error_logs[0]["level"] == "error"


# ──────────────────────────────────────────────
# 5. Filtering — agent_name
# ──────────────────────────────────────────────

def test_get_logs_filter_by_agent_name():
    from backend.services.logger import get_agent_logger, get_logs
    get_agent_logger("agent_x").info("from x")
    get_agent_logger("agent_y").info("from y")
    get_agent_logger("agent_x").error("also from x")
    result = get_logs(agent_name="agent_x")
    assert len(result) == 2
    assert all(e["agent_name"] == "agent_x" for e in result)


# ──────────────────────────────────────────────
# 6. Compound filter
# ──────────────────────────────────────────────

def test_get_logs_compound_filter_agent_and_level():
    from backend.services.logger import get_agent_logger, get_logs
    get_agent_logger("agent_a").info("a info")
    get_agent_logger("agent_a").error("a error")
    get_agent_logger("agent_b").info("b info")
    result = get_logs(agent_name="agent_a", level="info")
    assert len(result) == 1
    assert result[0]["agent_name"] == "agent_a"
    assert result[0]["level"] == "info"


# ──────────────────────────────────────────────
# 7. Limit
# ──────────────────────────────────────────────

def test_get_logs_limit_returns_most_recent():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("limit_agent")
    for i in range(10):
        logger.info(f"msg {i}")
    result = get_logs(limit=3)
    assert len(result) == 3
    # Most recent 3 should be msg 7, 8, 9
    messages = [e["message"] for e in result]
    assert "msg 9" in messages
    assert "msg 8" in messages
    assert "msg 7" in messages


def test_get_logs_limit_default_returns_all_up_to_100():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("limit_agent")
    for i in range(5):
        logger.info(f"msg {i}")
    result = get_logs()
    assert len(result) == 5


def test_get_logs_limit_larger_than_buffer_returns_all():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("limit_agent")
    logger.info("only one")
    result = get_logs(limit=1000)
    assert len(result) == 1


# ──────────────────────────────────────────────
# 8. In-memory buffer max size (1000)
# ──────────────────────────────────────────────

def test_buffer_max_1000_drops_oldest():
    from backend.services.logger import get_agent_logger, get_logs
    logger = get_agent_logger("overflow_agent")
    for i in range(1005):
        logger.info(f"msg {i}")
    all_logs = get_logs(limit=2000)
    assert len(all_logs) == 1000
    # Oldest should be msg 5 (msg 0..4 dropped)
    messages = [e["message"] for e in all_logs]
    assert "msg 0" not in messages
    assert "msg 4" not in messages
    assert "msg 5" in messages
    assert "msg 1004" in messages


# ──────────────────────────────────────────────
# 9. Thread safety
# ──────────────────────────────────────────────

def test_concurrent_logging_does_not_corrupt_buffer():
    from backend.services.logger import get_agent_logger, get_logs
    errors = []

    def log_many(agent_name, count):
        try:
            logger = get_agent_logger(agent_name)
            for i in range(count):
                logger.info(f"concurrent msg {i}")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=log_many, args=(f"agent_{t}", 50)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    logs = get_logs(limit=2000)
    assert len(logs) <= 1000  # buffer max
    assert len(logs) > 0


# ──────────────────────────────────────────────
# 10. clear_logs
# ──────────────────────────────────────────────

def test_clear_logs_empties_buffer():
    from backend.services.logger import get_agent_logger, get_logs, clear_logs
    logger = get_agent_logger("clear_agent")
    logger.info("before clear")
    clear_logs()
    assert get_logs() == []


# ──────────────────────────────────────────────
# 11. File logging
# ──────────────────────────────────────────────

def test_log_file_is_created_on_first_log(tmp_path):
    from backend.services.logger import get_agent_logger, configure_log_file
    log_file = tmp_path / "test_via2.log"
    configure_log_file(log_file)
    logger = get_agent_logger("file_agent")
    logger.info("written to file")
    assert log_file.exists()


def test_log_file_contains_json_lines(tmp_path):
    from backend.services.logger import get_agent_logger, configure_log_file
    log_file = tmp_path / "test_via2.log"
    configure_log_file(log_file)
    logger = get_agent_logger("file_agent")
    logger.info("line one")
    logger.error("line two")
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "timestamp" in parsed
        assert "agent_name" in parsed
        assert "level" in parsed
        assert "message" in parsed


def test_clear_logs_truncates_log_file(tmp_path):
    from backend.services.logger import get_agent_logger, configure_log_file, clear_logs
    log_file = tmp_path / "test_via2.log"
    configure_log_file(log_file)
    logger = get_agent_logger("file_agent")
    logger.info("will be cleared")
    clear_logs()
    assert log_file.exists()
    assert log_file.read_text() == ""


# ──────────────────────────────────────────────
# 12. get_agent_names
# ──────────────────────────────────────────────

def test_get_agent_names_returns_unique_names():
    from backend.services.logger import get_agent_logger, get_agent_names
    get_agent_logger("alpha").info("msg")
    get_agent_logger("beta").info("msg")
    get_agent_logger("alpha").error("msg")
    names = get_agent_names()
    assert set(names) == {"alpha", "beta"}


def test_get_agent_names_empty_when_no_logs():
    from backend.services.logger import get_agent_names
    names = get_agent_names()
    assert names == []


# ──────────────────────────────────────────────
# 13. API — GET /api/logs
# ──────────────────────────────────────────────

def test_api_get_logs_returns_200(client):
    response = client.get("/api/logs")
    assert response.status_code == 200


def test_api_get_logs_empty_initially(client):
    response = client.get("/api/logs")
    data = response.json()
    assert data["logs"] == []
    assert data["total"] == 0


def test_api_get_logs_returns_logged_entries(client):
    from backend.services.logger import get_agent_logger
    get_agent_logger("api_agent").info("api test msg")
    response = client.get("/api/logs")
    data = response.json()
    assert data["total"] >= 1
    assert any(e["message"] == "api test msg" for e in data["logs"])


def test_api_get_logs_filter_by_agent_name(client):
    from backend.services.logger import get_agent_logger
    get_agent_logger("agent_x").info("from x")
    get_agent_logger("agent_y").info("from y")
    response = client.get("/api/logs?agent_name=agent_x")
    data = response.json()
    assert all(e["agent_name"] == "agent_x" for e in data["logs"])


def test_api_get_logs_filter_by_level(client):
    from backend.services.logger import get_agent_logger
    get_agent_logger("level_agent").info("info")
    get_agent_logger("level_agent").error("error")
    response = client.get("/api/logs?level=error")
    data = response.json()
    assert all(e["level"] == "error" for e in data["logs"])


def test_api_get_logs_limit_param(client):
    from backend.services.logger import get_agent_logger
    logger = get_agent_logger("limit_agent")
    for i in range(10):
        logger.info(f"msg {i}")
    response = client.get("/api/logs?limit=3")
    data = response.json()
    assert len(data["logs"]) == 3


# ──────────────────────────────────────────────
# 14. API — GET /api/logs/agents
# ──────────────────────────────────────────────

def test_api_get_logs_agents_returns_200(client):
    response = client.get("/api/logs/agents")
    assert response.status_code == 200


def test_api_get_logs_agents_empty_initially(client):
    response = client.get("/api/logs/agents")
    data = response.json()
    assert data["agents"] == []


def test_api_get_logs_agents_lists_agent_names(client):
    from backend.services.logger import get_agent_logger
    get_agent_logger("alpha_agent").info("msg")
    get_agent_logger("beta_agent").info("msg")
    response = client.get("/api/logs/agents")
    data = response.json()
    assert set(data["agents"]) == {"alpha_agent", "beta_agent"}


# ──────────────────────────────────────────────
# 15. API — DELETE /api/logs
# ──────────────────────────────────────────────

def test_api_delete_logs_returns_200(client):
    response = client.delete("/api/logs")
    assert response.status_code == 200


def test_api_delete_logs_clears_buffer(client):
    from backend.services.logger import get_agent_logger
    get_agent_logger("del_agent").info("to delete")
    client.delete("/api/logs")
    response = client.get("/api/logs")
    data = response.json()
    assert data["logs"] == []
    assert data["total"] == 0


def test_api_delete_logs_response_has_cleared_field(client):
    response = client.delete("/api/logs")
    data = response.json()
    assert data["cleared"] is True
