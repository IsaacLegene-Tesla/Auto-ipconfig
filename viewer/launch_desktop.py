#!/usr/bin/env python3
"""
Desktop viewer: starts the Flask API and shows it in a native window.
No browser tab, no need to re-run the .bat for each session.
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "generator"
URL = "http://127.0.0.1:8765"
TITLE = "AMR Fleet Config Builder"


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def _wait_for_server(timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open("127.0.0.1", 8765):
            return True
        time.sleep(0.15)
    return False


def _run_flask() -> None:
    sys.path.insert(0, str(GENERATOR))
    import fleet_app

    fleet_app.run_server()


def main() -> None:
    if not (GENERATOR / "fleet_app.py").is_file():
        raise SystemExit(f"generator not found at {GENERATOR}")

    server = threading.Thread(target=_run_flask, daemon=True)
    server.start()

    if not _wait_for_server():
        raise SystemExit("Server did not start on port 8765")

    try:
        import webview
    except ImportError:
        print("Installing pywebview (one-time)…")
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pywebview", "-q"],
        )
        import webview

    window = webview.create_window(TITLE, URL, width=1120, height=760, min_size=(800, 600))
    webview.start(gui="edgechromium")


if __name__ == "__main__":
    main()
