import json
from typing import Dict, Optional

from conductor.sessions.session import Session
from conductor.utils.config import SESSIONS_DIR, ensure_dirs


class SessionRegistry:
    """In-memory registry of all sessions, with metadata persisted to disk."""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        ensure_dirs()

    async def _on_session_exit(self, session_id: str):
        """Called when a session's process exits. Removes the session."""
        session = self.sessions.pop(session_id, None)
        if session:
            self._delete_metadata(session_id)

    async def create(self, name: str, command: str, cwd: str | None = None) -> Session:
        if name in self.sessions:
            existing = self.sessions[name]
            if existing.status == "running":
                raise ValueError(f"Session '{name}' already exists and is running")
            else:
                await self.remove(name)

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

    def get(self, session_id: str) -> Optional[Session]:
        return self.sessions.get(session_id)

    def list_all(self) -> list[dict]:
        return [s.to_dict() for s in self.sessions.values()]

    async def remove(self, session_id: str):
        session = self.sessions.pop(session_id, None)
        if session:
            await session.kill()
            await session.cleanup()
            self._delete_metadata(session_id)

    def _save_metadata(self, session: Session):
        path = SESSIONS_DIR / f"{session.id}.json"
        path.write_text(json.dumps(session.to_dict(), indent=2))

    def _delete_metadata(self, session_id: str):
        path = SESSIONS_DIR / f"{session_id}.json"
        path.unlink(missing_ok=True)

    async def cleanup_all(self):
        for session_id in list(self.sessions.keys()):
            await self.remove(session_id)
