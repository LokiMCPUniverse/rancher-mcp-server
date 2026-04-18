"""Asynchronous Rancher Manager REST API client."""

from __future__ import annotations

from typing import Any

import httpx

from .config import RancherConfig
from .exceptions import APIError, AuthenticationError, NotFoundError


class RancherClient:
    """Thin async wrapper around the Rancher Manager v3 REST API.

    Uses bearer-token authentication with the Rancher API key (format
    ``token-xxx:yyy...``). In addition to the ``/v3`` management plane the
    client exposes helpers for the Kubernetes API that Rancher proxies via
    ``/k8s/clusters/{cluster_id}/...``.
    """

    def __init__(
        self,
        config: RancherConfig,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self._owns_client = http_client is None
        if http_client is None:
            headers: dict[str, str] = {"Accept": "application/json"}
            if config.api_token:
                headers["Authorization"] = f"Bearer {config.api_token}"
            http_client = httpx.AsyncClient(
                base_url=config.normalized_base_url,
                headers=headers,
                timeout=config.timeout,
                verify=config.verify_ssl,
            )
        self._client = http_client

    async def aclose(self) -> None:
        """Close the underlying httpx client if this instance owns it."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> RancherClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    # ---------------------------------------------------------- url helpers
    @staticmethod
    def k8s_path(cluster_id: str, path: str) -> str:
        """Build a Kubernetes-proxied URL path for the given cluster.

        ``path`` may start with or without a leading ``/``.
        """
        suffix = path if path.startswith("/") else f"/{path}"
        return f"/k8s/clusters/{cluster_id}{suffix}"

    # ---------------------------------------------------------- http helpers
    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        if response.status_code in (401, 403):
            raise AuthenticationError(
                f"Rancher authentication failed ({response.status_code}) for {response.request.url}"
            )
        if response.status_code == 404:
            raise NotFoundError(f"Rancher resource not found: {response.request.url}")
        raise APIError(
            f"Rancher API error {response.status_code} for {response.request.url}: "
            f"{response.text[:500]}",
            status_code=response.status_code,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        response = await self._client.request(
            method,
            path,
            params=params,
            json=json,
            headers=headers,
        )
        self._raise_for_status(response)
        return response

    async def _get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        return await self._request("GET", path, params=params)

    async def _post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> httpx.Response:
        return await self._request("POST", path, params=params, json=json)

    async def _patch(
        self,
        path: str,
        *,
        json: Any | None = None,
        content_type: str = "application/strategic-merge-patch+json",
    ) -> httpx.Response:
        # httpx's request helper handles arbitrary methods and content types.
        headers = {"Content-Type": content_type}
        return await self._request("PATCH", path, json=json, headers=headers)

    # --------------------------------------------------------- v3 mgmt API
    async def list_clusters(self) -> list[dict[str, Any]]:
        response = await self._get("/v3/clusters")
        return response.json().get("data", [])

    async def get_cluster(self, cluster_id: str) -> dict[str, Any]:
        response = await self._get(f"/v3/clusters/{cluster_id}")
        return response.json()

    async def list_projects(self, cluster_id: str | None = None) -> list[dict[str, Any]]:
        params = {"clusterId": cluster_id} if cluster_id else None
        response = await self._get("/v3/projects", params=params)
        return response.json().get("data", [])

    async def list_nodes(self, cluster_id: str) -> list[dict[str, Any]]:
        response = await self._get(f"/v3/clusters/{cluster_id}/nodes")
        return response.json().get("data", [])

    async def list_catalog_apps(self, cluster_id: str) -> list[dict[str, Any]]:
        """List applications installed from catalogs for a cluster.

        Uses the v3 apps endpoint filtered by cluster. Rancher 2.5+ stores
        catalog v2 installs as Kubernetes resources, so callers may also
        want to hit the cluster's /v1 apps.catalog.cattle.io endpoint.
        """
        response = await self._get("/v3/apps", params={"clusterId": cluster_id})
        return response.json().get("data", [])

    async def create_kubeconfig(self, cluster_id: str) -> dict[str, Any]:
        """Generate a kubeconfig document for the given cluster."""
        response = await self._post(
            f"/v3/clusters/{cluster_id}",
            params={"action": "generateKubeconfig"},
        )
        return response.json()

    # ---------------------------------------------------- k8s-proxied API
    async def list_namespaces(self, cluster_id: str) -> list[dict[str, Any]]:
        path = self.k8s_path(cluster_id, "/api/v1/namespaces")
        response = await self._get(path)
        return response.json().get("items", [])

    async def list_pods(
        self, cluster_id: str, namespace: str | None = None
    ) -> list[dict[str, Any]]:
        if namespace:
            path = self.k8s_path(cluster_id, f"/api/v1/namespaces/{namespace}/pods")
        else:
            path = self.k8s_path(cluster_id, "/api/v1/pods")
        response = await self._get(path)
        return response.json().get("items", [])

    async def list_deployments(
        self, cluster_id: str, namespace: str | None = None
    ) -> list[dict[str, Any]]:
        if namespace:
            path = self.k8s_path(
                cluster_id, f"/apis/apps/v1/namespaces/{namespace}/deployments"
            )
        else:
            path = self.k8s_path(cluster_id, "/apis/apps/v1/deployments")
        response = await self._get(path)
        return response.json().get("items", [])

    async def get_pod_logs(
        self,
        cluster_id: str,
        namespace: str,
        pod_name: str,
        tail_lines: int = 100,
    ) -> str:
        path = self.k8s_path(
            cluster_id, f"/api/v1/namespaces/{namespace}/pods/{pod_name}/log"
        )
        response = await self._get(path, params={"tailLines": tail_lines})
        return response.text

    async def scale_deployment(
        self,
        cluster_id: str,
        namespace: str,
        name: str,
        replicas: int,
    ) -> dict[str, Any]:
        """Scale a Kubernetes Deployment via the Rancher proxy.

        Issues a strategic-merge patch against the deployment's ``/scale``
        subresource. The patch body matches the ``autoscaling/v1`` Scale
        schema (``spec.replicas``).
        """
        path = self.k8s_path(
            cluster_id,
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{name}/scale",
        )
        body = {"spec": {"replicas": int(replicas)}}
        response = await self._patch(path, json=body)
        return response.json()
