# ♭ conductor

Local orchestration layer that manages interactive terminal processes and exposes them through a web dashboard. Start Claude Code sessions on your workstation, then monitor and interact with them from your phone over Tailscale.

## The Idea

You start a few Claude Code sessions on your workstation. You walk away. On the couch, you pull out your phone, open the dashboard, and keep prompting. Sessions survive disconnects — close the browser, reopen it later, everything is still there.

```
You at your desk                          You on the couch
─────────────────                         ──────────────────
conductor run claude research             Open phone browser
conductor run claude coding               → http://my-machine:7777

Leave your desk.                          Select "research"
                                          Send a prompt
Come back later.                          Switch to "coding"
Everything still running.                 Close phone. Reconnect anytime.
```

## Setup

### 1. Clone and install

```bash
git clone git@github.com:xohm/conductor.git
cd conductor
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Make it available everywhere

After `pip install -e .`, the `conductor` command is inside `.venv/bin/`. To use it from any terminal without activating the venv, add it to your PATH.

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/path/to/conductor/.venv/bin:$PATH"
```

Then reload:

```bash
source ~/.bashrc  # or ~/.zshrc
```

Now you can run `conductor` from any terminal.

### 3. Start sessions

```bash
# Start one session (server auto-starts in background)
conductor run claude research

# Start more
conductor run claude coding
conductor run claude review
```

That's it. Open `http://127.0.0.1:7777` in your browser.

## Remote Access from Phone/Tablet (Tailscale)

This is the main use case — run sessions on your workstation, interact from your phone on the couch.

### What you need

- [Tailscale](https://tailscale.com/) installed on your workstation and your phone/tablet
- Both devices on the same Tailnet (just sign in with the same account)

### Steps

**1. Start Conductor on your workstation** (if not already running):

```bash
conductor run claude research
```

**2. Find your machine's Tailscale name:**

```bash
tailscale status
# 100.64.0.1    my-machine    linux   -
```

**3. Open on your phone/tablet:**

Option A — run `conductor qr` to show a QR code in the terminal and open a clean SVG in the browser:

```
$ conductor qr
```

Option B — use the dashboard's **Link Device** feature (hamburger menu → Link Device).

Option C — type the URL:

```
http://my-machine:7777
```

Done. You have full terminal access to all your running sessions. Type prompts, view output, create new sessions, kill old ones — all from your phone.

### Why this works

Tailscale creates a private network between your devices using WireGuard. Only your devices can reach the server. No ports exposed to the internet, no passwords, no setup beyond installing Tailscale. Conductor binds to `0.0.0.0` so it's reachable on your Tailscale network without any extra configuration.

## Dashboard

The web dashboard at `http://127.0.0.1:7777` provides:

- **Session sidebar** — all sessions with live status, focus tracking
- **Terminal panels** — full xterm.js rendering with colors, cursor, scrollback
- **Split view** — horizontal or vertical, with draggable divider
- **Keyboard input** — type directly into the terminal
- **New session** — create sessions from the browser with directory picker
- **Kill confirmation** — stop sessions with a confirmation dialog
- **Color themes** — 6 presets per panel: Default, Dark, Mid, Bright, Bernstein, Green (retro CRT)
- **Font size controls** — per-panel `+` / `−` buttons, adaptive defaults for desktop and mobile
- **Idle notifications** — browser notification when a session is waiting for input (when tab not visible)
- **Link Device** — QR code in the hamburger menu for opening the dashboard on another device
- **Collapsible sidebar** — chevron toggle, auto-reopens when all panels close
- **Auto-reconnect** — WebSocket reconnects automatically on disconnect
- **Minimum 80 columns** — narrow panels get horizontal scroll instead of reflow
- **Mobile-friendly** — responsive drawer, touch targets, dynamic viewport height

## CLI Reference

| Command | Description |
|---|---|
| `conductor serve` | Start the server (foreground) |
| `conductor serve --host 0.0.0.0 --port 8888` | Custom host/port |
| `conductor run COMMAND [NAME]` | Start a managed session |
| `conductor list` | List active sessions |
| `conductor stop NAME` | Stop a session |
| `conductor open` | Open the dashboard in the default browser |
| `conductor qr` | Show QR code (terminal + opens SVG in browser) |

`conductor run` auto-starts the server as a background daemon if it isn't already running. If no name is given, the command name is used.

## API

All endpoints on `127.0.0.1:7777`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/sessions` | List all sessions |
| `POST` | `/sessions/run` | Create session (`{"name": "...", "command": "..."}`) |
| `POST` | `/sessions/{id}/input` | Send input (`{"text": "..."}`) |
| `POST` | `/sessions/{id}/resize` | Resize PTY (`{"rows": 24, "cols": 80}`) |
| `DELETE` | `/sessions/{id}` | Kill session |
| `WS` | `/sessions/{id}/stream` | Bidirectional WebSocket — output out, keystrokes in |

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

Each process is wrapped in a PTY. Output goes into a rolling in-memory buffer (~1MB). When a browser connects, it gets the full buffer first, then live output streams over WebSocket. Sessions survive browser disconnects — reconnect and pick up where you left off.

## Project Structure

```
conductor/
├── conductor/
│   ├── server/app.py        # FastAPI app + static serving
│   ├── api/routes.py         # REST + WebSocket endpoints
│   ├── sessions/
│   │   ├── session.py        # Session — PTY, buffer, subscribers
│   │   └── registry.py       # In-memory session registry
│   ├── proxy/pty_wrapper.py  # PTY spawn and I/O
│   └── utils/config.py       # Paths, ports, allowed commands
├── cli/main.py               # Click CLI
├── static/index.html          # Dashboard (single-file HTML/JS/CSS)
├── main.py                    # Entry point
├── pyproject.toml
└── LICENSE                    # MIT
```

## Requirements

- Python 3.10+
- Linux or macOS (PTY required)
- Dependencies: FastAPI, uvicorn, click, httpx, websockets, qrcode
