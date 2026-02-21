# Setup script for Atlassian MCP
# Prerequisites: Node.js v18+ and npm must be installed
# The mcp-remote package will be auto-installed via npx on first run
import sys
from setuptools import setup, find_packages

def do_setup():
    setup(
        name="atlassian-mcps",
        version="0.1.0",
        packages=find_packages(),
        install_requires=[
        ],
        entry_points={
            "console_scripts": [
                "atlassian-mcps=run:main", 
            ],
        },
    )

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No command supplied, run install
        sys.argv.append("install")
    do_setup()