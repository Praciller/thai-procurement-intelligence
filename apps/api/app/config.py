from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field("sqlite:///./thai_procurement_demo.db", alias="DATABASE_URL")
    cors_origins: str = Field("http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS")
    llm_provider: Literal["mock", "gemini", "openrouter"] = Field("mock", alias="LLM_PROVIDER")
    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")
    openrouter_api_key: str | None = Field(None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field("mistralai/mistral-small-3.2-24b-instruct:free", alias="OPENROUTER_MODEL")
    enable_llm: bool = Field(False, alias="ENABLE_LLM")
    enable_embeddings: bool = Field(False, alias="ENABLE_EMBEDDINGS")
    ai_rate_limit_per_hour: int = Field(20, alias="AI_RATE_LIMIT_PER_HOUR")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

