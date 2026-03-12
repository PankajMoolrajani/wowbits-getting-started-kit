#!/usr/bin/env python3
"""
mcp_server/server.py — WowBits Kali Linux MCP Server entry point.

Runs on the HOST machine (not inside Docker) as a standalone HTTP server.
Any MCP client connects to it over HTTP — no path dependency, no subprocess spawning.

Usage:
    # 1. Start the Kali container
    docker-compose up -d

    # 2. Start this MCP server (runs on http://localhost:8765/mcp by default)
    export KALI_API_URL=http://localhost:5000
    python3 mcp_server/server.py

Environment variables:
    KALI_API_URL   Base URL of the Kali API server   (default: http://localhost:5000)
    MCP_HOST       Host to bind to                   (default: 127.0.0.1)
    MCP_PORT       Port to listen on                 (default: 8765)
    LOG_LEVEL      Logging level                     (default: INFO)
"""

import logging
import os
import sys

# Ensure the project root (wowbits_kali_linux_mcp_server/) is on sys.path
# so that "from mcp_server import kali_client" and tool imports resolve correctly
# regardless of the current working directory when this script is launched.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from fastmcp import FastMCP
from mcp_server.tools import register_all

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# --- MCP server instance ---------------------------------------------------

mcp = FastMCP("WowBitsKaliMCP")

# Auto-register every tool module found in mcp_server/tools/
register_all(mcp)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    kali_url = os.environ.get("KALI_API_URL", "http://localhost:5000")
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8765"))
    logger.info("WowBits Kali Linux MCP Server starting")
    logger.info("Kali API target: %s", kali_url)
    logger.info("MCP endpoint:    http://%s:%d/mcp", host, port)
    mcp.run(transport="streamable-http", host=host, port=port)
