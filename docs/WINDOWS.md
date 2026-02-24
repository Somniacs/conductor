# Windows Support

**Status: Not yet supported.**

Conductor currently requires Unix PTY (pseudo-terminal), which is not available on Windows. The core architecture relies on `pty`, `fcntl`, and `termios` — all Unix-only modules.

## What would need to change

Windows 10 (build 1809+) introduced **ConPTY** (Windows Pseudo Console), which provides similar functionality to Unix PTY. The Python library [`pywinpty`](https://github.com/annoviko/winpty) provides bindings for it.

### Modules that need replacement

| Current (Unix) | Windows replacement |
|---|---|
| `pty.openpty()` | `winpty.PtyProcess.spawn()` |
| `fcntl.ioctl(fd, TIOCSWINSZ, ...)` | `winpty` resize API |
| `os.setsid` / `os.killpg` | `subprocess.CREATE_NEW_PROCESS_GROUP` + `taskkill` |
| `loop.add_reader(fd)` | Thread-based reader (Windows `asyncio` uses IOCP, not file descriptors) |
| `termios` | Not needed with `winpty` |

### Architecture changes

1. **PTY wrapper** — create a `WindowsPtyWrapper` using `pywinpty` alongside the existing Unix `PtyWrapper`
2. **Async I/O** — replace `loop.add_reader()` with a threaded reader that pushes data into an asyncio queue
3. **Process management** — use `subprocess.CREATE_NEW_PROCESS_GROUP` and `taskkill` instead of Unix process groups
4. **Platform detection** — add `sys.platform` checks to load the right wrapper

### Estimated effort

Medium. The `pywinpty` library handles most of the heavy lifting. The main work is:
- A new `WindowsPtyWrapper` class (~80 lines)
- A threaded async reader (~30 lines)
- Platform-aware factory function to pick the right wrapper
- Testing on Windows

### Dependencies for Windows

```
pywinpty>=2.0
```

### ConPTY references

- [Microsoft: Windows Terminal and ConPTY](https://devblogs.microsoft.com/commandline/windows-command-line-introducing-the-windows-pseudo-console-conpty/)
- [pywinpty on PyPI](https://pypi.org/project/pywinpty/)
- [ConPTY API docs](https://learn.microsoft.com/en-us/windows/console/creating-a-pseudoconsole-session)

## WSL workaround

If you're on Windows and want to use Conductor now, run it inside **WSL** (Windows Subsystem for Linux):

```bash
# Inside WSL
git clone https://github.com/xohm/conductor.git
cd conductor
./install.sh
conductor run claude research
```

Then open `http://localhost:7777` in your Windows browser. WSL provides full Unix PTY support.
