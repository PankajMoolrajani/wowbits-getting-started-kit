#!/usr/bin/env python3
"""
Run the Memento Protocol MCP server via supergateway (STDIO → SSE bridge).

Uses the remote Memento API via `npx memento-mcp` — no local repo clone needed.
Environment variables (MEMENTO_API_KEY, MEMENTO_API_URL, MEMENTO_WORKSPACE)
are loaded from the project .env file.
"""

import subprocess
import os
import json
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).resolve().parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

# Load config
config_path = Path(__file__).resolve().parent / "config.json"
with open(config_path) as f:
    config = json.load(f)

port = config["server"]["port"]
host = config["server"]["host"]

# Verify required env vars
api_key = os.environ.get("MEMENTO_API_KEY")
if not api_key:
    print("❌ MEMENTO_API_KEY not set in .env file")
    print("   Sign up first: curl -X POST https://memento-api.myrakrusemark.workers.dev/v1/auth/signup \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"workspace": "wowbits-project"}\'')
    exit(1)

api_url = os.environ.get("MEMENTO_API_URL", "https://memento-api.myrakrusemark.workers.dev")
workspace = os.environ.get("MEMENTO_WORKSPACE", "wowbits-project")

print(f"🚀 Starting Memento MCP server (remote) via supergateway on {host}:{port}")
print(f"   Using: npx memento-mcp (remote API)")
print(f"   API URL: {api_url}")
print(f"   Workspace: {workspace}")

# Build environment for the subprocess
env = os.environ.copy()
env["MEMENTO_API_KEY"] = api_key
env["MEMENTO_API_URL"] = api_url
env["MEMENTO_WORKSPACE"] = workspace

# Use supergateway to bridge npx memento-mcp (STDIO) → SSE
subprocess.run(
    [
        "npx", "-y", "supergateway",
        "--stdio", "npx -y memento-mcp",
        "--port", str(port),
        "--host", host,
    ],
    env=env,
)
