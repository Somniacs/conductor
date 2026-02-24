import asyncio
import os
import shlex
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from conductor.sessions.registry import SessionRegistry
from conductor.utils.config import ALLOWED_COMMANDS, DEFAULT_DIRECTORIES

router = APIRouter()
registry = SessionRegistry()

# Build set of allowed base commands for fast lookup
_allowed_commands = {shlex.split(c["command"])[0] for c in ALLOWED_COMMANDS}


class RunRequest(BaseModel):
    name: str
    command: str
    cwd: str | None = None
    source: str | None = None  # "cli" bypasses whitelist; dashboard is restricted


class InputRequest(BaseModel):
    text: str


class ResizeRequest(BaseModel):
    rows: int
    cols: int


@router.get("/config")
async def get_config():
    """Return allowed commands and directories for the dashboard."""
    return {
        "allowed_commands": ALLOWED_COMMANDS,
        "default_directories": DEFAULT_DIRECTORIES,
    }


@router.get("/browse")
async def browse_directory(path: str = "~"):
    """List subdirectories of a given path for the directory picker."""
    try:
        resolved = Path(path).expanduser().resolve()
        if not resolved.is_dir():
            raise HTTPException(status_code=400, detail="Not a directory")

        dirs = []
        try:
            for entry in sorted(resolved.iterdir()):
                if entry.name.startswith("."):
                    continue
                if entry.is_dir():
                    dirs.append({"name": entry.name, "path": str(entry)})
        except PermissionError:
            pass

        return {
            "current": str(resolved),
            "parent": str(resolved.parent) if resolved != resolved.parent else None,
            "directories": dirs,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    return registry.list_all()


@router.post("/sessions/run")
async def create_session(req: RunRequest):
    # Validate command against whitelist (CLI is unrestricted, dashboard is restricted)
    if req.source != "cli":
        try:
            base_cmd = shlex.split(req.command)[0]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid command")

        if base_cmd not in _allowed_commands:
            raise HTTPException(
                status_code=403,
                detail=f"Command '{base_cmd}' is not allowed. Permitted: {', '.join(sorted(_allowed_commands))}",
            )

    try:
        session = await registry.create(req.name, req.command, cwd=req.cwd)
        return session.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"Command not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/input")
async def send_input(session_id: str, req: InputRequest):
    session = registry.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.send_input(req.text)
    return {"status": "ok"}


@router.post("/sessions/{session_id}/resize")
async def resize_session(session_id: str, req: ResizeRequest):
    session = registry.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.resize(req.rows, req.cols)
    return {"status": "ok"}


@router.delete("/sessions/{session_id}")
async def kill_session(session_id: str):
    session = registry.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await registry.remove(session_id)
    return {"status": "killed"}


@router.websocket("/sessions/{session_id}/stream")
async def stream_session(ws: WebSocket, session_id: str):
    session = registry.get(session_id)
    if not session:
        await ws.close(code=4004, reason="Session not found")
        return

    await ws.accept()

    # Send buffered output first
    buffer = session.get_buffer()
    if buffer:
        await ws.send_bytes(buffer)

    queue = session.subscribe()

    async def writer():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    if data is None:
                        # Session ended — close WebSocket
                        await ws.close()
                        break
                    await ws.send_bytes(data)
                except asyncio.TimeoutError:
                    # Keepalive
                    try:
                        await ws.send_bytes(b"")
                    except Exception:
                        break
        except Exception:
            pass

    async def reader():
        try:
            while True:
                message = await ws.receive()
                if message["type"] == "websocket.disconnect":
                    break
                text = message.get("text")
                raw = message.get("bytes")
                if text:
                    session.send_input(text)
                elif raw:
                    session.send_input_bytes(raw)
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    writer_task = asyncio.create_task(writer())
    reader_task = asyncio.create_task(reader())

    try:
        done, pending = await asyncio.wait(
            {writer_task, reader_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        session.unsubscribe(queue)
