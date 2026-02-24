import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from conductor.sessions.registry import SessionRegistry

router = APIRouter()
registry = SessionRegistry()


class RunRequest(BaseModel):
    name: str
    command: str


class InputRequest(BaseModel):
    text: str


class ResizeRequest(BaseModel):
    rows: int
    cols: int


@router.get("/sessions")
async def list_sessions():
    return registry.list_all()


@router.post("/sessions/run")
async def create_session(req: RunRequest):
    try:
        session = await registry.create(req.name, req.command)
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
