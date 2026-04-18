"""Exception hierarchy for the Rancher MCP server."""

from __future__ import annotations


class RancherError(Exception):
    """Base error raised by the Rancher MCP server."""


class AuthenticationError(RancherError):
    """Raised when Rancher rejects the supplied credentials (HTTP 401/403)."""


class NotFoundError(RancherError):
    """Raised when a requested Rancher resource does not exist (HTTP 404)."""


class APIError(RancherError):
    """Raised for any other non-success response from the Rancher API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
