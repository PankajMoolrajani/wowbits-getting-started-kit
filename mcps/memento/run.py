#!/usr/bin/env python3
"""
Run the Memento Protocol MCP server via supergateway (STDIO → SSE bridge).

This script:
1. Loads environment variables from the project .env
2. Launches supergateway to wrap the Memento MCP (STDIO) as an SSE server on port 8932
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

# Path to the memento-protocol repo (cloned by setup.py)
memento_repo = Path(__file__).resolve().parent / "memento-protocol"
index_js = memento_repo / "src" / "index.js"

if not index_js.exists():
    print(f"❌ Memento Protocol not found at {index_js}")
    print("   Run 'python setup.py' first to clone and install the repo.")
    exit(1)

# Verify required env vars
api_key = os.environ.get("MEMENTO_API_KEY")
if not api_key:
    print("❌ MEMENTO_API_KEY not set in .env file")
    print("   Sign up first: curl -X POST https://memento-api.myrakrusemark.workers.dev/v1/auth/signup \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"workspace": "wowbits-project"}\'')
    exit(1)

print(f"🚀 Starting Memento MCP server via supergateway on {host}:{port}")
print(f"   Memento repo: {memento_repo}")
print(f"   API URL: {os.environ.get('MEMENTO_API_URL', 'https://memento-api.myrakrusemark.workers.dev')}")
print(f"   Workspace: {os.environ.get('MEMENTO_WORKSPACE', 'wowbits-project')}")

# Build environment for the subprocess
env = os.environ.copy()
env["MEMENTO_API_KEY"] = api_key
env["MEMENTO_API_URL"] = os.environ.get("MEMENTO_API_URL", "https://memento-api.myrakrusemark.workers.dev")
env["MEMENTO_WORKSPACE"] = os.environ.get("MEMENTO_WORKSPACE", "wowbits-project")

# Use supergateway to bridge STDIO → SSE
subprocess.run(
    [
        "npx", "-y", "supergateway",
        "--stdio", f"node {index_js}",
        "--port", str(port),
        "--host", host,
    ],
    env=env,
)
