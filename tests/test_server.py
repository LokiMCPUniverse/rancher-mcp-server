"""Tests for the Rancher MCP server wiring."""

from __future__ import annotations

import pytest

from rancher_mcp import server as server_module


def test_mcp_server_registers_expected_tools() -> None:
    names = {t.name for t in server_module.mcp._tool_manager.list_tools()}
    expected = {
        "list_clusters",
        "get_cluster",
        "list_projects",
        "list_nodes",
        "list_namespaces",
        "list_pods",
        "list_deployments",
        "get_pod_logs",
        "scale_deployment",
        "list_catalog_apps",
        "create_kubeconfig",
    }
    missing = expected - names
    assert not missing, f"missing MCP tools: {sorted(missing)}"


def test_fastmcp_server_name() -> None:
    assert server_module.mcp.name == "rancher-mcp-server"


def test_main_is_callable() -> None:
    # Smoke-test the entrypoint without actually starting the transport.
    assert callable(server_module.main)


@pytest.mark.asyncio
async def test_lifespan_builds_and_closes_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from rancher_mcp.config import RancherConfig

    cfg = RancherConfig(base_url="https://rancher.example.com", api_token="token-a:b")
    lifespan = server_module._build_lifespan(cfg)
    async with lifespan(server_module.mcp) as app_ctx:
        assert app_ctx.config is cfg
        assert app_ctx.client.config is cfg
    # After exiting the context, the httpx client should be closed.
    assert app_ctx.client._client.is_closed
