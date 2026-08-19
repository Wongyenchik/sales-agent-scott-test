from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_chat_deployment: str | None = None
    llm_enabled: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    streamlit_origin: str = Field(default="http://localhost:8501")
    outlook_origin: str = Field(default="http://localhost:5173")
    request_timeout_seconds: float = Field(default=30.0, gt=0.0)
    data_dir: Path = Field(default=Path(__file__).parent / "data")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_azure_openai_settings(self) -> Settings:
        """Require Azure OpenAI settings only when LLM use is enabled."""
        if self.llm_enabled:
            missing = [
                name
                for name, value in {
                    "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
                    "AZURE_OPENAI_API_KEY": self.azure_openai_api_key,
                    "AZURE_OPENAI_API_VERSION": self.azure_openai_api_version,
                    "AZURE_OPENAI_CHAT_DEPLOYMENT": self.azure_openai_chat_deployment,
                }.items()
                if not value
            ]
            if missing:
                raise ConfigurationError(
                    "Missing Azure OpenAI settings while LLM_ENABLED=true: " + ", ".join(missing)
                )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
