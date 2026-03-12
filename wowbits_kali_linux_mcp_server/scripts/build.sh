#!/usr/bin/env bash
# Build the Kali API Docker image
set -euo pipefail
cd "$(dirname "$0")/.."
echo "==> Building wowbits-kali-api Docker image..."
docker build -t wowbits-kali-api:latest .
echo "==> Build complete: wowbits-kali-api:latest"
