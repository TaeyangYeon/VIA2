from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "VIA2"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
