import subprocess
import sys


def _install(package: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


if __name__ == "__main__":
    _install("mcp-proxy")