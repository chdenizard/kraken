"""CLI commands for system info LCD mode."""

from __future__ import annotations

import os
import signal
import sys
import time

import click

from kraken.config.manager import load_config, save_config
from kraken.core.device import KrakenDevice
from kraken.core.exceptions import KrakenError
from kraken.core.lcd import set_liquid_mode
from kraken.sysinfo.renderer import SysInfoEngine

PID_FILE = "/tmp/kraken-sysinfo.pid"


@click.group()
def sysinfo() -> None:
    """System info LCD overlay."""


@sysinfo.command("start")
@click.option("--daemon", "-d", is_flag=True, help="Run in background as a daemon.")
def sysinfo_start(daemon: bool) -> None:
    """Start rendering system stats on the LCD."""
    if daemon:
        pid = os.fork()
        if pid > 0:
            click.echo(f"System info started in background (PID: {pid}).")
            return
        os.setsid()
        sys.stdin = open(os.devnull, "r")
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    try:
        config = load_config()
        dev = KrakenDevice.find()
        dev.connect()
        dev.initialize()

        # Write PID file for stop command
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def on_error(msg: str) -> None:
            click.echo(f"Error: {msg}", err=True)

        engine = SysInfoEngine(dev, config.sysinfo, on_error=on_error)
        engine.start()
        if not daemon:
            click.echo(
                f"System info started (CPU: {'on' if config.sysinfo.show_cpu_temp else 'off'}, "
                f"GPU: {'on' if config.sysinfo.show_gpu_temp else 'off'}, "
                f"refresh: {config.sysinfo.refresh_seconds}s). Press Ctrl+C to stop."
            )

        stop = False

        def handle_signal(sig, frame):
            nonlocal stop
            stop = True

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        while not stop and engine.is_running:
            time.sleep(0.5)

        engine.stop()
        set_liquid_mode(dev)
        dev.disconnect()

        try:
            os.unlink(PID_FILE)
        except OSError:
            pass

        if not daemon:
            click.echo("System info stopped. LCD restored to liquid mode.")

    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@sysinfo.command("stop")
def sysinfo_stop() -> None:
    """Stop the system info display."""
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        click.echo(f"Stopped system info (PID: {pid}).")
    except FileNotFoundError:
        click.echo("No running system info instance found.")
    except ProcessLookupError:
        click.echo("Process not found (already stopped).")
        try:
            os.unlink(PID_FILE)
        except OSError:
            pass


@sysinfo.command("config")
@click.option("--cpu/--no-cpu", default=None, help="Enable/disable CPU temperature.")
@click.option("--gpu/--no-gpu", default=None, help="Enable/disable GPU temperature.")
@click.option("--refresh", type=float, default=None, help="Refresh interval in seconds.")
def sysinfo_config(cpu: bool | None, gpu: bool | None, refresh: float | None) -> None:
    """Show or modify system info configuration."""
    config = load_config()
    changed = False

    if cpu is not None:
        config.sysinfo.show_cpu_temp = cpu
        changed = True
    if gpu is not None:
        config.sysinfo.show_gpu_temp = gpu
        changed = True
    if refresh is not None:
        config.sysinfo.refresh_seconds = refresh
        changed = True

    if changed:
        save_config(config)
        click.echo("Configuration updated.")

    click.echo(f"CPU temp:  {'on' if config.sysinfo.show_cpu_temp else 'off'}")
    click.echo(f"GPU temp:  {'on' if config.sysinfo.show_gpu_temp else 'off'}")
    click.echo(f"Refresh:   {config.sysinfo.refresh_seconds}s")
