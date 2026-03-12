"""
Command executor for the Kali API server.

Handles subprocess execution with timeouts, logging, and an optional
command allowlist (if ENFORCE_ALLOWLIST=true in the container env).
"""

import logging
import os
import shlex
import subprocess

logger = logging.getLogger(__name__)

# Pre-approved base commands. Enforced only when ENFORCE_ALLOWLIST=true.
ALLOWED_COMMANDS = {
    # Network recon
    "nmap", "netexec", "nxc",
    # Web
    "gobuster", "nikto", "sqlmap", "curl", "wget",
    # Exploitation helpers
    "searchsploit",
    # System / file utils (useful for agents navigating the container)
    "cat", "ls", "pwd", "find", "file", "stat", "head", "tail",
    "grep", "awk", "sed", "cut", "wc", "sort", "uniq", "tr",
    "echo", "printf", "env",
    # Network utils
    "ping", "traceroute", "ip", "ifconfig", "netstat", "ss",
    "whois", "dig", "host", "nslookup",
    # Scripting
    "python3", "python", "bash", "sh",
    # File transfers
    "scp", "rsync", "nc", "netcat",
}


def is_allowed(command: str) -> bool:
    """Return True if the base command is in the allowlist."""
    try:
        parts = shlex.split(command.strip())
        if not parts:
            return False
        base = os.path.basename(parts[0])
        return base in ALLOWED_COMMANDS
    except Exception:
        return False


def execute(command: str, timeout: int = 120) -> dict:
    """
    Execute a shell command.

    Returns a dict with keys: stdout, stderr, returncode.
    Never raises — errors are captured and returned in the dict.
    """
    if not command or not command.strip():
        return {"stdout": "", "stderr": "Empty command provided.", "returncode": 1}

    logger.info("Executing (timeout=%ss): %s", timeout, command)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        logger.debug("Exit %s for: %s", result.returncode, command)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        logger.warning("Timeout (%ss) for: %s", timeout, command)
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds.",
            "returncode": 124,
        }
    except Exception as exc:
        logger.error("Execution error for '%s': %s", command, exc)
        return {
            "stdout": "",
            "stderr": f"Execution error: {exc}",
            "returncode": 1,
        }
