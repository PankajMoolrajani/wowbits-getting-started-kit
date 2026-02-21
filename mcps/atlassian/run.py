import subprocess
import json
import os

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

remote_url = config['remote_server_url']
port = str(config['local_proxy']['port'])

# Start supergateway to bridge mcp-remote (STDIO) as a local SSE server
# mcp-remote handles OAuth 2.1 auth with Atlassian; supergateway exposes it as SSE
# On first run, a browser window will open for OAuth authorization
stdio_cmd = f'npx -y mcp-remote {remote_url}'
subprocess.run(['npx', '-y', 'supergateway', '--stdio', stdio_cmd, '--port', port])

