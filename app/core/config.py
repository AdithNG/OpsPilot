from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OpsPilot"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    environment: str = Field(default="development")
    llm_provider: str = "local"
    openai_model: str = "gpt-4.1-mini"
    embedding_provider: str = "local"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 64
    retrieval_limit: int = 3
    retrieval_candidate_limit: int = 8
    database_url: str = "postgresql://postgres:postgres@db:5432/opspilot"
    storage_backend: str = "memory"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
