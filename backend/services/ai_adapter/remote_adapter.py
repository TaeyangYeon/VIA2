import asyncio
import base64
import json

import httpx

from backend.services.ai_adapter.base import BaseAIAdapter

_GENERATE_PATH = "/generate"
_HEALTH_PATH = "/health"
_HEALTH_TIMEOUT = 15.0
_MAX_RETRIES = 2
_BACKOFF = [1, 2]


class RemoteAdapter(BaseAIAdapter):
    def __init__(
        self,
        base_url: str,
        auth_token: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.base_url = base_url
        self.auth_token = auth_token
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "remote"

    def _headers(self) -> dict:
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    async def _post(self, payload: dict) -> dict:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}{_GENERATE_PATH}",
                        json=payload,
                        headers=self._headers(),
                    )
                    if response.status_code >= 500:
                        if attempt < _MAX_RETRIES:
                            await asyncio.sleep(_BACKOFF[attempt])
                            continue
                        raise RuntimeError(
                            f"Remote AI server error: {response.status_code}"
                        )
                    if response.status_code >= 400:
                        raise RuntimeError(
                            f"Remote AI server error: {response.status_code}"
                        )
                    return response.json()
            except httpx.TimeoutException as exc:
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_BACKOFF[attempt])
                    continue
                raise TimeoutError("Remote AI server request timed out") from exc
            except httpx.ConnectError as exc:
                raise ConnectionError(
                    f"Cannot connect to remote AI server: {self.base_url}"
                ) from exc
        raise RuntimeError("Remote AI server error: retry loop exhausted")

    async def generate_text(
        self,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        data = await self._post(
            {
                "prompt": prompt,
                "model": model,
                "system_prompt": system_prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        return data["response"]

    async def generate_json(
        self,
        prompt: str,
        model: str,
        schema: dict | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        data = await self._post(
            {
                "prompt": prompt,
                "model": model,
                "system_prompt": system_prompt,
                "format": "json",
            }
        )
        raw = data["response"]
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON response from remote AI: {raw!r}"
            ) from exc

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: str,
    ) -> str:
        b64 = base64.b64encode(image_data).decode("utf-8")
        data = await self._post(
            {
                "prompt": prompt,
                "model": model,
                "images": [b64],
            }
        )
        return data["response"]

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=_HEALTH_TIMEOUT) as client:
                response = await client.get(
                    f"{self.base_url}{_HEALTH_PATH}",
                    headers=self._headers(),
                )
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False
