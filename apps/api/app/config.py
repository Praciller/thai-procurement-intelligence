from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
