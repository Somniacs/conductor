import asyncio
import os
import time
from typing import Set

from conductor.proxy.pty_wrapper import PTYProcess
from conductor.utils.config import BUFFER_MAX_BYTES


class Session:
    """A single managed terminal session backed by a PTY."""

    def __init__(self, name: str, command: str, session_id: str | None = None, cwd: str | None = None, on_exit=None):
        self.id = session_id or name
        self.name = name
        self.command = command
        self.cwd = cwd
        self.pty = PTYProcess(command, cwd=cwd)
        self.buffer = bytearray()
        self.subscribers: Set[asyncio.Queue] = set()
        self.status = "starting"
        self.pid: int | None = None
        self.start_time: float | None = None
        self._monitor_task: asyncio.Task | None = None
        self._on_exit = on_exit

    async def start(self):
        self.pty.spawn()
        self.pid = self.pty.pid
        self.start_time = time.time()
        self.status = "running"

        loop = asyncio.get_event_loop()
        loop.add_reader(self.pty.master_fd, self._on_readable)
        self._monitor_task = asyncio.create_task(self._monitor_process())

    def _on_readable(self):
        try:
            data = os.read(self.pty.master_fd, 65536)
            if data:
                self._append_buffer(data)
                self._broadcast(data)
        except OSError:
            pass

    def _append_buffer(self, data: bytes):
        self.buffer.extend(data)
        if len(self.buffer) > BUFFER_MAX_BYTES:
            excess = len(self.buffer) - BUFFER_MAX_BYTES
            del self.buffer[:excess]

    def _broadcast(self, data: bytes):
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(data)
            except asyncio.QueueFull:
                pass

    def _broadcast_close(self):
        """Send None sentinel to all subscribers to signal session end."""
        for queue in list(self.subscribers):
            try:
                queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        self.subscribers.discard(queue)

    def get_buffer(self) -> bytes:
        return bytes(self.buffer)

    def send_input(self, text: str):
        self.pty.write(text.encode())

    def send_input_bytes(self, data: bytes):
        self.pty.write(data)

    def resize(self, rows: int, cols: int):
        self.pty.resize(rows, cols)

    async def _monitor_process(self):
        while self.pty.poll() is None:
            await asyncio.sleep(0.5)
        self.status = "exited"
        try:
            asyncio.get_event_loop().remove_reader(self.pty.master_fd)
        except Exception:
            pass
        self._broadcast(b"\r\n[Process exited]\r\n")
        self._broadcast_close()
        self.pty.close()
        if self._on_exit:
            await self._on_exit(self.id)

    async def kill(self):
        self.pty.kill()
        self.status = "killed"
        try:
            asyncio.get_event_loop().remove_reader(self.pty.master_fd)
        except Exception:
            pass
        # Signal all subscribers to disconnect
        self._broadcast_close()

    async def cleanup(self):
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.pty.close()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "status": self.status,
            "pid": self.pid,
            "start_time": self.start_time,
            "cwd": self.cwd,
        }
