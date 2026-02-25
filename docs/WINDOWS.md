# Windows Support

**Status: Supported** (Windows 10 Build 1809+ / Windows 11)

Conductor runs natively on Windows using [ConPTY](https://devblogs.microsoft.com/commandline/windows-command-line-introducing-the-windows-pseudo-console-conpty/) (Windows Pseudo Console) via the [`pywinpty`](https://pypi.org/project/pywinpty/) library.

## Prerequisites

- **Windows 10 Build 1809+** or Windows 11 — ConPTY is required
- **Python 3.10+** — download from [python.org](https://python.org). Check "Add Python to PATH" during install
- **Git** — download from [git-scm.com](https://git-scm.com/download/win)

To check your Windows build: press `Win+R`, type `winver`, press Enter.

To check Python: open PowerShell and run `python --version` or `py --version`.

## Install

### Option A — From release (recommended)

```powershell
# Download and extract
Invoke-WebRequest https://github.com/somniacs/conductor/releases/latest/download/conductor.zip -OutFile conductor.zip
Expand-Archive conductor.zip -DestinationPath .
cd conductor
powershell -ExecutionPolicy Bypass -File install.ps1
```

Or download manually from the [latest release](https://github.com/somniacs/conductor/releases/latest).

### Option B — From source

```powershell
git clone https://github.com/somniacs/conductor.git
cd conductor
powershell -ExecutionPolicy Bypass -File install.ps1
```

The install script checks for Python 3.10+, installs [pipx](https://pipx.pypa.io/) if needed, and installs Conductor system-wide. After it finishes, the `conductor` command is available from any terminal.

If the command is not found after install, restart your terminal.

### Manual install (without install script)

```powershell
git clone https://github.com/somniacs/conductor.git
cd conductor
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Usage

Works the same as Linux/macOS:

```powershell
conductor run <agent> research
conductor run <agent> coding
conductor list
conductor open
```

Open `http://127.0.0.1:7777` in your browser for the dashboard.

### Attach / Detach

- `conductor run <agent> research` — starts and attaches (you see output in your terminal)
- Press `Ctrl+]` to detach without stopping the session
- `conductor attach research` — reattach later
- `conductor run -d <agent> coding` — start detached (background)

## Remote access from another device

1. Install [Tailscale](https://tailscale.com/download/windows) on your Windows machine and your phone, tablet, or laptop
2. Sign in with the same account on all devices
3. Run `conductor qr` to get a scannable QR code — or open the dashboard's **Servers** dialog (hamburger menu → Servers) to discover Tailscale devices automatically

## Multi-machine setup

To monitor sessions from multiple machines (Windows, Linux, Mac — any mix):

1. Install and start Conductor on each machine
2. Open the dashboard on any device
3. Add machines via the **Servers** dialog — Tailscale device picker, manual URL, or QR scan

All machines appear in a single sidebar, grouped by machine. Open terminals from different machines side by side in split view.

## How it works on Windows

| Component | Implementation |
|-----------|---------------|
| PTY | ConPTY via `pywinpty` |
| Terminal sizing | `pywinpty` resize API |
| Process management | `CREATE_NEW_PROCESS_GROUP` + `taskkill /F /T` |
| Async I/O | Thread-based reader with `call_soon_threadsafe()` |
| CLI attach | `msvcrt` for console I/O |

The `pywinpty` dependency is installed automatically (it's a conditional dependency that only activates on Windows).

## Troubleshooting

### "pywinpty not found" or import error

Make sure you have Python 3.10+ and pip is up to date:

```powershell
python -m pip install --upgrade pip
pip install pywinpty
```

### ConPTY not available

ConPTY requires Windows 10 Build 1809 or later. Check your build with `winver`. If you're on an older build, use the WSL workaround below.

### Terminal output looks garbled

Make sure you're using Windows Terminal, PowerShell, or cmd.exe. Some third-party terminals may not fully support ConPTY escape sequences.

## WSL alternative

If you prefer, you can also run Conductor inside WSL (Windows Subsystem for Linux):

```bash
# Inside WSL
git clone https://github.com/somniacs/conductor.git
cd conductor
./install.sh
conductor run <agent> research
```

Then open `http://localhost:7777` in your Windows browser. WSL provides full Unix PTY support.
