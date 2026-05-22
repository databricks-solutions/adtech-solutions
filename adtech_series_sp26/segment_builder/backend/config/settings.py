"""Environment configuration for the application.

Uses Pydantic BaseSettings to validate env at startup. All Databricks vars
are optional when using profile auth (local) or Databricks Apps SDK auth.
.env is loaded when present (local); in Databricks Apps, env vars come from the platform.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file_path() -> str | None:
    """Use .env only if it exists so the app works in Databricks Apps without a .env file."""
    p = Path(".env")
    return ".env" if p.is_file() else None


class Settings(BaseSettings):
    """Application settings loaded and validated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Databricks SQL Connection (optional when using profile or Apps auth)
    databricks_server_hostname: str = Field(
        default="",
        description="Databricks workspace hostname (e.g. xxx.cloud.databricks.com)",
    )
    databricks_http_path: str = Field(
        default="",
        description="SQL warehouse HTTP path (e.g. /sql/1.0/warehouses/xxx)",
    )
    databricks_token: str = Field(
        default="",
        description="Databricks personal access token for SQL and model serving",
    )

    # Local dev: use a Databricks CLI profile (e.g. ~/.databrickscfg)
    databricks_config_profile: str = Field(
        default="e2-demo-field-eng",
        description="Databricks CLI profile name when not using env vars",
    )

    # Databricks Model Serving (for Agent Mode)
    databricks_model_endpoint: str = Field(
        default="databricks-claude-sonnet-4-5",
        description="Model serving endpoint name for agent LLM",
    )

    # Unity Catalog Tables (defaults; can be overridden via API)
    profiles_table: str = Field(
        default="media_advertising.profiles.megacorp_audience_census_profile",
        description="Unity Catalog table for audience profiles",
    )
    campaigns_table: str = Field(
        default="media_advertising.segments.megacorp_campaigns",
        description="Unity Catalog table for campaign segment lists",
    )
    definitions_table: str = Field(
        default="media_advertising.segments.megacorp_segment_definitions",
        description="Unity Catalog table for segment definitions",
    )

    @property
    def is_databricks_configured(self) -> bool:
        """True if explicit hostname + http_path + token are set (env vars)."""
        return bool(
            self.databricks_server_hostname
            and self.databricks_http_path
            and self.databricks_token
        )

    @property
    def use_profile_auth(self) -> bool:
        """True when not using Apps and not using explicit env; use SDK profile for local dev."""
        return bool(self.databricks_config_profile)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance (validated at first access)."""
    return Settings()
