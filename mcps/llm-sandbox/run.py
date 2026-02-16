import os
import subprocess
import sys
"""python -m llm_sandbox.mcp_server.server"""

def main():
    env = os.environ.copy()
    env.update({
        "BACKEND": "docker",
        "DOCKER_HOST": "unix:///var/run/docker.sock",
        "COMMIT_CONTAINER": "false",
        "KEEP_TEMPLATE": "false",
        "DEFAULT_IMAGE": "python:3.11-slim",
    })

    try:
        subprocess.run(
            [sys.executable, "-m", "llm_sandbox.mcp_server.server"],
            env=env,
            check=True,
        )
    except KeyboardInterrupt:
        print("\nLLM Sandbox MCP server stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting LLM Sandbox MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
