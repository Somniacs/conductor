from pathlib import Path

HOST = "0.0.0.0"
PORT = 7777
BASE_URL = f"http://{HOST}:{PORT}"

CONDUCTOR_DIR = Path.home() / ".conductor"
SESSIONS_DIR = CONDUCTOR_DIR / "sessions"
LOG_DIR = CONDUCTOR_DIR / "logs"
PID_FILE = CONDUCTOR_DIR / "server.pid"

BUFFER_MAX_BYTES = 1_000_000  # 1MB rolling buffer

# Allowed commands for the web dashboard "New Session" form.
# Only the base command name is checked (first token before args).
# The CLI is unrestricted — this only limits what the dashboard can launch.
ALLOWED_COMMANDS = [
    {"command": "claude --dangerously-skip-permissions", "label": "Claude Code"},
    {"command": "codex", "label": "OpenAI Codex CLI"},
    {"command": "gh copilot", "label": "GitHub Copilot CLI"},
    {"command": "aider", "label": "Aider"},
    {"command": "cursor", "label": "Cursor Agent"},
    {"command": "goose", "label": "Goose (Block)"},
]

# Default working directories shown in the dashboard directory picker.
DEFAULT_DIRECTORIES = [
    str(Path.home()),
    str(Path.home() / "Documents"),
]


def ensure_dirs():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
