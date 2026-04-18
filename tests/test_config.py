"""Tests for RancherConfig."""

from __future__ import annotations

import pytest

from rancher_mcp.config import RancherConfig


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("RANCHER_BASE_URL", "RANCHER_API_TOKEN", "RANCHER_VERIFY_SSL", "RANCHER_TIMEOUT"):
        monkeypatch.delenv(var, raising=False)
    cfg = RancherConfig(_env_file=None)
    assert cfg.base_url == "https://localhost"
    assert cfg.api_token == ""
    assert cfg.verify_ssl is True
    assert cfg.timeout == 60.0


def test_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RANCHER_BASE_URL", "https://rancher.example.com/")
    monkeypatch.setenv("RANCHER_API_TOKEN", "token-abcde:xxxyyyzzz")
    monkeypatch.setenv("RANCHER_VERIFY_SSL", "false")
    monkeypatch.setenv("RANCHER_TIMEOUT", "15")
    cfg = RancherConfig(_env_file=None)
    assert cfg.base_url == "https://rancher.example.com/"
    assert cfg.api_token == "token-abcde:xxxyyyzzz"
    assert cfg.verify_ssl is False
    assert cfg.timeout == 15.0


def test_normalized_base_url_strips_trailing_slashes() -> None:
    cfg = RancherConfig(base_url="https://rancher.example.com///")
    assert cfg.normalized_base_url == "https://rancher.example.com"
