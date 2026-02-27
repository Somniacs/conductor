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

"""In-memory session registry with metadata persisted to disk."""

import asyncio
import json
import shlex
from typing import Dict, Optional

from conductor.sessions.session import Session
from conductor.utils import config as cfg
from conductor.utils.config import SESSIONS_DIR, ensure_dirs


class SessionRegistry:
    """In-memory registry of all sessions, with metadata persisted to disk.

    Running sessions live in ``self.sessions``.  When a session exits and
    its terminal output matches a configured resume pattern (e.g. Claude
    Code's ``--resume <id>``), its metadata is kept in ``self.resumable``
    so the user can resume the conversation later — even after a server
    restart.  Resume patterns are configured per command in
    ``ALLOWED_COMMANDS`` (see config.py).
    """

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.resumable: Dict[str, dict] = {}
        ensure_dirs()
        self._load_resumable()

    @staticmethod
    def _agent_config_for(command: str) -> dict:
        """Return per-command config fields for a command.

        Matches the command's base executable against ALLOWED_COMMANDS entries
        and returns resume_pattern, resume_flag, and stop_sequence (if any).
        """
        try:
            base = shlex.split(command)[0]
        except ValueError:
            return {}
        for entry in cfg.ALLOWED_COMMANDS:
            try:
                entry_base = shlex.split(entry["command"])[0]
            except ValueError:
                continue
            if base == entry_base:
                return {
                    k: entry[k]
                    for k in ("resume_pattern", "resume_flag", "resume_command", "stop_sequence")
                    if k in entry
                }
        return {}

    def _load_resumable(self):
        """Load persisted resumable-session metadata from disk on startup."""
        for path in SESSIONS_DIR.glob("*.json"):
            try:
                meta = json.loads(path.read_text())
                if meta.get("resume_id") and meta.get("status") == "exited":
                    self.resumable[meta["id"]] = meta
            except Exception:
                pass

    async def _on_session_exit(self, session_id: str):
        """Called when a session's process exits."""
        session = self.sessions.pop(session_id, None)
        if not session:
            return

        if session.resume_id:
            # Keep the metadata so the user can resume later.
            meta = session.to_dict()
            self.resumable[session_id] = meta
            self._save_metadata_dict(meta)
        else:
            self._delete_metadata(session_id)

    async def create(self, name: str, command: str, cwd: str | None = None,
                     env: dict | None = None, rows: int | None = None,
                     cols: int | None = None, source: str | None = None) -> Session:
        if name in self.sessions:
            existing = self.sessions[name]
            if existing.status == "running":
                raise ValueError(f"Session '{name}' already exists and is running")
            else:
                await self.remove(name)

        # If resuming over an old resumable entry with the same name, clear it.
        self.resumable.pop(name, None)

        agent_cfg = self._agent_config_for(command)

        session = Session(
            name=name,
            command=command,
            session_id=name,
            cwd=cwd,
            on_exit=self._on_session_exit,
            env=env,
            resume_pattern=agent_cfg.get("resume_pattern"),
            resume_flag=agent_cfg.get("resume_flag"),
            resume_command=agent_cfg.get("resume_command"),
            stop_sequence=agent_cfg.get("stop_sequence"),
        )
        await session.start(rows=rows or 24, cols=cols or 80)
        # Record initial size so the web client knows the PTY dimensions.
        if rows and cols and source == "cli":
            session.resize(rows, cols, source="cli")
        self.sessions[name] = session
        self._save_metadata(session)
        return session

    async def resume(self, session_id: str) -> Session:
        """Resume a previously exited session using its stored resume ID.

        Two modes:

        1. **Token-based** (Claude Code, Copilot) — a ``resume_pattern``
           captures a token from the terminal output and ``resume_flag``
           appends it to the original command, e.g.
           ``claude ... --resume <id>``.
        2. **Command-based** (Codex) — a fixed ``resume_command`` replaces
           the original command entirely, e.g. ``codex resume --last``.
        """
        meta = self.resumable.pop(session_id, None)

        # Edge case: session just exited but _on_session_exit hasn't moved
        # it to self.resumable yet — check self.sessions as a fallback.
        if not meta:
            live = self.sessions.get(session_id)
            if live and live.status == "exited" and live.resume_id:
                meta = live.to_dict()
                self.sessions.pop(session_id, None)
                if live._monitor_task:
                    live._monitor_task.cancel()
                    try:
                        await live._monitor_task
                    except asyncio.CancelledError:
                        pass
                live.pty.close()

        if not meta or not meta.get("resume_id"):
            raise ValueError(f"No resumable session '{session_id}'")

        # Command-based resume (e.g. "codex resume --last") — use as-is.
        if meta.get("resume_command"):
            command = meta["resume_command"]
        else:
            # Token-based resume — append flag + captured ID to original command.
            flag = meta.get("resume_flag", "--resume")
            # Strip any previous resume flag+id from the command to avoid
            # accumulation across multiple resumes.
            import re as _re
            command = _re.sub(
                rf'\s*{_re.escape(flag)}\s+\S+', '', meta["command"]
            ).rstrip()
            command += f" {flag} {meta['resume_id']}"

        cwd = meta.get("cwd")
        self._delete_metadata(session_id)

        return await self.create(meta["name"], command, cwd=cwd)

    def get(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    def list_all(self) -> list[dict]:
        live = [s.to_dict() for s in self.sessions.values()]
        resumable = list(self.resumable.values())
        return live + resumable

    async def remove(self, session_id: str):
        session = self.sessions.pop(session_id, None)
        if session:
            await session.kill()
            await session.cleanup()
            self._delete_metadata(session_id)

    def graceful_stop(self, session_id: str):
        """Send SIGINT to the session for a graceful shutdown.

        The session stays in ``self.sessions`` — its ``_monitor_process``
        task will detect the exit, extract any resume token from the
        terminal buffer, and call ``_on_session_exit`` which moves the
        session to ``self.resumable`` if a resume ID was found.
        """
        session = self.sessions.get(session_id)
        if session and session.status in ("running", "starting"):
            session.interrupt(timeout=cfg.GRACEFUL_STOP_TIMEOUT)

    def dismiss_resumable(self, session_id: str):
        """Remove a resumable entry without resuming it."""
        self.resumable.pop(session_id, None)
        self._delete_metadata(session_id)

    def _save_metadata(self, session: Session):
        path = SESSIONS_DIR / f"{session.id}.json"
        path.write_text(json.dumps(session.to_dict(), indent=2))

    def _save_metadata_dict(self, meta: dict):
        path = SESSIONS_DIR / f"{meta['id']}.json"
        path.write_text(json.dumps(meta, indent=2))

    def _delete_metadata(self, session_id: str):
        path = SESSIONS_DIR / f"{session_id}.json"
        path.unlink(missing_ok=True)

    async def cleanup_all(self):
        for session_id in list(self.sessions.keys()):
            await self.remove(session_id)
