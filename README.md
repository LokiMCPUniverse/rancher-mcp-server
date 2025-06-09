# Rancher MCP Server

<div align="center">

# Rancher Mcp Server

[![GitHub stars](https://img.shields.io/github/stars/LokiMCPUniverse/rancher-mcp-server?style=social)](https://github.com/LokiMCPUniverse/rancher-mcp-server/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/LokiMCPUniverse/rancher-mcp-server?style=social)](https://github.com/LokiMCPUniverse/rancher-mcp-server/network)
[![GitHub watchers](https://img.shields.io/github/watchers/LokiMCPUniverse/rancher-mcp-server?style=social)](https://github.com/LokiMCPUniverse/rancher-mcp-server/watchers)

[![License](https://img.shields.io/github/license/LokiMCPUniverse/rancher-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/rancher-mcp-server/blob/main/LICENSE)
[![Issues](https://img.shields.io/github/issues/LokiMCPUniverse/rancher-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/rancher-mcp-server/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/LokiMCPUniverse/rancher-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/rancher-mcp-server/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/LokiMCPUniverse/rancher-mcp-server?style=for-the-badge)](https://github.com/LokiMCPUniverse/rancher-mcp-server/commits)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-DC143C?style=for-the-badge)](https://modelcontextprotocol.io)

[![Commit Activity](https://img.shields.io/github/commit-activity/m/LokiMCPUniverse/rancher-mcp-server?style=flat-square)](https://github.com/LokiMCPUniverse/rancher-mcp-server/pulse)
[![Code Size](https://img.shields.io/github/languages/code-size/LokiMCPUniverse/rancher-mcp-server?style=flat-square)](https://github.com/LokiMCPUniverse/rancher-mcp-server)
[![Contributors](https://img.shields.io/github/contributors/LokiMCPUniverse/rancher-mcp-server?style=flat-square)](https://github.com/LokiMCPUniverse/rancher-mcp-server/graphs/contributors)

</div>

A Model Context Protocol (MCP) server for integrating Rancher with GenAI applications.

## Overview

Kubernetes management and deployment platform

## Features

- Comprehensive Rancher API coverage
- Multiple authentication methods
- Enterprise-ready with rate limiting
- Full error handling and retry logic
- Async support for better performance

## Installation

```bash
pip install rancher-mcp-server
```

Or install from source:

```bash
git clone https://github.com/asklokesh/rancher-mcp-server.git
cd rancher-mcp-server
pip install -e .
```

## Configuration

Create a `.env` file or set environment variables according to Rancher API requirements.

## Quick Start

```python
from rancher_mcp import RancherMCPServer

# Initialize the server
server = RancherMCPServer()

# Start the server
server.start()
```

## License

MIT License - see LICENSE file for details
