from abc import ABC, abstractmethod


class BaseAIAdapter(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str: ...

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        model: str,
        schema: dict | None = None,
        system_prompt: str | None = None,
    ) -> dict: ...

    @abstractmethod
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        model: str,
    ) -> str: ...

    @abstractmethod
    async def health_check(self) -> bool: ...
