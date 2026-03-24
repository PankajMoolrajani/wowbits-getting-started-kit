import json
import os
import subprocess
from pathlib import Path


def _load_config() -> dict:
    """Load configuration from config.json in the same directory."""
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r") as f:
        return json.load(f)


def _load_email_config(config: dict) -> dict:
    """Extract and validate email configuration from config dict."""
    email_config = config.get("email_config", {})
    
    required_fields = ["email", "password", "imap_server", "smtp_server"]
    for field in required_fields:
        if not email_config.get(field):
            raise ValueError(f"Missing required field in email_config: {field}")
    
    return {
        "email": email_config["email"],
        "password": email_config["password"],
        "imap_server": email_config["imap_server"],
        "imap_port": email_config.get("imap_port", 993),
        "smtp_server": email_config["smtp_server"],
        "smtp_port": email_config.get("smtp_port", 587),
    }


def main() -> None:
    config = _load_config()
    server_cfg = config.get("server", {})

    host = server_cfg.get("host", "127.0.0.1")
    port = str(server_cfg.get("port", 8942))
    image = "yashtekwani/gmail-mcp"
    connector_cfg = _load_email_config(config)

    child_args = [
        "docker",
        "run",
        "-i",
        "--rm",
        "-e",
        "EMAIL_ADDRESS",
        "-e",
        "IMAP_HOST",
        "-e",
        "IMAP_PORT",
        "-e",
        "SMTP_HOST",
        "-e",
        "SMTP_PORT",
        "-e",
        "EMAIL_PASSWORD",
        image,
    ]

    env = os.environ.copy()
    env["EMAIL_ADDRESS"] = str(connector_cfg["email"])
    env["EMAIL_PASSWORD"] = str(connector_cfg["password"])
    env["IMAP_HOST"] = str(connector_cfg["imap_server"])
    env["IMAP_PORT"] = str(connector_cfg["imap_port"])
    env["SMTP_HOST"] = str(connector_cfg["smtp_server"])
    env["SMTP_PORT"] = str(connector_cfg["smtp_port"])

    command = [
        "mcp-proxy",
        "--host",
        host,
        "--port",
        port,
        "--",
        *child_args,
    ]

    subprocess.run(command, env=env, check=True)


if __name__ == "__main__":
    main()