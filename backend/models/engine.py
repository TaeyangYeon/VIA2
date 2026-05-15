from enum import Enum

from pydantic import BaseModel, model_validator


class EngineMode(str, Enum):
    local = "local"
    remote = "remote"


class EngineSettings(BaseModel):
    mode: EngineMode = EngineMode.local
    local_ollama_url: str = "http://127.0.0.1:11434"
    remote_url: str | None = None
    remote_type: str = "colab"
    remote_auth_token: str | None = None
    model_name: str = "qwen2.5-coder:7b"

    @model_validator(mode="after")
    def remote_url_required_when_remote(self) -> "EngineSettings":
        if self.mode == EngineMode.remote and not self.remote_url:
            raise ValueError("remote_url is required when mode is 'remote'")
        return self
