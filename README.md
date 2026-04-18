# Rancher MCP Server

A Model Context Protocol (MCP) server that exposes the Rancher Manager v2.x
API to LLM clients. Built on the official `mcp` Python SDK (FastMCP) with
async HTTP via `httpx` and settings management via `pydantic-settings`.

## Features

- Bearer-token authentication using a Rancher API key (`token-xxx:yyy...`).
- Cluster, project, and node discovery against the `/v3` management API.
- Kubernetes resource queries (`namespaces`, `pods`, `deployments`, pod logs)
  through Rancher's `/k8s/clusters/{cluster_id}` proxy.
- Deployment scaling via strategic-merge PATCH on the `/scale` subresource.
- Catalog app listing and on-demand kubeconfig generation.

## Requirements

- Python 3.10+
- A Rancher Manager instance reachable over HTTPS.
- An API token generated from the Rancher UI (Account -> API & Keys). The
  token must be passed in the full `token-xxx:yyy...` form.

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Configure the server through environment variables (prefix `RANCHER_`) or a
`.env` file in the working directory:

| Variable               | Description                                     | Default               |
| ---------------------- | ----------------------------------------------- | --------------------- |
| `RANCHER_BASE_URL`     | Rancher Manager base URL (no trailing slash).   | `https://localhost`   |
| `RANCHER_API_TOKEN`    | API token in `token-xxx:yyy...` format.         | *(required)*          |
| `RANCHER_VERIFY_SSL`   | Verify TLS certificates.                        | `true`                |
| `RANCHER_TIMEOUT`      | HTTP timeout in seconds.                        | `60`                  |

## Running

```bash
rancher-mcp
```

The server speaks MCP over stdio and can be wired into any MCP-capable
client (Claude Desktop, Cursor, custom agents, and so on).

## Tools

| Tool                  | Description                                            |
| --------------------- | ------------------------------------------------------ |
| `list_clusters`       | List all managed clusters.                             |
| `get_cluster`         | Fetch one cluster by ID.                               |
| `list_projects`       | List projects, optionally scoped to a cluster.         |
| `list_nodes`          | List nodes in a cluster.                               |
| `list_namespaces`     | List Kubernetes namespaces via the Rancher proxy.      |
| `list_pods`           | List pods (optionally namespace-scoped).               |
| `list_deployments`    | List Deployments (optionally namespace-scoped).        |
| `get_pod_logs`        | Tail pod logs.                                         |
| `scale_deployment`    | Scale a Deployment via the `/scale` subresource.       |
| `list_catalog_apps`   | List catalog apps installed in a cluster.              |
| `create_kubeconfig`   | Generate a kubeconfig for a cluster.                   |

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -x --tb=short
ruff check src tests
```

## License

MIT License - see LICENSE file for details.
