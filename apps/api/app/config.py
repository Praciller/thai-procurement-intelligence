from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = Field("sqlite:///./thai_procurement_demo.db", alias="DATABASE_URL")
    cors_origins: str = Field("http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS")
    enable_embeddings: bool = Field(False, alias="ENABLE_EMBEDDINGS")
    dataset_mode: Literal["synthetic", "official_snapshot"] = Field("synthetic", alias="DATASET_MODE")
    admin_ingestion_token: str | None = Field(None, alias="ADMIN_INGESTION_TOKEN")
    official_snapshot_metadata: str = Field(
        "../../data/official/metadata/dga-egp-contract-2568-250.json", alias="OFFICIAL_SNAPSHOT_METADATA"
    )
    official_quality_report: str = Field(
        "../../reports/official_snapshot/data_quality_summary.json", alias="OFFICIAL_QUALITY_REPORT"
    )
    enable_llm: bool = Field(False, alias="ENABLE_LLM")
    llm_provider: str | None = Field(None, alias="LLM_PROVIDER")
    llm_provider_chain: str = Field("gemini,groq,openrouter,mock", alias="LLM_PROVIDER_CHAIN")
    llm_timeout_seconds: float = Field(12.0, alias="LLM_TIMEOUT_SECONDS", gt=0, le=60)
    llm_max_retries: int = Field(1, alias="LLM_MAX_RETRIES", ge=0, le=3)
    gemini_model: str = Field("gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_base_url: str = Field(
        "https://generativelanguage.googleapis.com/v1beta", alias="GEMINI_BASE_URL"
    )
    groq_model: str = Field("openai/gpt-oss-20b", alias="GROQ_MODEL")
    groq_base_url: str = Field("https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    cerebras_model: str = Field("gpt-oss-120b", alias="CEREBRAS_MODEL")
    cerebras_base_url: str = Field("https://api.cerebras.ai/v1", alias="CEREBRAS_BASE_URL")
    openrouter_model: str = Field("openrouter/free", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    okmd_model: str = Field("gemini-2.5-flash-lite", alias="OKMD_MODEL")
    okmd_base_url: str = Field("https://gen.ai.kku.ac.th/okmd/api/v1", alias="OKMD_BASE_URL")
    thaillm_model: str = Field(
        "Pathumma-ThaiLLM-qwen3-8b-think-3.0.0", alias="THAILLM_MODEL"
    )
    thaillm_base_url: str = Field("https://thaillm.or.th/api/v1", alias="THAILLM_BASE_URL")
    enable_okmd_fallback: bool = Field(False, alias="ENABLE_OKMD_FALLBACK")
    enable_thaillm_fallback: bool = Field(False, alias="ENABLE_THAILLM_FALLBACK")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
