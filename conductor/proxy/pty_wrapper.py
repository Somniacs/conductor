import fcntl
import os
import pty
import shlex
import signal
import struct
import subprocess
import termios


class PTYProcess:
    """Wraps a subprocess in a pseudo-terminal."""

    def __init__(self, command: str):
        self.command = command
        self.master_fd: int = -1
        self.process: subprocess.Popen | None = None
        self.closed = False

    def spawn(self, rows: int = 24, cols: int = 80) -> int:
        master_fd, slave_fd = pty.openpty()

        # Set terminal size
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

        args = shlex.split(self.command)
        env = os.environ.copy()
        env["TERM"] = "xterm-256color"

        # Clean env so spawned processes don't think they're nested
        for key in list(env):
            if key.startswith("CLAUDE"):
                del env[key]

        self.process = subprocess.Popen(
            args,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,
            env=env,
        )

        os.close(slave_fd)
        self.master_fd = master_fd
        os.set_blocking(self.master_fd, False)

        return self.master_fd

    def write(self, data: bytes):
        if self.master_fd >= 0 and not self.closed:
            os.write(self.master_fd, data)

    def resize(self, rows: int, cols: int):
        if self.master_fd >= 0 and not self.closed:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)

    def kill(self):
        if self.process and self.process.poll() is None:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass

    def poll(self) -> int | None:
        if self.process:
            return self.process.poll()
        return None

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                os.close(self.master_fd)
            except OSError:
                pass
            self.kill()

    @property
    def pid(self) -> int | None:
        return self.process.pid if self.process else None
