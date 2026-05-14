import base64
import json

import httpx

from backend.services.ai_adapter.base import BaseAIAdapter

_GENERATE_PATH = "/api/generate"
_TAGS_PATH = "/api/tags"


class OllamaAdapter(BaseAIAdapter):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "ollama"

    async def generate_text(
        self,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt is not None:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{_GENERATE_PATH}", json=payload
                )
                response.raise_for_status()
                return response.json()["response"]
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Ollama request timed out: {exc}") from exc

    async def generate_json(
        self,
        prompt: str,
        model: str,
        schema: dict | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        if system_prompt is not None:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{_GENERATE_PATH}", json=payload
                )
                response.raise_for_status()
                raw = response.json()["response"]
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON response from Ollama: {raw!r}"
                    ) from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Ollama request timed out: {exc}") from exc

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: str,
    ) -> str:
        b64 = base64.b64encode(image_data).decode("utf-8")
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "images": [b64],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{_GENERATE_PATH}", json=payload
                )
                response.raise_for_status()
                return response.json()["response"]
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Ollama request timed out: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}{_TAGS_PATH}")
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
