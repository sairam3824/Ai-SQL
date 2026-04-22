from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_database_url: str = "sqlite:///./data/app.db"
    app_encryption_key: str | None = None
    app_cors_origins: str = "http://localhost:3000"
    app_storage_dir: str = "./data"
    app_log_level: str = "INFO"

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_summary_model: str = "openai/gpt-4.1-mini"
    openrouter_site_url: str = "http://localhost:3000"
    openrouter_site_name: str = "AI SQL Copilot"

    query_timeout_seconds: int = 20
    query_default_limit: int = 200
    query_max_rows: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]

    @property
    def storage_dir(self) -> Path:
        return Path(self.app_storage_dir).resolve()

    @property
    def uploads_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def demo_dir(self) -> Path:
        return self.storage_dir / "demo"

    @property
    def prompt_dir(self) -> Path:
        return Path(__file__).resolve().parents[1] / "prompts"


@lru_cache
def get_settings() -> Settings:
    return Settings()
