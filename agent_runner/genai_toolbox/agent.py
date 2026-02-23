import logging
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Path to the tools.yaml config for the GenAI Toolbox
TOOLS_YAML = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "mcps", "genai_toolbox", "tools.yaml"
)

INSTRUCTIONS = """You are a database assistant that helps users explore and query the WowBits SQLite database.
You have access to the GenAI Toolbox for Databases MCP server which provides SQL tools.

## Available Capabilities

1. **List Tables**: Discover all tables in the database
2. **Describe Table**: Get the schema of any table
3. **Query Data**: Run SQL SELECT queries to retrieve data
4. **Search Agents**: Find agents by name
5. **List MCP Servers**: Show all registered MCP configurations
6. **List Skills**: Show all registered skills

## Guidelines

- Always start by listing available tables if the user's request is vague
- Before querying a table, describe its schema first to understand the columns
- Use SELECT queries only - never modify data
- Present results in a clean, formatted manner
- If a query returns too many rows, use LIMIT to restrict results
- Explain what you found in plain language after retrieving data
- Be proactive: suggest related queries the user might find useful
"""

# Use stdio mode — Toolbox runs as a child process, no separate server needed!
root_agent = LlmAgent(
    name="genai_toolbox",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    description="A database assistant agent that uses the GenAI Toolbox for Databases MCP to query and explore the WowBits SQLite database via natural language.",
    instruction=INSTRUCTIONS,
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="toolbox",
                    args=["--stdio", "--tools-file", TOOLS_YAML],
                ),
                timeout=10.0,
            )
        )
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=16000,
    ),
)

logger.info("GenAI Toolbox agent created (stdio mode — no separate server needed)")
