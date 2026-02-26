# conductor — Local orchestration for terminal sessions.
#
# Copyright (c) 2026 Max Rheiner / Somniacs AG
#
# Licensed under the MIT License. You may obtain a copy
# of the license at:
#
#     https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

"""Central configuration — networking, paths, buffer sizes, command whitelist."""

import os
from pathlib import Path

import yaml

VERSION = "0.3.1"
CONDUCTOR_TOKEN = os.environ.get("CONDUCTOR_TOKEN")

HOST = "0.0.0.0"
PORT = 7777
BASE_URL = f"http://127.0.0.1:{PORT}"

CONDUCTOR_DIR = Path.home() / ".conductor"
SESSIONS_DIR = CONDUCTOR_DIR / "sessions"
LOG_DIR = CONDUCTOR_DIR / "logs"
UPLOADS_DIR = CONDUCTOR_DIR / "uploads"
PID_FILE = CONDUCTOR_DIR / "server.pid"
USER_CONFIG_FILE = CONDUCTOR_DIR / "config.yaml"

# ── Defaults (overridden by ~/.conductor/config.yaml if it exists) ──────────

BUFFER_MAX_BYTES = 1_000_000  # 1MB rolling buffer
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
GRACEFUL_STOP_TIMEOUT = 30  # seconds before force-kill
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp"}

_DEFAULT_ALLOWED_COMMANDS = [
    {
        "command": "claude",
        "label": "Claude Code",
        "resume_pattern": r"--resume\s+(\S+)",
        "resume_flag": "--resume",
        "stop_sequence": ["\x03", "/exit", "\r"],
    },
    {
        "command": "claude --dangerously-skip-permissions",
        "label": "Claude Code (skip permissions)",
        "resume_pattern": r"--resume\s+(\S+)",
        "resume_flag": "--resume",
        "stop_sequence": ["\x03", "/exit", "\r"],
    },
    {"command": "codex", "label": "OpenAI Codex CLI"},
    {"command": "gh copilot", "label": "GitHub Copilot CLI"},
    {"command": "aider", "label": "Aider"},
    {"command": "cursor", "label": "Cursor Agent"},
    {"command": "goose", "label": "Goose (Block)"},
]

_DEFAULT_DIRECTORIES = [
    str(Path.home()),
    str(Path.home() / "Documents"),
]

# ── Mutable runtime state ───────────────────────────────────────────────────

ALLOWED_COMMANDS: list[dict] = list(_DEFAULT_ALLOWED_COMMANDS)
DEFAULT_DIRECTORIES: list[str] = list(_DEFAULT_DIRECTORIES)

_config_version: int = 0


def get_config_version() -> int:
    return _config_version


def load_user_config():
    """Load ~/.conductor/config.yaml and merge over defaults."""
    global ALLOWED_COMMANDS, DEFAULT_DIRECTORIES, BUFFER_MAX_BYTES, MAX_UPLOAD_SIZE, GRACEFUL_STOP_TIMEOUT

    if not USER_CONFIG_FILE.exists():
        return

    try:
        data = yaml.safe_load(USER_CONFIG_FILE.read_text()) or {}
    except Exception:
        return

    if "allowed_commands" in data and isinstance(data["allowed_commands"], list):
        ALLOWED_COMMANDS = data["allowed_commands"]
    if "default_directories" in data and isinstance(data["default_directories"], list):
        DEFAULT_DIRECTORIES = data["default_directories"]
    if "buffer_max_bytes" in data and isinstance(data["buffer_max_bytes"], int):
        BUFFER_MAX_BYTES = data["buffer_max_bytes"]
    if "max_upload_size" in data and isinstance(data["max_upload_size"], int):
        MAX_UPLOAD_SIZE = data["max_upload_size"]
    if "graceful_stop_timeout" in data and isinstance(data["graceful_stop_timeout"], (int, float)):
        GRACEFUL_STOP_TIMEOUT = data["graceful_stop_timeout"]


def save_user_config(data: dict):
    """Write settings to ~/.conductor/config.yaml and update in-memory values."""
    global ALLOWED_COMMANDS, DEFAULT_DIRECTORIES, BUFFER_MAX_BYTES, MAX_UPLOAD_SIZE, GRACEFUL_STOP_TIMEOUT, _config_version

    if "allowed_commands" in data and isinstance(data["allowed_commands"], list):
        ALLOWED_COMMANDS = data["allowed_commands"]
    if "default_directories" in data and isinstance(data["default_directories"], list):
        DEFAULT_DIRECTORIES = data["default_directories"]
    if "buffer_max_bytes" in data and isinstance(data["buffer_max_bytes"], int):
        BUFFER_MAX_BYTES = data["buffer_max_bytes"]
    if "max_upload_size" in data and isinstance(data["max_upload_size"], int):
        MAX_UPLOAD_SIZE = data["max_upload_size"]
    if "graceful_stop_timeout" in data and isinstance(data["graceful_stop_timeout"], (int, float)):
        GRACEFUL_STOP_TIMEOUT = data["graceful_stop_timeout"]

    config_out = {
        "allowed_commands": ALLOWED_COMMANDS,
        "default_directories": DEFAULT_DIRECTORIES,
        "buffer_max_bytes": BUFFER_MAX_BYTES,
        "max_upload_size": MAX_UPLOAD_SIZE,
        "graceful_stop_timeout": GRACEFUL_STOP_TIMEOUT,
    }

    CONDUCTOR_DIR.mkdir(parents=True, exist_ok=True)
    USER_CONFIG_FILE.write_text(yaml.dump(config_out, default_flow_style=False, sort_keys=False))
    _config_version += 1


def get_editable_settings() -> dict:
    """Return current editable settings for the admin API."""
    return {
        "allowed_commands": ALLOWED_COMMANDS,
        "default_directories": DEFAULT_DIRECTORIES,
        "buffer_max_bytes": BUFFER_MAX_BYTES,
        "max_upload_size": MAX_UPLOAD_SIZE,
        "graceful_stop_timeout": GRACEFUL_STOP_TIMEOUT,
    }


def get_admin_settings() -> dict:
    """Return full settings for the admin panel (editable + read-only)."""
    return {
        **get_editable_settings(),
        "host": HOST,
        "port": PORT,
        "version": VERSION,
        "auth_enabled": CONDUCTOR_TOKEN is not None,
    }


# ── Load user config on import ──────────────────────────────────────────────

load_user_config()


def ensure_dirs():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
