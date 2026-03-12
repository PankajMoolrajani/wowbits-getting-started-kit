"""
Convenience launcher for the WowBits Kali Linux MCP stack.

Both services (Kali tool executor + MCP HTTP server) run inside Docker.
This script just starts docker-compose from the correct directory.

After running this, the MCP endpoint is live at: http://localhost:8765/mcp
wowbits connects to that URL automatically — no path dependency.

Usage:
  python3 mcps/kali_linux/run.py            # start the stack
  python3 mcps/kali_linux/run.py stop       # stop the stack
"""

import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _find_compose_dir() -> str:
  folder_name = "wowbits_kali_linux_mcp_server"
  candidates = [
    os.path.join(_HERE, folder_name),
    os.path.join(os.path.dirname(_HERE), folder_name),
    os.path.join(os.path.dirname(os.path.dirname(_HERE)), folder_name),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_HERE))), folder_name),
  ]
  for path in candidates:
    if os.path.isdir(path):
      return path

  searched = "\n  - ".join(candidates)
  raise FileNotFoundError(
    "Could not find 'wowbits_kali_linux_mcp_server'. Searched:\n"
    f"  - {searched}"
  )


def _compose_cmd() -> list[str]:
  # Prefer 'docker compose' (v2, built-in) over 'docker-compose' (v1 snap)
  # The snap version has a known race condition bug.
  if shutil.which("docker"):
    return ["docker", "compose"]
  if shutil.which("docker-compose"):
    return ["docker-compose"]
  raise FileNotFoundError(
    "Neither 'docker' nor 'docker-compose' was found in PATH. "
    "Please install Docker and Docker Compose."
  )


COMPOSE_DIR = _find_compose_dir()
COMPOSE_CMD = _compose_cmd()

action = sys.argv[1] if len(sys.argv) > 1 else "up"

if action == "stop":
  subprocess.run([*COMPOSE_CMD, "down"], cwd=COMPOSE_DIR, check=True)
else:
  subprocess.run([*COMPOSE_CMD, "up", "-d", "--build"], cwd=COMPOSE_DIR, check=True)

print("\nMCP server is starting up.")
print("Endpoint: http://localhost:8765/mcp")
print("Stop with: python3 mcps/kali_linux/run.py stop")
