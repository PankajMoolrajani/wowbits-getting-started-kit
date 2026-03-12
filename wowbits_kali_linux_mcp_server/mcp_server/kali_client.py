"""
kali_client.py — HTTP client for the Kali API server running in Docker.

All tool modules call kali_client.run(command, timeout) which POSTs to
the Flask /execute endpoint and returns a formatted string.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

_base_url: str | None = None


def get_base_url() -> str:
    global _base_url
    if _base_url is None:
        _base_url = os.environ.get("KALI_API_URL", "http://localhost:5000").rstrip("/")
    return _base_url


def run(command: str, timeout: int = 120) -> str:
    """
    Execute *command* on the Kali container via POST /execute.

    Returns a human-readable string with stdout, stderr (if any), and exit code.
    Never raises — errors are returned as error strings so agents always get output.
    """
    url = f"{get_base_url()}/execute"

    try:
        resp = requests.post(
            url,
            json={"command": command, "timeout": timeout},
            timeout=timeout + 15,  # HTTP timeout slightly larger than command timeout
        )
        resp.raise_for_status()
        data = resp.json()

    except requests.ConnectionError:
        return (
            f"[ERROR] Cannot connect to Kali API at {get_base_url()}.\n"
            "Is the container running?  →  docker-compose up -d"
        )
    except requests.Timeout:
        return f"[ERROR] HTTP request timed out waiting for command (timeout={timeout}s)."
    except requests.HTTPError as exc:
        return f"[ERROR] Kali API returned HTTP {exc.response.status_code}: {exc.response.text}"
    except Exception as exc:
        return f"[ERROR] Unexpected error communicating with Kali API: {exc}"

    # API-level error (e.g. blocked by allowlist)
    if "error" in data:
        return f"[ERROR] {data['error']}"

    stdout = (data.get("stdout") or "").strip()
    stderr = (data.get("stderr") or "").strip()
    rc = data.get("returncode", 0)

    parts = []
    if stdout:
        parts.append(stdout)
    if stderr:
        parts.append(f"[stderr]\n{stderr}")
    if rc not in (0, None) and not stderr:
        parts.append(f"[exit code: {rc}]")

    return "\n".join(parts) if parts else "Command completed with no output."
