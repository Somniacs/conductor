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

import json
from typing import Dict, Optional

from conductor.sessions.session import Session
from conductor.utils.config import SESSIONS_DIR, ensure_dirs


class SessionRegistry:
    """In-memory registry of all sessions, with metadata persisted to disk.

    Running sessions live in ``self.sessions``.  When a session exits and
    its terminal output contains a ``--resume <id>`` token (e.g. from
    Claude Code), its metadata is kept in ``self.resumable`` so the user
    can resume the conversation later — even after a server restart.
    """

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.resumable: Dict[str, dict] = {}
        ensure_dirs()
        self._load_resumable()

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

    async def create(self, name: str, command: str, cwd: str | None = None) -> Session:
        if name in self.sessions:
            existing = self.sessions[name]
            if existing.status == "running":
                raise ValueError(f"Session '{name}' already exists and is running")
            else:
                await self.remove(name)

        # If resuming over an old resumable entry with the same name, clear it.
        self.resumable.pop(name, None)

        session = Session(
            name=name,
            command=command,
            session_id=name,
            cwd=cwd,
            on_exit=self._on_session_exit,
        )
        await session.start()
        self.sessions[name] = session
        self._save_metadata(session)
        return session

    async def resume(self, session_id: str) -> Session:
        """Resume a previously exited session using its stored resume_id."""
        meta = self.resumable.pop(session_id, None)
        if not meta or not meta.get("resume_id"):
            raise ValueError(f"No resumable session '{session_id}'")

        # Build the command: original command + --resume <id>
        command = meta["command"] + f" --resume {meta['resume_id']}"
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
