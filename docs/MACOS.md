# macOS Setup

Conductor runs natively on macOS. No extra dependencies beyond Python.

## Install

```bash
git clone git@github.com:xohm/conductor.git
cd conductor
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Make it available system-wide

Add to your `~/.zshrc`:

```bash
export PATH="$HOME/path/to/conductor/.venv/bin:$PATH"
```

Then reload:

```bash
source ~/.zshrc
```

## Start sessions

```bash
conductor run claude research
conductor run claude coding
```

Open `http://127.0.0.1:7777` in Safari or any browser.

## Remote access from iPhone/iPad

1. Install [Tailscale](https://apps.apple.com/app/tailscale/id1470499037) on your Mac and iOS device
2. Sign in with the same account on both
3. Run `conductor qr` to get a scannable QR code
4. Or use the dashboard's **Link Device** feature (hamburger menu)

## Notes

- macOS uses the same PTY (pseudo-terminal) system as Linux — full compatibility
- Tested on macOS 13+ (Ventura) with Python 3.10+
- The `conductor` daemon runs in the background after `conductor run`
- Sessions survive terminal and browser disconnects
