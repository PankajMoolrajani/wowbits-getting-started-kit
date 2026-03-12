#!/usr/bin/env python3
"""
kali_api_server/server.py — Flask REST API entry point.

Runs INSIDE the Kali Docker container.
Accepts HTTP requests from the host-side MCP server and executes
terminal commands via executor.py.

Endpoints:
  GET  /health           → {"status": "ok"}
  POST /execute          → {"command": "...", "timeout": 120}
                         ← {"stdout": "...", "stderr": "...", "returncode": 0}
"""

import logging
import os
import sys

# Ensure /app is on the path so "from kali_api_server import executor" resolves
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request
from kali_api_server import executor

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ENFORCE_ALLOWLIST = os.getenv("ENFORCE_ALLOWLIST", "false").lower() == "true"


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/execute")
def execute_command():
    data = request.get_json(force=True, silent=True) or {}

    command = data.get("command", "").strip()
    timeout = int(data.get("timeout", 120))

    if not command:
        return jsonify({"error": "No command provided."}), 400

    if ENFORCE_ALLOWLIST and not executor.is_allowed(command):
        base = command.split()[0]
        logger.warning("Blocked disallowed command: %s", base)
        return jsonify({"error": f"Command not in allowlist: {base}"}), 403

    result = executor.execute(command, timeout=timeout)
    return jsonify(result)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG"
    logger.info("WowBits Kali API Server starting on %s:%s", host, port)
    app.run(host=host, port=port, debug=debug)
