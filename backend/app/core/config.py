"""Centralized configuration loaded from environment variables.

Uses pydantic-settings v2 so values are validated and typed at import time.
The DSN is derived lazily from the discrete POSTGRES_* variables so deployment
secrets can be rotated without changing application code.
"""
from __future__ import annotations

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Project ---
    PROJECT_NAME: str = "PlotLine"
    API_V1_STR: str = "/api/v1"

    # --- CORS ---
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Database ---
    POSTGRES_USER: str = "plotline_admin"
    POSTGRES_PASSWORD: str = "secure_dev_pass_2026"
    POSTGRES_DB: str = "plotline_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(  # type: ignore[return-value]
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


settings = Settings()
