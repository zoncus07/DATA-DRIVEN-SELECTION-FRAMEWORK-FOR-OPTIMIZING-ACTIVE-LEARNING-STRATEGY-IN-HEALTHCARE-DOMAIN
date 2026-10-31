"""
Desktop launcher for the Active Learning Strategy Recommender.

Runs the Flask app on a local port and opens it inside a native
window via pywebview, so the whole thing behaves like a normal
desktop application (and can be frozen into a single .exe).
"""
import sys
import os
import threading
import socket
import time

import webview

from app import app as flask_app


def resource_path(relative_path):
    """Resolve a path correctly whether running from source or a PyInstaller bundle."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_flask(port):
    flask_app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def main():
    port = find_free_port()

    server_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    server_thread.start()

    # Give Flask a moment to bind before pointing the window at it
    time.sleep(0.6)

    webview.create_window(
        "Active Learning Strategy Recommender",
        f"http://127.0.0.1:{port}",
        width=1080,
        height=820,
        min_size=(760, 600),
        background_color="#f2f4ef",
    )

    try:
        # Force the modern Edge (Chromium) engine. Without this, pywebview
        # can silently fall back to the legacy IE/Trident renderer on
        # Windows machines missing the WebView2 Runtime, which produces a
        # badly broken layout instead of an error.
        webview.start(gui="edgechromium")
    except Exception as e:
        import ctypes
        message = (
            "This app requires the Microsoft Edge WebView2 Runtime, which "
            "doesn't seem to be installed.\n\n"
            "Download it from:\n"
            "https://developer.microsoft.com/en-us/microsoft-edge/webview2/\n\n"
            f"Details: {e}"
        )
        try:
            ctypes.windll.user32.MessageBoxW(0, message, "Missing WebView2 Runtime", 0x10)
        except Exception:
            print(message)


if __name__ == "__main__":
    main()
