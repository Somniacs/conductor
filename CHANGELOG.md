# Changelog

All notable changes to Conductor are documented here.

## v0.3.2

- **Update notification** — the dashboard checks GitHub for new releases on load and shows a subtle banner at the bottom of the sidebar when an update is available; click to open the release page
- **Reconnect spinner** — the "Server disconnected" status bar now shows a spinning indicator instead of static text

## v0.3.1

- **Admin settings panel** — localhost-only Settings dialog in the web dashboard for managing allowed commands, default directories, buffer size, upload limits, and stop timeout. Changes persist to `~/.conductor/config.yaml` and propagate to all connected clients automatically
- **Admin API** — `GET /admin/settings` and `PUT /admin/settings` endpoints (localhost-only, returns 403 for remote clients)
- **Config file** — settings now stored in `~/.conductor/config.yaml`, loaded at startup, merged over built-in defaults
- **Live config updates** — config version tracking via `X-Config-Version` header; all dashboard clients auto-refresh when settings change
- **Terminal resize fix** — split-view panels now resize without cursor drift or spurious scrollbars; rows always match the visible area while columns match the PTY for correct line wrapping
- **Cursor position fix** — eliminated resize oscillation by reading cell dimensions directly from the xterm renderer instead of calling `fit()`, so a single resize per layout change keeps the cursor in place
- **Mobile touch scroll** — direction-locked one-finger scroll (vertical or horizontal) with momentum; `touch-action: none` prevents the browser from hijacking diagonal gestures
- **Mobile horizontal scroll** — wide terminal output scrolls horizontally via the same touch handler when content overflows the panel width
- **Extra-keys modifiers** — Ctrl and Alt buttons on the mobile extra-keys bar now work with virtual keyboard input (e.g. Ctrl+O, Ctrl+C, Alt+F); modifiers auto-clear after each keystroke
- **Extra-keys overlay** — collapsed mobile keys handle overlays the terminal at reduced opacity instead of reserving vertical space
- **Extra-keys positioning** — bar now tracks the visual viewport on mobile so it stays above the keyboard in split-view lower panels instead of jumping to the top of the screen
- **UI contrast** — bumped muted text colors across the dashboard for better readability in sunlight
- **Auth token hint** — Settings dialog shows setup instructions when `CONDUCTOR_TOKEN` is not set
- **Stable Tailscale URLs** — all server connections (Tailscale picker, manual input, QR scanner, QR code dialog, CLI `conductor qr`) now use MagicDNS names instead of bare IPs, so saved servers survive IP changes
- **Tailscale peer names** — devices that report "localhost" as hostname (e.g. Android) now show the MagicDNS device name in the picker instead
- **Robust server shutdown** — `conductor shutdown` now finds the server process via `pgrep` when the PID file is missing
- **CLI `--version` flag** — `conductor --version` prints the current version
- **Auto-start docs** — setup guide for systemd (Linux), launchd (macOS), and Task Scheduler (Windows)
- **CHANGELOG.md** — added changelog with history from v0.1.0
- **README** — table of contents, refined intro and cloud-independence positioning, autostart reference

## v0.3.0

First public release.

- **Web terminal rendering** — custom scrollbar, correct PTY dimensions on buffer replay, full-height terminal panels
- **Graceful stop & resume** — stop sequence support, resume token capture from terminal output, persistent resume across reboots
- **Session creation from dashboard** — pick agent, directory, and target machine; start sessions without a terminal
- **Multi-machine dashboard** — connect to multiple Conductor servers, sessions grouped by machine with status indicators
- **Tailscale device picker** — discover and add machines from your Tailscale network
- **File upload** — paste, drag-and-drop, or attachment button; upload dialog with progress; auto-cleanup on session end
- **Mobile extra keys** — on-screen toolbar (ESC, TAB, arrows, CTRL, ALT, etc.) above the virtual keyboard, with collapsible drawer
- **Mobile touch scroll** — one-finger scroll with momentum in terminal panels
- **Split view** — binary tree panel layout with directional placement and draggable dividers
- **Performance** — async Tailscale lookups, incremental session list rendering, fetch timeouts for offline servers
- **CLI** — `--version` flag, `run` passes initial terminal size to PTY, `attach` syncs terminal dimensions
- **Security** — session name sanitization, command allowlist enforcement, bearer token auth
- **Platform support** — Linux, macOS, Windows 10+ (ConPTY)

## v0.2.1

- Upload dialog for file sharing with sessions
- Mobile extra keys toolbar with persistent expand/collapse state
- One-finger touch scroll with momentum for mobile terminals
- WebSocket auth fix for bearer token middleware

## v0.1.3

- Session resume support — captures resume tokens from terminal output, persists across restarts
- Hostname display for local server in multi-server sidebar

## v0.1.2

- Multi-server dashboard — connect to multiple machines from a single browser
- Tailscale device picker in Servers dialog
- License headers and security hardening
- README rewrite with generic agent examples

## v0.1.1

- Binary tree panel layout with directional placement menu
- Mobile placement menu support
- GitHub org migration (xohm → somniacs)
- Session name sanitization

## v0.1.0

Initial internal release.

- Terminal session management via PTY
- Web dashboard with xterm.js
- CLI for run, attach, list, stop, shutdown
- WebSocket streaming (raw and typed JSON)
- Theme presets, font size controls, idle notifications
- QR code for device linking
- Tailscale remote access
- Install scripts for Linux, macOS, Windows
