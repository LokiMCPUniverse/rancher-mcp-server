"""MCP server implementation for the Rancher Manager API using FastMCP."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .client import RancherClient
from .config import RancherConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application-level context shared with every tool call."""

    client: RancherClient
    config: RancherConfig


def _build_lifespan(config: RancherConfig | None = None):
    """Create a lifespan manager bound to the given (or default) config."""

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
        cfg = config or RancherConfig()
        client = RancherClient(cfg)
        try:
            yield AppContext(client=client, config=cfg)
        finally:
            await client.aclose()

    return lifespan


# Module-level FastMCP instance - tools are registered against this.
mcp: FastMCP = FastMCP("rancher-mcp-server", lifespan=_build_lifespan())


def _get_client(ctx: Context) -> RancherClient:
    """Fetch the shared :class:`RancherClient` from the lifespan context."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    return app_ctx.client


def _format(payload: Any) -> str:
    """Serialize a response payload as pretty JSON text."""
    return json.dumps(payload, indent=2, default=str)


# --------------------------------------------------------------------- tools
@mcp.tool()
async def list_clusters(ctx: Context | None = None) -> str:
    """List all clusters managed by this Rancher server."""
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_clusters())
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_clusters: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def get_cluster(cluster_id: str, ctx: Context | None = None) -> str:
    """Get detailed information about a specific Rancher cluster.

    Args:
        cluster_id: Rancher-assigned cluster identifier (e.g. ``c-abcde``).
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.get_cluster(cluster_id))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling get_cluster: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def list_projects(
    cluster_id: str | None = None, ctx: Context | None = None
) -> str:
    """List Rancher projects, optionally filtered by cluster.

    Args:
        cluster_id: Optional cluster ID used to scope the result.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_projects(cluster_id))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_projects: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def list_nodes(cluster_id: str, ctx: Context | None = None) -> str:
    """List nodes belonging to a Rancher-managed cluster.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_nodes(cluster_id))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_nodes: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def list_namespaces(cluster_id: str, ctx: Context | None = None) -> str:
    """List namespaces in the Kubernetes cluster via the Rancher proxy.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_namespaces(cluster_id))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_namespaces: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def list_pods(
    cluster_id: str,
    namespace: str | None = None,
    ctx: Context | None = None,
) -> str:
    """List pods in a cluster, optionally scoped to a namespace.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
        namespace: Optional namespace to filter pods.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_pods(cluster_id, namespace))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_pods: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def list_deployments(
    cluster_id: str,
    namespace: str | None = None,
    ctx: Context | None = None,
) -> str:
    """List Deployments in a cluster, optionally scoped to a namespace.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
        namespace: Optional namespace to filter deployments.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_deployments(cluster_id, namespace))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_deployments: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def get_pod_logs(
    cluster_id: str,
    namespace: str,
    pod_name: str,
    tail_lines: int = 100,
    ctx: Context | None = None,
) -> str:
    """Fetch logs from a pod via the Rancher Kubernetes proxy.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
        namespace: Namespace the pod lives in.
        pod_name: Name of the pod whose logs should be returned.
        tail_lines: Number of trailing lines to return (default 100).
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return await client.get_pod_logs(cluster_id, namespace, pod_name, tail_lines)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling get_pod_logs: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def scale_deployment(
    cluster_id: str,
    namespace: str,
    name: str,
    replicas: int,
    ctx: Context | None = None,
) -> str:
    """Scale a Kubernetes Deployment to the given replica count.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
        namespace: Namespace containing the deployment.
        name: Deployment name.
        replicas: Desired replica count.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        result = await client.scale_deployment(cluster_id, namespace, name, replicas)
        return _format(result)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling scale_deployment: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def list_catalog_apps(cluster_id: str, ctx: Context | None = None) -> str:
    """List catalog applications installed in a Rancher cluster.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.list_catalog_apps(cluster_id))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling list_catalog_apps: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def create_kubeconfig(cluster_id: str, ctx: Context | None = None) -> str:
    """Generate a kubeconfig document for the given cluster.

    Args:
        cluster_id: Rancher-assigned cluster identifier.
    """
    assert ctx is not None
    client = _get_client(ctx)
    try:
        return _format(await client.create_kubeconfig(cluster_id))
    except Exception as exc:  # noqa: BLE001
        logger.error("Error calling create_kubeconfig: %s", exc)
        return f"Error: {exc}"


def main() -> None:
    """Main entry point for the MCP server (stdio transport)."""
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        logger.error("Server error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
