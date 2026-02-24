import os
import subprocess
import sys
import time
from pathlib import Path

import click
import httpx

from conductor.utils.config import BASE_URL, HOST, PORT, ensure_dirs


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

    with open(log_path, "a") as log:
        subprocess.Popen(
            [sys.executable, "-m", "conductor.server.app"],
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            cwd=str(project_root),
            env=env,
        )

    for _ in range(20):
        time.sleep(0.25)
        if server_running():
            return True
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
def run(command, name):
    """Run a command in a new Conductor session.

    Usage: conductor run COMMAND [NAME]

    Examples:
        conductor run claude research
        conductor run "python train.py" training
        conductor run bash
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
        json={"name": name, "command": command},
        timeout=10,
    )

    if r.status_code == 200:
        data = r.json()
        click.echo(f"Session '{data['name']}' started (pid: {data['pid']})")
        click.echo(f"Dashboard: {BASE_URL}")
    elif r.status_code == 409:
        click.echo(f"Session '{name}' already exists.", err=True)
        sys.exit(1)
    else:
        click.echo(f"Error: {r.text}", err=True)
        sys.exit(1)


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


if __name__ == "__main__":
    cli()
