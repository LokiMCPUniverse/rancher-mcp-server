"""Configuration for the Rancher MCP server."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RancherConfig(BaseSettings):
    """Rancher Manager connection configuration.

    Values are loaded from environment variables using the ``RANCHER_`` prefix.
    ``api_token`` must be a Rancher API key in the ``token-xxx:yyy...`` format
    produced by the Rancher UI (Account -> API & Keys).
    """

    model_config = SettingsConfigDict(
        env_prefix="RANCHER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    base_url: str = Field(
        default="https://localhost",
        description="Base URL of the Rancher Manager (no trailing slash).",
    )
    api_token: str = Field(
        default="",
        description="Rancher API token in the form 'token-xxx:yyy...'.",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify TLS certificates when talking to Rancher.",
    )
    timeout: float = Field(
        default=60.0,
        description="HTTP timeout in seconds for all Rancher API calls.",
    )

    @property
    def normalized_base_url(self) -> str:
        """Return the base URL with trailing slashes stripped."""
        return self.base_url.rstrip("/")
