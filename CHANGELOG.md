# Changelog

All notable changes to Conductor are documented here.

## v0.3.5

### New features

- **Tablet support** — touch scrolling, extra-keys bar, and custom scrollbars now work on tablets (previously only activated below 700px width); uses `pointer: coarse` media query to detect touch devices without affecting touchscreen laptops
- **Keyboard-aware extra keys** — extra-keys bar appears when the virtual keyboard opens and positions itself above it, including on tablets in desktop browser mode (uses the Visual Viewport API with focusin fallback)
- **Maximize panel** — double-click a session title bar to maximize that panel; double-click again or click any session in the sidebar to restore the split layout
- **Open panel indicators** — sessions placed in the view show a highlighted left border in the sidebar, so you can tell which sessions are open vs unplaced

### Fixes

- Extra-keys drawer expand/collapse now correctly resizes the terminal in all modes
- Body height properly accounts for extra-keys bar when the keyboard is open in desktop browser mode

## v0.3.4

### New features

- **Smooth native scrolling** — one-finger scrolling on mobile is now hardware-accelerated with native momentum, replacing the custom JavaScript scroll handler for dramatically lower latency
- **Focused panel on mobile** — when the keyboard opens with multiple panels, only the active panel is shown at full size; the split layout restores when the keyboard closes
- **Compact extra keys** — reduced vertical size of the mobile extra-keys bar so more terminal content is visible

### Fixes

- Mobile terminal no longer shifts upward after scrolling
- Faster reconnection on mobile (reduced from 2s to 500ms)

## v0.3.3

### New features

- **Combined touch scroll** — vertical and horizontal scrolling work simultaneously on mobile with momentum on both axes; no direction locking
- **Horizontal scrollbar** — scroll indicator at the bottom of the terminal shows when content is wider than the panel
- **Sidebar version** — current version shown next to the title in the sidebar
- **Tap to scroll** — tapping the terminal on mobile scrolls to the cursor position
- **Shift modifier** — Shift button (⇧) on the mobile extra-keys bar enables Shift+Tab, Shift+Arrow, and other modified key sequences (useful for edit mode in Claude/Codex)
- **Extra-keys layout** — added pipe (|) key; Tab and Shift use Unicode symbols (⇥/⇧); ↑ and ↓ arrows are vertically aligned across rows

### Fixes

- `conductor run` now sends the caller's working directory to the server, so sessions start in the correct directory instead of the server's cwd
- Mobile sidebar drawer now closes when creating or resuming a session (previously only closed when opening an existing one)
- Extra-keys drawer toggle now works reliably on mobile after collapsing
- Custom scrollbar drag now works on mobile (was mouse-only; added touch event support)
- Extra-keys drawer no longer overlaps terminal content; terminal resizes to fit above keyboard and drawer
- Vertical touch scroll now works reliably when the virtual keyboard is open
- Horizontal scrollbar now updates immediately after terminal resize instead of waiting up to 500ms
- Terminal now resizes correctly when the mobile keyboard opens — switched to `interactive-widget=resizes-content` so the layout viewport shrinks with the keyboard; title bar stays visible, scrollbars stay within bounds
- Drag-and-drop overlay no longer triggers on internal element drags (only activates for external file drops)
- One-finger touch scroll is now immediate (removed rAF batching that added a frame of input latency); two-finger gestures no longer cause scroll position to jump back on release

## v0.3.2

- **Update notification** — the dashboard checks GitHub for new releases on load and shows a subtle banner at the bottom of the sidebar when an update is available; click to open the release page
- **Reconnect spinner** — the "Server disconnected" status bar now shows a spinning indicator instead of static text
- **Codex resume support** — Codex sessions are always resumable; clicking the play button runs `codex resume`. Added `codex --full-auto` variant with `codex resume --last`
- **Copilot resume support** — GitHub Copilot CLI sessions are always resumable via `copilot --resume` (picker) or `copilot --continue` (most recent). Command changed from `gh copilot` to `copilot` (standalone binary). Added `copilot --allow-all-tools` variant
- **Command-based resume** — new `resume_command` field for agents that manage their own session history (no token extraction needed); used by Codex and Copilot
- **Graceful stop improvements** — SIGINT-first kill prevents Node runtime crashes (Codex); reduced stop sequence delay from 2s to 1s; Copilot uses direct SIGINT instead of PTY text commands for instant shutdown
- **Orphan panel cleanup** — terminal panels are automatically closed when their session disappears from the server
- **Settings reset** — "Reset to defaults" button in the Settings dialog restores built-in command list, directories, and all other settings
- **Unified versioning** — version defined in one place (`pyproject.toml`); backend reads via `importlib.metadata`, frontend fetches from `/info`

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
