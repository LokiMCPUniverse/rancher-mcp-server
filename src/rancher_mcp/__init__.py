"""Rancher MCP Server - Model Context Protocol server for Rancher Manager."""

from __future__ import annotations

from .client import RancherClient
from .config import RancherConfig
from .exceptions import APIError, AuthenticationError, NotFoundError, RancherError
from .server import main, mcp

__version__ = "0.1.0"

__all__ = [
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "RancherClient",
    "RancherConfig",
    "RancherError",
    "main",
    "mcp",
]
