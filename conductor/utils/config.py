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

VERSION = "0.3.0"
CONDUCTOR_TOKEN = os.environ.get("CONDUCTOR_TOKEN")

HOST = "0.0.0.0"
PORT = 7777
BASE_URL = f"http://127.0.0.1:{PORT}"

CONDUCTOR_DIR = Path.home() / ".conductor"
SESSIONS_DIR = CONDUCTOR_DIR / "sessions"
LOG_DIR = CONDUCTOR_DIR / "logs"
UPLOADS_DIR = CONDUCTOR_DIR / "uploads"
PID_FILE = CONDUCTOR_DIR / "server.pid"

BUFFER_MAX_BYTES = 1_000_000  # 1MB rolling buffer
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "image/bmp"}

# Allowed commands for the web dashboard "New Session" form.
# Only the base command name is checked (first token before args).
# The CLI is unrestricted — this only limits what the dashboard can launch.
#
# Resume support (optional per command):
#   resume_pattern  — regex applied to terminal output to extract a resume ID.
#                     Must contain exactly one capture group for the ID.
#   resume_flag     — CLI flag prepended to the resume ID when restarting,
#                     e.g. "--resume" → "claude ... --resume <id>".
#
# Commands without resume_pattern/resume_flag simply won't offer resume.
ALLOWED_COMMANDS = [
    {
        "command": "claude --dangerously-skip-permissions",
        "label": "Claude Code",
        "resume_pattern": r"--resume\s+(\S+)",
        "resume_flag": "--resume",
        # Graceful stop: Ctrl-C to cancel any running task, then /exit to
        # trigger Claude's own shutdown which prints the resume token.
        "stop_sequence": ["\x03", "/exit", "\r"],
    },
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
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
