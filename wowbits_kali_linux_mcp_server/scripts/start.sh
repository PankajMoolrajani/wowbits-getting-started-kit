#!/usr/bin/env bash
# Start the Kali API container as a background service
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Starting Kali API container..."
docker-compose up -d --build

echo ""
echo "✅  Kali API server is running at http://localhost:5000"
echo ""
echo "Next: start the MCP server on your host:"
echo "  cd $(pwd)"
echo "  pip install -r requirements.txt"
echo "  export KALI_API_URL=http://localhost:5000"
echo "  python3 mcp_server/server.py"
