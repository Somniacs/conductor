import os
from pathlib import Path

HOST = "127.0.0.1"
PORT = 7777
BASE_URL = f"http://{HOST}:{PORT}"

CONDUCTOR_DIR = Path.home() / ".conductor"
SESSIONS_DIR = CONDUCTOR_DIR / "sessions"
LOG_DIR = CONDUCTOR_DIR / "logs"
PID_FILE = CONDUCTOR_DIR / "server.pid"

BUFFER_MAX_BYTES = 1_000_000  # 1MB rolling buffer

PASSWORD = os.environ.get("CONDUCTOR_PASSWORD")


def ensure_dirs():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
