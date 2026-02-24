# ☉ Conductor

Local orchestration layer that manages interactive terminal processes and exposes them through a web dashboard for observation and remote input.

Start an AI agent, a training script, or any long-running process — then monitor and interact with it from your phone, tablet, or any browser on your network.

## How It Works

```
Terminal Process
      │
  PTY Wrapper
      │
 Conductor Session
      │
┌──────────────────┐
│ Conductor Server │  ← 127.0.0.1:7777
└──────────────────┘
      │
  WebSocket API
      │
 Browser Dashboard
```

Conductor wraps each process in a pseudo-terminal (PTY), captures all output into a rolling buffer, and streams it over WebSocket to any connected browser. Sessions survive browser disconnects — reconnect anytime and pick up where you left off.

## Quick Start

### Install

```bash
# Clone
git clone git@github.com:xohm/conductor.git
cd conductor

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### Run

```bash
# Start the server
conductor serve

# In another terminal — start a session
conductor run bash myshell
conductor run claude research
conductor run "python train.py" training

# Open the dashboard
open http://127.0.0.1:7777
```

## CLI Reference

| Command | Description |
|---|---|
| `conductor serve` | Start the server (foreground) |
| `conductor serve --host 0.0.0.0 --port 8888` | Bind to custom host/port |
| `conductor run COMMAND [NAME]` | Run a command as a managed session |
| `conductor list` | List all active sessions |
| `conductor stop NAME` | Stop a session |

**`conductor run` auto-starts the server** as a background daemon if it isn't already running.

If no `NAME` is given, the command name is used as the session name.

## Dashboard

The web dashboard at `http://127.0.0.1:7777` provides:

- **Session sidebar** — see all sessions with live status
- **Terminal panels** — full xterm.js terminal rendering with colors and cursor support
- **Split view** — view 1, 2, or 4 sessions simultaneously (CSS grid)
- **Input** — type directly into the terminal or use the input bar
- **New session** — create sessions from the browser
- **Auto-reconnect** — WebSocket reconnects automatically on disconnect

## API

All endpoints are on `127.0.0.1:7777`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all sessions |
| `POST` | `/sessions/run` | Create a session (`{"name": "...", "command": "..."}`) |
| `POST` | `/sessions/{id}/input` | Send input (`{"text": "..."}`) |
| `POST` | `/sessions/{id}/resize` | Resize terminal (`{"rows": 24, "cols": 80}`) |
| `DELETE` | `/sessions/{id}` | Kill a session |
| `WS` | `/sessions/{id}/stream` | Bidirectional WebSocket — receive output, send keystrokes |

### WebSocket Protocol

Connect to `ws://127.0.0.1:7777/sessions/{id}/stream`:

1. Server immediately sends the output buffer (everything captured so far)
2. Server streams new PTY output as binary frames
3. Client sends text or binary frames — forwarded as stdin to the process

## Remote Access

Conductor binds to `127.0.0.1` only — it is not exposed to the network by default.

For remote access (e.g. from your phone to a GPU box), use [Tailscale](https://tailscale.com/):

1. Install Tailscale on both machines
2. Start Conductor: `conductor serve`
3. On your phone/laptop, open: `http://<tailscale-hostname>:7777`

To bind to all interfaces (use with caution on trusted networks only):

```bash
conductor serve --host 0.0.0.0
```

### Password Protection

Set the `CONDUCTOR_PASSWORD` environment variable to require authentication:

```bash
CONDUCTOR_PASSWORD=mysecret conductor serve
```

API requests must include `Authorization: Bearer mysecret` or `?token=mysecret`.

## Persistence

- Sessions survive browser disconnects and WebSocket drops
- Session metadata is stored in `~/.conductor/sessions/` as JSON files
- Output is kept in a rolling in-memory buffer (~1MB per session)
- Sessions end when their underlying process exits
- Server state resets on restart (no session restore yet)

## Project Structure

```
conductor/
├── conductor/
│   ├── server/app.py        # FastAPI application + static serving
│   ├── api/routes.py         # REST + WebSocket endpoints
│   ├── sessions/
│   │   ├── session.py        # Session class — PTY, buffer, subscribers
│   │   └── registry.py       # In-memory session registry + disk metadata
│   ├── proxy/pty_wrapper.py  # Low-level PTY spawn and I/O
│   └── utils/config.py       # Paths, ports, constants
├── cli/main.py               # Click-based CLI
├── static/index.html          # Web dashboard (HTML + JS + CSS)
├── main.py                    # Entry point
└── pyproject.toml
```

## Requirements

- Python 3.10+
- Linux or macOS (PTY support required)
- Dependencies: FastAPI, uvicorn, click, httpx, websockets

## Build

### Install from source

```bash
pip install -e .
```

### Install dependencies only

```bash
pip install fastapi "uvicorn[standard]" websockets click httpx
python main.py serve
```

### Run without installing

```bash
pip install fastapi "uvicorn[standard]" websockets click httpx
python -m conductor.server.app
```

### Build a distributable package

```bash
pip install build
python -m build
# Produces dist/conductor-0.1.0-py3-none-any.whl
pip install dist/conductor-0.1.0-py3-none-any.whl
```

## Design Principles

- **Local-first** — no cloud, no external services
- **No IDE integration required** — works with any terminal
- **Processes remain normal terminals** — PTY preserves full terminal behavior
- **Browser is a secondary control surface** — not a replacement for your terminal
- **Minimal dependencies** — standard Python + FastAPI
