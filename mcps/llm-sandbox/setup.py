import subprocess
import sys

"""pip install llm-sandbox[mcp-docker]"""

def main():
    """Install llm-sandbox with MCP Docker backend dependencies."""
    print("Installing llm-sandbox with MCP Docker support...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "llm-sandbox[mcp-docker]"
    ])
    print("✅ llm-sandbox[mcp-docker] installed successfully.")


if __name__ == "__main__":
    main()

