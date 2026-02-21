#!/usr/bin/env python3
"""
One-time setup for the Memento Protocol MCP server.

This script:
1. Clones the memento-protocol GitHub repo
2. Runs npm install in the cloned repo
3. Verifies supergateway is available via npx
"""

import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/myrakrusemark/memento-protocol.git"
SCRIPT_DIR = Path(__file__).resolve().parent
MEMENTO_DIR = SCRIPT_DIR / "memento-protocol"


def run_cmd(cmd, cwd=None, description=""):
    """Run a command and handle errors."""
    print(f"  ⏳ {description}...")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ Failed: {description}")
        print(f"     stdout: {result.stdout}")
        print(f"     stderr: {result.stderr}")
        sys.exit(1)
    print(f"  ✅ {description}")
    return result


def main():
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║         Memento Protocol MCP Server Setup                    ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")

    # Step 1: Clone the repo
    if MEMENTO_DIR.exists():
        print(f"📁 Memento Protocol repo already exists at {MEMENTO_DIR}")
        print("   Pulling latest changes...")
        run_cmd(
            ["git", "pull"],
            cwd=str(MEMENTO_DIR),
            description="Pulling latest changes"
        )
    else:
        print(f"📥 Cloning Memento Protocol repo...")
        run_cmd(
            ["git", "clone", REPO_URL, str(MEMENTO_DIR)],
            description="Cloning memento-protocol repository"
        )

    # Step 2: Install npm dependencies
    print("\n📦 Installing npm dependencies...")
    run_cmd(
        ["npm", "install"],
        cwd=str(MEMENTO_DIR),
        description="Installing npm dependencies"
    )

    # Step 3: Verify supergateway is available
    print("\n🔧 Verifying supergateway availability...")
    result = subprocess.run(
        ["npx", "-y", "supergateway", "--help"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  ✅ supergateway is available via npx")
    else:
        print("  ⚠️  supergateway not readily available, will be auto-installed on first run via npx -y")

    # Step 4: Remind about API key
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("   1. Sign up for a Memento API key (if you haven't already):")
    print('      curl -X POST https://memento-api.myrakrusemark.workers.dev/v1/auth/signup \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"workspace": "wowbits-project"}\'')
    print("\n   2. Add the API key to your .env file:")
    print("      MEMENTO_API_KEY=mp_live_your_key_here")
    print("      MEMENTO_API_URL=https://memento-api.myrakrusemark.workers.dev")
    print("      MEMENTO_WORKSPACE=wowbits-project")
    print("\n   3. Run the server:")
    print("      python run.py")


if __name__ == "__main__":
    main()
