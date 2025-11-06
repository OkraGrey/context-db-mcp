"""Configuration management for the Context DB MCP server."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration for the MCP server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CONTEXT_DB_OPENAI_API_KEY", "OPENAI_API_KEY"),
        description="Primary OpenAI API key used for vector store operations.",
    )
    openai_organization: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "CONTEXT_DB_OPENAI_ORGANIZATION",
            "CONTEXT_DB_OPENAI_ORG",
            "OPENAI_ORGANIZATION",
            "OPENAI_ORG",
        ),
        description="Optional OpenAI organization identifier.",
    )
    openai_project: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CONTEXT_DB_OPENAI_PROJECT", "OPENAI_PROJECT"),
        description="Optional OpenAI project identifier.",
    )
    default_vector_store_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "CONTEXT_DB_VECTOR_STORE_ID",
            "OPENAI_VECTOR_STORE_ID",
            "VECTOR_STORE_ID",
        ),
        description="Vector store ID used when a tool call omits an explicit identifier.",
    )
    default_vector_store_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("CONTEXT_DB_VECTOR_STORE_NAME"),
        description="When provided, a vector store with this name will be created on demand.",
    )
    request_timeout_seconds: float = Field(
        default=120.0,
        validation_alias=AliasChoices("CONTEXT_DB_REQUEST_TIMEOUT_SECONDS"),
        description="Default request timeout for OpenAI API calls.",
    )
    default_max_results: int = Field(
        default=10,
        validation_alias=AliasChoices("CONTEXT_DB_DEFAULT_MAX_RESULTS"),
        description="Fallback maximum number of search results when not provided by the caller.",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("CONTEXT_DB_LOG_LEVEL", "LOG_LEVEL"),
        description="Application log level (e.g. INFO, DEBUG).",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


__all__ = ["Settings", "get_settings"]




