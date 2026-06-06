"""CLI commands for carousel management."""

from __future__ import annotations

import os
import signal
import sys
import time

import click

from kraken.carousel.engine import CarouselEngine
from kraken.carousel.playlist import Playlist
from kraken.config.manager import load_config, save_config
from kraken.core.device import KrakenDevice
from kraken.core.exceptions import KrakenError
from kraken.core.lcd import set_liquid_mode
from kraken.core.models import CarouselItem

PID_FILE = "/tmp/kraken-carousel.pid"


@click.group()
def carousel() -> None:
    """Image carousel management."""


@carousel.command("start")
@click.option("--daemon", "-d", is_flag=True, help="Run in background as a daemon.")
def carousel_start(daemon: bool) -> None:
    """Start the carousel from config."""
    if daemon:
        pid = os.fork()
        if pid > 0:
            click.echo(f"Carousel started in background (PID: {pid}).")
            return
        os.setsid()
        sys.stdin = open(os.devnull, "r")
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    try:
        config = load_config()
        if not config.carousel.items:
            click.echo("Error: No items in carousel. Use 'kraken carousel add' first.", err=True)
            raise SystemExit(1)

        dev = KrakenDevice.find()
        dev.connect()
        dev.initialize()

        # Write PID file for stop command
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        playlist = Playlist(config.carousel.items)

        def on_item_changed(index: int, item: CarouselItem) -> None:
            if not daemon:
                label = f"[{item.media_type}]" if item.is_special else item.path
                click.echo(f"[{index + 1}/{len(playlist)}] {label}")

        engine = CarouselEngine(
            dev, playlist, loop=config.carousel.loop,
            on_item_changed=on_item_changed,
            sysinfo_refresh_seconds=config.sysinfo.refresh_seconds,
        )
        engine.start()
        if not daemon:
            click.echo(f"Carousel started ({len(playlist)} items). Press Ctrl+C to stop.")

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
            click.echo("Carousel stopped. LCD restored to liquid mode.")

    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@carousel.command("stop")
def carousel_stop() -> None:
    """Stop the running carousel."""
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        click.echo(f"Stopped carousel (PID: {pid}).")
    except FileNotFoundError:
        click.echo("No running carousel instance found.")
    except ProcessLookupError:
        click.echo("Process not found (already stopped).")
        try:
            os.unlink(PID_FILE)
        except OSError:
            pass


@carousel.command("add")
@click.argument("image_path", type=click.Path(exists=True), required=False, default=None)
@click.option("--seconds", "-s", default=10.0, help="Display duration in seconds (default: 10).")
@click.option("--position", "-p", type=int, default=None, help="Insert at position (default: end).")
@click.option("--sysinfo", "special_type", flag_value="sysinfo", help="Add system info display.")
@click.option("--liquid", "special_type", flag_value="liquid", help="Add liquid temp display.")
def carousel_add(image_path: str | None, seconds: float, position: int | None, special_type: str | None) -> None:
    """Add an image or special item to the carousel."""
    if special_type and image_path:
        click.echo("Error: Cannot specify both an image path and --sysinfo/--liquid.", err=True)
        raise SystemExit(1)
    if not special_type and not image_path:
        click.echo("Error: Provide an image path or use --sysinfo / --liquid.", err=True)
        raise SystemExit(1)

    try:
        config = load_config()
        playlist = Playlist(config.carousel.items)
        if special_type:
            item = playlist.add_special(special_type, display_seconds=seconds, position=position)
        else:
            item = playlist.add(image_path, display_seconds=seconds, position=position)
        config.carousel.items = playlist.items
        save_config(config)
        label = item.path if item.path else f"[{item.media_type}]"
        click.echo(f"Added: {label} ({item.media_type}, {item.display_seconds}s)")
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@carousel.command("remove")
@click.argument("index", type=int)
def carousel_remove(index: int) -> None:
    """Remove an item from the playlist by index."""
    try:
        config = load_config()
        playlist = Playlist(config.carousel.items)
        removed = playlist.remove(index)
        config.carousel.items = playlist.items
        save_config(config)
        label = f"[{removed.media_type}]" if removed.is_special else removed.path
        click.echo(f"Removed: {label}")
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@carousel.command("list")
def carousel_list() -> None:
    """List all carousel items."""
    config = load_config()
    if not config.carousel.items:
        click.echo("Carousel is empty.")
        return
    for i, item in enumerate(config.carousel.items):
        label = f"[{item.media_type}]" if item.is_special else item.path
        click.echo(f"  {i}: {label} ({item.media_type}, {item.display_seconds}s)")
    click.echo(f"\nLoop: {'yes' if config.carousel.loop else 'no'}")


@carousel.command("clear")
def carousel_clear() -> None:
    """Remove all items from the playlist."""
    config = load_config()
    config.carousel.items = []
    save_config(config)
    click.echo("Carousel cleared.")


@carousel.command("status")
def carousel_status() -> None:
    """Show carousel configuration status."""
    config = load_config()
    click.echo(f"Enabled: {'yes' if config.carousel.enabled else 'no'}")
    click.echo(f"Loop:    {'yes' if config.carousel.loop else 'no'}")
    click.echo(f"Items:   {len(config.carousel.items)}")
