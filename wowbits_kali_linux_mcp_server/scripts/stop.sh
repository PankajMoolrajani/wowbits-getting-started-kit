#!/usr/bin/env bash
# Stop and remove the Kali API container
set -euo pipefail
cd "$(dirname "$0")/.."
echo "==> Stopping Kali API container..."
docker-compose down
echo "==> Done."
