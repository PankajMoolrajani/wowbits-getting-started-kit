"""
LLM Sandbox Agent — ADK Agent with MCP tool integration.

This agent connects to the llm-sandbox MCP server (stdio transport)
and exposes code-execution tools through the Google ADK Web UI.
"""

import os
import sys

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

# Resolve paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(PROJECT_ROOT, "mcps", "llm-sandbox", ".venv", "bin", "python")

# Fall back to the root venv if the llm-sandbox venv doesn't exist
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")

root_agent = Agent(
    name="llm_sandbox_agent",
    model="openai/gpt-4o-mini",
    description="An AI agent that can execute code in a secure Docker sandbox.",
    instruction="""You are a helpful AI assistant with access to a secure code execution sandbox.

You can execute Python code inside isolated Docker containers using the available tools.

## Capabilities
- **execute_code**: Run Python code in a sandboxed Docker container
- **get_supported_languages**: List programming languages the sandbox supports
- **get_language_details**: Get details about a specific language's sandbox environment

## Guidelines
1. When the user asks you to run code, use the execute_code tool.
2. Always show both the code you're about to execute AND the results.
3. If the code needs external packages, pass them in the `libraries` parameter.
4. Keep execution timeouts reasonable (default 30s, max 120s).
5. If execution fails, explain the error clearly and suggest fixes.
6. For safety, remind users that code runs in an isolated Docker container.
""",
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=VENV_PYTHON,
                    args=["-m", "llm_sandbox.mcp_server.server"],
                    env={
                        "BACKEND": "docker",
                        "COMMIT_CONTAINER": "false",
                        "KEEP_TEMPLATE": "false",
                        "DEFAULT_IMAGE": "python:3.11-slim",
                    },
                ),
            ),
        )
    ],
)
