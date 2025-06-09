# Rancher MCP Server

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
