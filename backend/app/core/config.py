"""
core/config.py
--------------
Central application configuration loaded from environment variables.
All settings are type-validated by Pydantic. Never import raw os.environ
elsewhere in the codebase — always import `settings` from here.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    """Application settings driven by environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=(_BASE_DIR / ".env", _BASE_DIR / "backend" / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_name: str = "QueryMind"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    database_url: str = "postgresql://querymind_user:querymind_pass@localhost:5432/querymind_db"
    database_readonly_url: str = "postgresql://querymind_readonly:readonly_pass@localhost:5432/querymind_db"

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------ #
    # LLM
    # ------------------------------------------------------------------ #
    llm_provider: str = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:14b"
    ollama_timeout: int = 120

    # OpenAI (future)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Gemini (future)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    # ------------------------------------------------------------------ #
    # SQL Execution
    # ------------------------------------------------------------------ #
    max_sql_retries: int = 3
    sql_query_timeout: int = 30

    # ------------------------------------------------------------------ #
    # Logging
    # ------------------------------------------------------------------ #
    log_level: str = "INFO"

    # ------------------------------------------------------------------ #
    # Derived helpers
    # ------------------------------------------------------------------ #
    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()


# Convenience alias used throughout the application
settings: Settings = get_settings()
