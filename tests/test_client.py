"""Tests for the asynchronous RancherClient."""

from __future__ import annotations

import json

import httpx
import pytest

from rancher_mcp.client import RancherClient
from rancher_mcp.config import RancherConfig
from rancher_mcp.exceptions import APIError, AuthenticationError, NotFoundError


def _client_with_transport(
    handler,
    *,
    token: str = "token-abcde:xxxyyyzzz",
    base_url: str = "https://rancher.example.com",
) -> RancherClient:
    """Build a RancherClient backed by a MockTransport handler."""
    config = RancherConfig(base_url=base_url, api_token=token)
    transport = httpx.MockTransport(handler)
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    http = httpx.AsyncClient(
        base_url=config.normalized_base_url,
        headers=headers,
        timeout=config.timeout,
        transport=transport,
    )
    return RancherClient(config, http_client=http)


def test_k8s_path_helper() -> None:
    assert (
        RancherClient.k8s_path("c-abcde", "/api/v1/namespaces")
        == "/k8s/clusters/c-abcde/api/v1/namespaces"
    )
    # Works without a leading slash too.
    assert (
        RancherClient.k8s_path("c-abcde", "apis/apps/v1/deployments")
        == "/k8s/clusters/c-abcde/apis/apps/v1/deployments"
    )


@pytest.mark.asyncio
async def test_bearer_header_injected() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("Authorization", "")
        seen["path"] = request.url.path
        return httpx.Response(200, json={"data": []})

    client = _client_with_transport(handler)
    try:
        await client.list_clusters()
    finally:
        await client.aclose()

    assert seen["auth"] == "Bearer token-abcde:xxxyyyzzz"
    assert seen["path"] == "/v3/clusters"


@pytest.mark.asyncio
async def test_list_clusters_happy_path() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v3/clusters"
        return httpx.Response(
            200,
            json={
                "type": "collection",
                "data": [
                    {"id": "c-aaaaa", "name": "prod"},
                    {"id": "c-bbbbb", "name": "stage"},
                ],
            },
        )

    client = _client_with_transport(handler)
    try:
        clusters = await client.list_clusters()
    finally:
        await client.aclose()

    assert [c["id"] for c in clusters] == ["c-aaaaa", "c-bbbbb"]


@pytest.mark.asyncio
async def test_list_projects_uses_cluster_filter() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        return httpx.Response(200, json={"data": []})

    client = _client_with_transport(handler)
    try:
        await client.list_projects("c-abcde")
    finally:
        await client.aclose()

    assert seen["path"] == "/v3/projects"
    assert "clusterId=c-abcde" in seen["query"]


@pytest.mark.asyncio
async def test_list_namespaces_uses_k8s_proxy_path() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"kind": "NamespaceList", "items": [{"metadata": {"name": "default"}}]})

    client = _client_with_transport(handler)
    try:
        items = await client.list_namespaces("c-abcde")
    finally:
        await client.aclose()

    assert seen["path"] == "/k8s/clusters/c-abcde/api/v1/namespaces"
    assert items[0]["metadata"]["name"] == "default"


@pytest.mark.asyncio
async def test_list_pods_namespace_scope() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        return httpx.Response(200, json={"items": []})

    client = _client_with_transport(handler)
    try:
        await client.list_pods("c-abcde", namespace="kube-system")
        await client.list_pods("c-abcde")
    finally:
        await client.aclose()

    assert seen[0] == "/k8s/clusters/c-abcde/api/v1/namespaces/kube-system/pods"
    assert seen[1] == "/k8s/clusters/c-abcde/api/v1/pods"


@pytest.mark.asyncio
async def test_get_pod_logs_returns_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            request.url.path
            == "/k8s/clusters/c-abcde/api/v1/namespaces/app/pods/web-1/log"
        )
        assert request.url.query.decode() == "tailLines=50"
        return httpx.Response(
            200,
            text="line1\nline2\nline3\n",
            headers={"content-type": "text/plain"},
        )

    client = _client_with_transport(handler)
    try:
        logs = await client.get_pod_logs("c-abcde", "app", "web-1", tail_lines=50)
    finally:
        await client.aclose()

    assert logs == "line1\nline2\nline3\n"


@pytest.mark.asyncio
async def test_scale_deployment_patch_body() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["content_type"] = request.headers.get("Content-Type", "")
        captured["body"] = request.content.decode()
        return httpx.Response(
            200,
            json={
                "kind": "Scale",
                "apiVersion": "autoscaling/v1",
                "metadata": {"name": "web"},
                "spec": {"replicas": 3},
            },
        )

    client = _client_with_transport(handler)
    try:
        result = await client.scale_deployment("c-abcde", "app", "web", 3)
    finally:
        await client.aclose()

    assert captured["method"] == "PATCH"
    assert (
        captured["path"]
        == "/k8s/clusters/c-abcde/apis/apps/v1/namespaces/app/deployments/web/scale"
    )
    assert captured["content_type"] == "application/strategic-merge-patch+json"
    assert json.loads(captured["body"]) == {"spec": {"replicas": 3}}
    assert result["spec"]["replicas"] == 3


@pytest.mark.asyncio
async def test_create_kubeconfig_posts_action_param() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["query"] = request.url.query.decode()
        return httpx.Response(200, json={"config": "apiVersion: v1\nkind: Config\n"})

    client = _client_with_transport(handler)
    try:
        result = await client.create_kubeconfig("c-abcde")
    finally:
        await client.aclose()

    assert captured["method"] == "POST"
    assert captured["path"] == "/v3/clusters/c-abcde"
    assert captured["query"] == "action=generateKubeconfig"
    assert "apiVersion" in result["config"]


@pytest.mark.asyncio
async def test_authentication_error_on_401() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "unauthorized"})

    client = _client_with_transport(handler)
    try:
        with pytest.raises(AuthenticationError):
            await client.list_clusters()
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_not_found_error_on_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "not found"})

    client = _client_with_transport(handler)
    try:
        with pytest.raises(NotFoundError):
            await client.get_cluster("c-missing")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_api_error_on_500_carries_status_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = _client_with_transport(handler)
    try:
        with pytest.raises(APIError) as excinfo:
            await client.list_nodes("c-abcde")
    finally:
        await client.aclose()

    assert excinfo.value.status_code == 500
