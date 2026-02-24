# ☉ Conductor

Local orchestration layer that manages interactive terminal processes and exposes them through a web dashboard for observation and remote input.

Start Claude Code sessions, training scripts, or any long-running process on your workstation — then monitor and interact with them from your phone over Tailscale. Walk away from the desk, pull out your phone, and keep prompting.

## The Workflow

```
You at your desk                          You on the couch
─────────────────                         ──────────────────
conductor run claude research             Open phone browser
conductor run claude coding               → http://mycomputer:7777
conductor run "python train.py" training
                                          Select "research"
Leave your desk.                          Send a prompt
                                          Check "training" progress
                                          Switch to "coding"
Come back later.
Everything still running.                 Close phone. Reconnect anytime.
```

## How It Works

```
Terminal Process
      │
  PTY Wrapper          ← each process gets its own pseudo-terminal
      │
 Conductor Session     ← captures output, accepts input, survives disconnects
      │
┌──────────────────┐
│ Conductor Server │   ← 127.0.0.1:7777
└──────────────────┘
      │
  WebSocket API        ← bidirectional: output streams out, keystrokes stream in
      │
 Browser Dashboard     ← phone, tablet, laptop — anything on your Tailscale network
```

Conductor wraps each process in a pseudo-terminal (PTY), captures all output into a rolling buffer, and streams it over WebSocket to any connected browser. Sessions survive browser disconnects — reconnect anytime and pick up where you left off.

## Quick Start

### Install

```bash
git clone git@github.com:xohm/conductor.git
cd conductor
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run

```bash
# Start the server
conductor serve

# In another terminal — start sessions
conductor run claude research
conductor run claude coding
conductor run "python train.py" training

# Open the dashboard
open http://127.0.0.1:7777
```

## Tailscale Setup (Remote Access from Phone)

This is the primary use case — run Claude sessions on your workstation, interact with them from anywhere on your Tailscale network.

### Prerequisites

- [Tailscale](https://tailscale.com/) installed on your workstation and your phone
- Both devices on the same Tailnet

### 1. Start Conductor on your workstation

```bash
conductor serve
```

### 2. Find your Tailscale hostname

```bash
tailscale status
# Example output:
# 100.64.0.1    solos-gpu    linux   -
```

### 3. Open on your phone

Open Safari/Chrome on your phone and go to:

```
http://solos-gpu:7777
```

That's it. You now have full terminal access to all your running sessions from your phone.

### What you can do from your phone

- **See all running sessions** in the sidebar
- **Tap a session** to view its live terminal output
- **Type prompts** into Claude sessions using the input bar
- **Split-view** multiple sessions side by side
- **Create new sessions** directly from the dashboard
- **Kill sessions** you no longer need
- **Walk away and come back** — sessions keep running, reconnect picks up the full buffer

### Example: Claude on your GPU box

```bash
# On your workstation
conductor run claude research
conductor run claude "write me a web scraper"
conductor run "python long_training.py" training

# On your phone (over Tailscale)
# → http://solos-gpu:7777
# Select "research", send: "summarize the latest papers on diffusion models"
# Switch to "training", check progress
# Go to bed. Check again in the morning.
```

### Security

Tailscale handles everything. Only devices on your Tailnet can reach the server — authenticated by device identity, encrypted end-to-end via WireGuard. No passwords needed, no ports exposed to the internet.

Conductor binds to `127.0.0.1` by default. Tailscale makes it reachable to your other devices without opening any firewall ports.

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
- **Secure by default** — localhost only, Tailscale for remote access (no extra auth needed)
- **Minimal dependencies** — standard Python + FastAPI
