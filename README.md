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

## Prerequisites

- **Python 3.10+** — check with `python3 --version`
- **Git** — to clone the repository
- **Tailscale** (optional, for remote access) — install on your workstation and your phone/tablet, sign in with the same account on both. See [tailscale.com](https://tailscale.com/)

## Install

### Option A — From release (recommended)

Download the latest release from GitHub, extract, and run the install script:

```bash
# Download and extract
curl -sL https://github.com/somniacs/conductor/releases/latest/download/conductor.tar.gz | tar xz
cd conductor
./install.sh
```

Or download manually from the [Releases](https://github.com/somniacs/conductor/releases) page, extract the archive, and run `./install.sh` inside.

### Option B — From source

```bash
git clone https://github.com/somniacs/conductor.git
cd conductor
./install.sh
```

The install script checks for Python 3.10+, installs [pipx](https://pipx.pypa.io/) if needed, and installs Conductor system-wide. After it finishes, the `conductor` command is available globally from any terminal.

If the command is not found after install, restart your terminal or run `source ~/.bashrc` (or `~/.zshrc`).

<details>
<summary>Manual install (without install script)</summary>

```bash
git clone https://github.com/somniacs/conductor.git
cd conductor
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This puts `conductor` inside `.venv/bin/`. You need to activate the venv each time, or add it to your PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/path/to/conductor/.venv/bin:$PATH"
```

</details>

## Usage

### Start sessions

```bash
# Start one session (server auto-starts in background)
conductor run claude research

# Start more
conductor run claude coding
conductor run claude review
```

Open `http://127.0.0.1:7777` in your browser. That's it for local use.

### Remote access from phone/tablet

This requires Tailscale on both your workstation and your phone/tablet (see Prerequisites).

**1. Start Conductor on your workstation** (if not already running):

```bash
conductor run claude research
```

**2. Open on your phone/tablet:**

Option A — run `conductor qr` to show a scannable QR code:

```bash
conductor qr
```

Option B — use the dashboard's **Link Device** feature (hamburger menu → Link Device).

Option C — find your Tailscale hostname and type the URL:

```bash
tailscale status
# 100.64.0.1    my-machine    linux   -
```

Then open `http://my-machine:7777` on your phone.

Done. Full terminal access to all sessions from your phone — type prompts, view output, create or kill sessions.

### Why remote access works

Tailscale creates a private network between your devices using WireGuard. Only your devices can reach the server. No ports exposed to the internet, no passwords, no setup beyond installing Tailscale. Conductor binds to `0.0.0.0` so it's reachable on your Tailscale network without any extra configuration.

## Is It Safe?

Yes. Conductor runs entirely on your machine and does not phone home, create accounts, or expose anything to the public internet.

- **Local only** — the server binds to your machine. Without Tailscale (or another VPN), it is not reachable from outside your local network.
- **No authentication layer needed** — when using Tailscale, only devices signed into *your* Tailscale account can reach the server. The network itself is the firewall.
- **No data leaves your machine** — session output stays in an in-memory buffer on localhost. Nothing is logged to external services.
- **Restricted dashboard commands** — the web dashboard can only launch commands from a predefined allowlist (`config.py`). The CLI is unrestricted, but the browser cannot start arbitrary processes.
- **No shell injection** — session input is sent through the PTY as keystrokes, not evaluated as shell commands by Conductor itself.
- **Sanitized session names** — names are validated against a strict allowlist (alphanumeric, hyphens, underscores, max 64 chars) on both the frontend and backend to prevent path traversal or injection via crafted names.
- **Open source (MIT)** — the entire codebase is a single Python package and a single HTML file. Read it, audit it, fork it.

If you're running Conductor on a shared network without Tailscale, anyone on that network can reach port 7777. In that case, use a firewall rule or bind to `127.0.0.1` instead of `0.0.0.0`.

## Dashboard

The web dashboard at `http://127.0.0.1:7777` provides:

- **Session sidebar** — all sessions with live status, focus tracking
- **Terminal panels** — full xterm.js rendering with colors, cursor, scrollback
- **Split view** — place panels Left, Right, Top, or Bottom with arbitrary nesting and draggable dividers
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
| `conductor run COMMAND [NAME]` | Start session and attach (see output in terminal) |
| `conductor run -d COMMAND [NAME]` | Start session in background (detached) |
| `conductor attach NAME` | Attach to a running session |
| `conductor list` | List active sessions |
| `conductor stop NAME` | Stop a session |
| `conductor restart` | Restart the server (picks up config changes) |
| `conductor open` | Open the dashboard in the default browser |
| `conductor qr` | Show QR code (terminal + opens SVG in browser) |

`conductor run` auto-starts the server as a background daemon if it isn't already running. If no name is given, the command name is used. Press `Ctrl+]` to detach from a session without stopping it.

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
├── install.sh                 # One-step installer (pipx)
├── pyproject.toml
└── LICENSE                    # MIT
```

## Platform Support

| Platform | Status |
|---|---|
| Linux | Supported |
| macOS | Supported — [setup guide](docs/MACOS.md) |
| Windows | Not yet — [roadmap & WSL workaround](docs/WINDOWS.md) |

## Requirements

- Python 3.10+
- Linux or macOS (PTY required)
- Dependencies: FastAPI, uvicorn, click, httpx, websockets, qrcode
