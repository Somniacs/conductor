import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import click
import httpx

from conductor.utils.config import BASE_URL, HOST, PORT, PID_FILE, ensure_dirs


def server_running() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/sessions", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def start_server_daemon() -> bool:
    ensure_dirs()
    log_path = Path.home() / ".conductor" / "logs" / "server.log"

    project_root = Path(__file__).parent.parent.resolve()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")

    click.echo(f"  [debug] python: {sys.executable}")
    click.echo(f"  [debug] project_root: {project_root}")
    click.echo(f"  [debug] PYTHONPATH: {env['PYTHONPATH']}")
    click.echo(f"  [debug] log: {log_path}")
    click.echo(f"  [debug] BASE_URL: {BASE_URL}")

    log = log_path.open("a")
    popen_kwargs = dict(
        stdout=log,
        stderr=subprocess.STDOUT,
        cwd=str(project_root),
        env=env,
    )
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True

    cmd = [sys.executable, "-m", "conductor.server.app"]
    click.echo(f"  [debug] cmd: {cmd}")
    proc = subprocess.Popen(cmd, **popen_kwargs)
    click.echo(f"  [debug] daemon pid: {proc.pid}")
    log.close()

    for i in range(20):
        time.sleep(0.25)
        if server_running():
            click.echo(f"  [debug] server responded after {(i+1)*0.25:.1f}s")
            return True
        # Check if process died immediately
        ret = proc.poll()
        if ret is not None:
            click.echo(f"  [debug] daemon exited with code {ret}", err=True)
            # Show last lines of server log
            try:
                tail = log_path.read_text().strip().split("\n")[-20:]
                click.echo("  [debug] server.log tail:", err=True)
                for line in tail:
                    click.echo(f"    {line}", err=True)
            except Exception:
                pass
            return False

    click.echo("  [debug] timeout — server did not respond in 5s", err=True)
    try:
        tail = log_path.read_text().strip().split("\n")[-20:]
        click.echo("  [debug] server.log tail:", err=True)
        for line in tail:
            click.echo(f"    {line}", err=True)
    except Exception:
        pass
    return False


@click.group()
def cli():
    """Conductor - Local orchestration for interactive terminal processes."""


@cli.command()
@click.option("--host", default=HOST, help="Host to bind to")
@click.option("--port", default=PORT, type=int, help="Port to bind to")
def serve(host, port):
    """Start the Conductor server."""
    from conductor.server.app import run_server

    click.echo(f"☉ Conductor server on {host}:{port}")
    click.echo(f"  Dashboard: http://{host}:{port}")
    run_server(host=host, port=port)


