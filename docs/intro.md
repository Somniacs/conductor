# Quick Start

Control your AI agents from your phone in 5 minutes.

## 1. Set up Tailscale

Tailscale is a free app that creates a private network between your devices. Install it once, and your phone can reach your computer from anywhere.

1. Go to [tailscale.com](https://tailscale.com/) and create a free account
2. Install Tailscale on your computer and sign in
3. Install the Tailscale app on your phone ([iOS](https://apps.apple.com/app/tailscale/id1470499037) / [Android](https://play.google.com/store/apps/details?id=com.tailscale.ipn)) and sign in with the **same account**

That's it. Your devices can now find each other.

## 2. Install Conductor

**Linux / macOS:**

```bash
curl -sL https://github.com/somniacs/conductor/releases/latest/download/conductor.tar.gz | tar xz
cd conductor
./install.sh
```

**Windows** (PowerShell):

```powershell
Invoke-WebRequest https://github.com/somniacs/conductor/releases/latest/download/conductor.zip -OutFile conductor.zip
Expand-Archive conductor.zip -DestinationPath .
cd conductor
powershell -ExecutionPolicy Bypass -File install.ps1
```

The installer handles everything. If it says Python is missing, grab it from [python.org](https://python.org) and run the installer again.

Restart your terminal after install.

## 3. Run an agent

```bash
conductor run claude research
```

Done. The agent is running. Start more if you want:

```bash
conductor run aider backend
conductor run codex feature
```

## 4. Open on your phone

```bash
conductor qr
```

Scan the QR code with your phone. The dashboard opens — all your sessions, live terminal, full control.

Or type the URL directly. Tailscale's [MagicDNS](https://tailscale.com/kb/1081/magicdns) lets you use your computer's name:

```
http://my-laptop:7777
```

Run `tailscale status` to see the name. No IP to remember.

## Quick reference

| Do this | Command |
|---|---|
| Start an agent | `conductor run claude research` |
| Start in background | `conductor run -d claude research` |
| List sessions | `conductor list` |
| Attach to a session | `conductor attach research` |
| Detach without stopping | `Ctrl+]` |
| Open dashboard | `conductor open` |
| QR code for phone | `conductor qr` |
| Stop a session | `conductor stop research` |
| Shut everything down | `conductor shutdown` |
