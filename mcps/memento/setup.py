#!/usr/bin/env python3
"""
Setup for the Memento Protocol MCP server (remote mode).

Uses the remote Memento API via `npx memento-mcp` — no local repo clone needed.
This script just verifies prerequisites (Node.js, npm) and reminds about API key setup.
"""

import subprocess
import sys


def check_command(cmd, description):
    """Check if a command is available."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True
        )
        version = result.stdout.strip()
        print(f"  ✅ {description}: {version}")
        return True
    except FileNotFoundError:
        print(f"  ❌ {description}: NOT FOUND")
        return False


def main():
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║     Memento Protocol MCP Server Setup (Remote Mode)         ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")

    # Step 1: Verify prerequisites
    print("🔍 Checking prerequisites...\n")
    
    ok = True
    ok = check_command(["node", "--version"], "Node.js") and ok
    ok = check_command(["npm", "--version"], "npm") and ok

    if not ok:
        print("\n❌ Missing prerequisites. Please install Node.js first.")
        print("   https://nodejs.org/")
        sys.exit(1)

    # Step 2: Verify supergateway is available
    print("\n🔧 Verifying supergateway availability...")
    result = subprocess.run(
        ["npx", "-y", "supergateway", "--help"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("  ✅ supergateway is available via npx")
    else:
        print("  ⚠️  supergateway will be auto-installed on first run via npx -y")

    # Step 3: Verify memento-mcp is available
    print("\n🧠 Verifying memento-mcp availability...")
    result = subprocess.run(
        ["npx", "-y", "memento-mcp", "--help"],
        capture_output=True, text=True,
        timeout=30
    )
    if result.returncode == 0:
        print("  ✅ memento-mcp is available via npx")
    else:
        print("  ⚠️  memento-mcp will be auto-installed on first run via npx -y")

    # Step 4: Remind about API key
    print("\n" + "=" * 60)
    print("✅ Setup complete! (No local clone needed — uses remote API)")
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
