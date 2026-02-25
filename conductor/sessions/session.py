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

"""PTY-backed terminal session with buffering and WebSocket broadcast."""

import asyncio
import os
import re
import sys
import threading
import time
from typing import Set

# Regex to strip ANSI escape sequences from terminal output.
_ANSI_RE = re.compile(
    r'\x1b'           # ESC
    r'(?:'
    r'\[[0-9;]*[a-zA-Z]'   # CSI sequences  (e.g. \e[31m)
    r'|\][^\x07]*\x07'     # OSC sequences  (e.g. \e]0;title\a)
    r'|[()][AB012]'        # charset select
    r'|[>=<]'              # keypad modes
    r'|#[0-9]'             # line attrs
    r'|.'                  # two-char sequences
    r')'
)

# Pattern to find `--resume <id>` in Claude Code exit output.
_RESUME_RE = re.compile(r'--resume\s+(\S+)')

from conductor.proxy.pty_wrapper import PTYProcess
from conductor.utils.config import BUFFER_MAX_BYTES

_IS_WIN = sys.platform == "win32"


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
        self.resume_id: str | None = None
        self._monitor_task: asyncio.Task | None = None
        self._on_exit = on_exit
        self._reader_thread: threading.Thread | None = None

    async def start(self):
        self.pty.spawn()
        self.pid = self.pty.pid
        self.start_time = time.time()
        self.status = "running"

        if _IS_WIN:
            # Windows: ConPTY doesn't expose a file descriptor, so we
            # read in a background thread and push data to the event loop.
            self._loop = asyncio.get_event_loop()
            self._reader_thread = threading.Thread(
                target=self._win_read_loop, daemon=True
            )
            self._reader_thread.start()
        else:
            # Unix: register the PTY master fd with the event loop.
            loop = asyncio.get_event_loop()
            loop.add_reader(self.pty.master_fd, self._on_readable)

        self._monitor_task = asyncio.create_task(self._monitor_process())

    # -- Unix reader (event-loop based) ------------------------------------

    def _on_readable(self):
        try:
            data = os.read(self.pty.master_fd, 65536)
            if data:
                self._append_buffer(data)
                self._broadcast(data)
        except OSError:
            pass

    # -- Windows reader (thread-based) -------------------------------------

    def _win_read_loop(self):
        """Background thread that reads from ConPTY and feeds the event loop."""
        while not self.pty.closed:
            try:
                data = self.pty.read()
                if data:
                    self._loop.call_soon_threadsafe(self._append_buffer, data)
                    self._loop.call_soon_threadsafe(self._broadcast, data)
                else:
                    time.sleep(0.01)
            except OSError:
                break
            except Exception:
                break

    # -- Buffer & broadcast ------------------------------------------------

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

    def _extract_resume_id(self):
        """Scan the tail of the terminal buffer for a --resume <id> token."""
        try:
            # Only inspect the last 4 KB — the resume line is near the end.
            tail = bytes(self.buffer[-4096:]).decode("utf-8", errors="replace")
            clean = _ANSI_RE.sub("", tail)
            match = _RESUME_RE.search(clean)
            if match:
                self.resume_id = match.group(1)
        except Exception:
            pass

    async def _monitor_process(self):
        while self.pty.poll() is None:
            await asyncio.sleep(0.5)
        self.status = "exited"

        if not _IS_WIN:
            try:
                asyncio.get_event_loop().remove_reader(self.pty.master_fd)
            except Exception:
                pass

        self._extract_resume_id()
        self._broadcast(b"\r\n[Process exited]\r\n")
        self._broadcast_close()
        self.pty.close()
        if self._on_exit:
            await self._on_exit(self.id)

    async def kill(self):
        self.pty.kill()
        self.status = "killed"

        if not _IS_WIN:
            try:
                asyncio.get_event_loop().remove_reader(self.pty.master_fd)
            except Exception:
                pass

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
        d = {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "status": self.status,
            "pid": self.pid,
            "start_time": self.start_time,
            "cwd": self.cwd,
        }
        if self.resume_id:
            d["resume_id"] = self.resume_id
        return d