@cli.command()
@click.argument("command")
@click.argument("name", required=False)
@click.option("-d", "--detach", is_flag=True, help="Run in background (don't attach to terminal)")
def run(command, name, detach):
    """Run a command in a new Conductor session.

    By default, attaches to the session so you see output in your terminal.
    Use -d/--detach to run in the background.

    Usage: conductor run COMMAND [NAME]

    Examples:
        conductor run claude research
        conductor run -d claude coding
        conductor run "python train.py" training
    """
    if name is None:
        name = command.split()[0]

    if not server_running():
        click.echo("Server not running. Starting daemon...")
        if not start_server_daemon():
            click.echo("Failed to start server. Try: conductor serve", err=True)
            sys.exit(1)
        click.echo(f"Server started on {BASE_URL}")

    r = httpx.post(
        f"{BASE_URL}/sessions/run",
        json={"name": name, "command": command, "source": "cli"},
        timeout=10,
    )

    if r.status_code == 200:
        data = r.json()
        if detach:
            click.echo(f"Session '{data['name']}' started (pid: {data['pid']})")
            click.echo(f"Dashboard: {BASE_URL}")
        else:
            click.echo(f"Session '{data['name']}' started. Attaching... (Ctrl+] to detach)")
            _attach_session(data["name"])
    elif r.status_code == 409:
        click.echo(f"Session '{name}' already exists.", err=True)
        sys.exit(1)
    else:
        click.echo(f"Error: {r.text}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("name")
def attach(name):
    """Attach to a running session.

    Connects your terminal to the session's output and input.
    Press Ctrl+] to detach without stopping the session.
    """
    if not server_running():
        click.echo("Server not running.", err=True)
        sys.exit(1)

    # Verify session exists
    r = httpx.get(f"{BASE_URL}/sessions", timeout=5)
    sessions = {s["name"]: s for s in r.json()}
    if name not in sessions:
        click.echo(f"Session '{name}' not found.", err=True)
        sys.exit(1)

    click.echo(f"Attaching to '{name}'... (Ctrl+] to detach)")
    _attach_session(name)


def _attach_session(session_name: str):
    """Attach terminal to a session via WebSocket."""
    if sys.platform == "win32":
        _attach_session_win(session_name)
    else:
        _attach_session_unix(session_name)


def _attach_session_unix(session_name: str):
    """Unix attach — raw terminal with select-based I/O."""
    import select
    import termios
    import threading
    import tty
    import websockets.sync.client as ws_sync

    ws_url = BASE_URL.replace("http://", "ws://") + f"/sessions/{session_name}/stream"

    stdin_fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(stdin_fd)
    stop = threading.Event()

    wake_r, wake_w = os.pipe()

    def ws_reader(ws):
        try:
            for message in ws:
                if isinstance(message, bytes) and message:
                    sys.stdout.buffer.write(message)
                    sys.stdout.buffer.flush()
                elif isinstance(message, str) and message:
                    sys.stdout.write(message)
                    sys.stdout.flush()
        except Exception:
            pass
        finally:
            stop.set()
            os.write(wake_w, b"\x00")

    try:
        tty.setraw(stdin_fd)
        ws = ws_sync.connect(ws_url)

        reader_thread = threading.Thread(target=ws_reader, args=(ws,), daemon=True)
        reader_thread.start()

        try:
            while not stop.is_set():
                readable, _, _ = select.select([stdin_fd, wake_r], [], [], 1.0)

                if wake_r in readable:
                    break

                if stdin_fd in readable:
                    data = os.read(stdin_fd, 1024)
                    if not data:
                        break
                    if b"\x1d" in data:  # Ctrl+]
                        break
                    try:
                        ws.send(data)
                    except Exception:
                        break
        finally:
            try:
                ws.close()
            except Exception:
                pass
            os.close(wake_r)
            os.close(wake_w)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        click.echo("\nDetached.")


def _attach_session_win(session_name: str):
    """Windows attach — msvcrt-based console I/O with threading."""
    import msvcrt
    import threading
    import websockets.sync.client as ws_sync

    ws_url = BASE_URL.replace("http://", "ws://") + f"/sessions/{session_name}/stream"
    stop = threading.Event()

    def ws_reader(ws):
        try:
            for message in ws:
                if isinstance(message, bytes) and message:
                    sys.stdout.buffer.write(message)
                    sys.stdout.buffer.flush()
                elif isinstance(message, str) and message:
                    sys.stdout.write(message)
                    sys.stdout.flush()
        except Exception:
            pass
        finally:
            stop.set()

    try:
        ws = ws_sync.connect(ws_url)
        reader_thread = threading.Thread(target=ws_reader, args=(ws,), daemon=True)
        reader_thread.start()

        try:
            while not stop.is_set():
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    if ch == "\x1d":  # Ctrl+]
                        break
                    try:
                        ws.send(ch.encode("utf-8"))
                    except Exception:
                        break
                else:
                    stop.wait(timeout=0.05)
        finally:
            try:
                ws.close()
            except Exception:
                pass
    except KeyboardInterrupt:
        pass
    finally:
        click.echo("\nDetached.")


@cli.command("list")
def list_sessions():
    """List all active sessions."""
    if not server_running():
        click.echo("Server not running.", err=True)
        sys.exit(1)

    r = httpx.get(f"{BASE_URL}/sessions", timeout=5)
    sessions = r.json()

    if not sessions:
        click.echo("No sessions.")
        return

    click.echo(f"{'NAME':<20} {'STATUS':<10} {'PID':<10} {'COMMAND'}")
    click.echo("-" * 60)
    for s in sessions:
        click.echo(
            f"{s['name']:<20} {s['status']:<10} {str(s.get('pid', '?')):<10} {s.get('command', '')}"
        )


@cli.command()
@click.argument("name")
def stop(name):
    """Stop a running session."""
    if not server_running():
        click.echo("Server not running.", err=True)
        sys.exit(1)

    r = httpx.delete(f"{BASE_URL}/sessions/{name}", timeout=5)
    if r.status_code == 200:
        click.echo(f"Session '{name}' stopped.")
    elif r.status_code == 404:
        click.echo(f"Session '{name}' not found.", err=True)
        sys.exit(1)
    else:
        click.echo(f"Error: {r.text}", err=True)
        sys.exit(1)


def stop_server() -> bool:
    """Stop the server daemon. Returns True if it was stopped."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            PID_FILE.unlink(missing_ok=True)
            return True
        except (ProcessLookupError, ValueError, OSError):
            PID_FILE.unlink(missing_ok=True)

    return False


@cli.command()
def shutdown():
    """Stop the Conductor server and all sessions."""
    if not server_running():
        click.echo("Server not running.")
        return

    click.echo("Shutting down server...")
    stop_server()
    for _ in range(20):
        time.sleep(0.25)
        if not server_running():
            click.echo("Server stopped.")
            return
    click.echo("Server may still be running. Check manually.", err=True)
    sys.exit(1)


@cli.command()
def restart():
    """Restart the Conductor server (keeps sessions)."""
    if not server_running():
        click.echo("Server not running. Starting...")
    else:
        click.echo("Stopping server...")
        stop_server()
        # Wait for it to die
        for _ in range(20):
            time.sleep(0.25)
            if not server_running():
                break

    if start_server_daemon():
        click.echo(f"Server restarted on {BASE_URL}")
    else:
        click.echo("Failed to start server. Try: conductor serve", err=True)
        sys.exit(1)


@cli.command()
def open():
    """Open the Conductor dashboard in the default browser."""
    import webbrowser

    if not server_running():
        click.echo("Server not running. Starting daemon...")
        if not start_server_daemon():
            click.echo("Failed to start server. Try: conductor serve", err=True)
            sys.exit(1)
        click.echo(f"Server started on {BASE_URL}")

    click.echo(f"Opening {BASE_URL}")
    webbrowser.open(BASE_URL)


@cli.command()
def qr():
    """Show a QR code to open the dashboard on your phone.

    Detects your Tailscale IP and generates a scannable QR code.
    Prints it in the terminal and opens a clean SVG image as fallback.
    """
    import shutil
    import tempfile
    import webbrowser

    import qrcode
    import qrcode.image.svg

    # Try to get Tailscale IP
    tailscale_ip = None
    if shutil.which("tailscale"):
        try:
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                tailscale_ip = result.stdout.strip().split("\n")[0]
        except Exception:
            pass

    if tailscale_ip:
        url = f"http://{tailscale_ip}:{PORT}"
    else:
        url = f"http://localhost:{PORT}"
        click.echo("Tailscale not found. Using localhost (won't work from other devices).")

    # Print ASCII in terminal
    click.echo(f"\n♭ conductor — scan to open on your phone\n")
    qr_obj = qrcode.QRCode(border=2)
    qr_obj.add_data(url)
    qr_obj.make(fit=True)
    qr_obj.print_ascii(invert=True)
    click.echo(f"\n  {url}\n")

    # Generate a clean SVG, wrap in HTML page, and open in browser
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    svg_path = os.path.join(tempfile.gettempdir(), "conductor-qr.svg")
    img.save(svg_path)

    svg_data = Path(svg_path).read_text()

    html_path = os.path.join(tempfile.gettempdir(), "conductor-qr.html")
    Path(html_path).write_text(f"""<!DOCTYPE html>
<html><head><title>conductor — Link Device</title>
<style>
body {{ margin:0; min-height:100vh; display:flex; flex-direction:column;
       align-items:center; justify-content:center; background:#0a0a1a;
       color:#e0e0e0; font-family:Helvetica,Arial,sans-serif; }}
h1 {{ font-size:28px; color:#8080ff; margin:0 0 6px; font-weight:600; }}
.sub {{ font-size:14px; color:#808090; margin-bottom:30px; }}
.qr {{ background:#ffffff; padding:24px; border-radius:12px; display:inline-block; }}
.qr svg {{ width:300px; height:300px; display:block; }}
.url {{ font-size:16px; color:#a0a0d0; margin-top:24px;
        font-family:monospace; letter-spacing:0.5px; }}
</style></head><body>
<h1>&#9837; conductor</h1>
<p class="sub">Scan to open on another device</p>
<div class="qr">{svg_data}</div>
<p class="url">{url}</p>
</body></html>""")

    file_url = f"file://{html_path}"
    click.echo(f"  QR page: {file_url}")
    webbrowser.open(file_url)
    click.echo("  (opened in browser — check your browser window)")


if __name__ == "__main__":
    cli()
