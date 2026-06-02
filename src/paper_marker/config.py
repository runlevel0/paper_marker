from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openai_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="OPENAI_BASE_URL")
    default_openrouter_model: str = Field(
        default="openrouter/auto", alias="PAPER_MARKER_OPENROUTER_MODEL"
    )
    default_timeout_per_route_s: int = Field(default=300, alias="PAPER_MARKER_TIMEOUT_PER_ROUTE")
    max_parallel_routes: int = Field(default=4, alias="PAPER_MARKER_MAX_PARALLEL_ROUTES")
    synth_max_chars_per_candidate: int = Field(
        default=12000, alias="PAPER_MARKER_SYNTH_MAX_CHARS_PER_CANDIDATE"
    )
    synth_max_total_chars: int = Field(default=30000, alias="PAPER_MARKER_SYNTH_MAX_TOTAL_CHARS")

    def resolved_api_key(self) -> str | None:
        return self.openrouter_api_key or self.openai_api_key


def load_settings() -> AppSettings:
    return AppSettings()
