import subprocess
import pytest
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:7b"
TIMEOUT = 120


def _server_is_running() -> bool:
    try:
        resp = requests.get(OLLAMA_BASE_URL, timeout=5)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def test_ollama_is_running():
    if not _server_is_running():
        pytest.skip("Ollama server not running")
    resp = requests.get(OLLAMA_BASE_URL, timeout=10)
    assert resp.status_code == 200


def test_qwen_coder_model_exists():
    if not _server_is_running():
        pytest.skip("Ollama server not running")
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "qwen2.5-coder" in result.stdout, (
        f"qwen2.5-coder:7b not found in ollama list. Output:\n{result.stdout}"
    )


def test_text_generation():
    if not _server_is_running():
        pytest.skip("Ollama server not running")
    payload = {
        "model": MODEL_NAME,
        "prompt": "Write a one-line Python function that adds two numbers.",
        "stream": False,
    }
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert len(data["response"].strip()) > 0, "Model returned an empty response"


def test_json_output_parsing():
    if not _server_is_running():
        pytest.skip("Ollama server not running")
    import json

    payload = {
        "model": MODEL_NAME,
        "prompt": 'Return a JSON object with keys "status" and "value". status should be "ok" and value should be 42.',
        "stream": False,
        "format": "json",
    }
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    parsed = json.loads(data["response"])
    assert isinstance(parsed, dict), "Response is not a valid JSON object"
    assert len(parsed) > 0, "Parsed JSON object is empty"
