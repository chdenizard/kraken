"""CLI commands for LCD operations."""

from __future__ import annotations

import click

from kraken.core.device import KrakenDevice
from kraken.core.exceptions import KrakenError
from kraken.core import gif as gif_player
from kraken.core import lcd as lcd_ops


def _get_device() -> KrakenDevice:
    dev = KrakenDevice.find()
    dev.connect()
    dev.initialize()
    return dev


@click.group()
def lcd() -> None:
    """LCD screen management."""


@lcd.command("static")
@click.argument("image_path", type=click.Path(exists=True))
def lcd_static(image_path: str) -> None:
    """Upload a static image to the LCD."""
    try:
        dev = _get_device()
        lcd_ops.upload_static(dev, image_path)
        click.echo(f"Uploaded: {image_path}")
        dev.disconnect()
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@lcd.command("gif")
@click.argument("gif_path", type=click.Path(exists=True))
@click.option(
    "--loops", type=click.IntRange(0), default=0, show_default=True,
    help="Number of full passes (0 = loop forever until Ctrl+C).",
)
def lcd_gif(gif_path: str, loops: int) -> None:
    """Play an animated GIF on the LCD frame-by-frame."""
    dev = None
    try:
        dev = _get_device()
        if loops == 0:
            click.echo(f"Playing GIF (Ctrl+C to stop): {gif_path}")
        else:
            click.echo(f"Playing GIF for {loops} loop(s): {gif_path}")
        gif_player.play_animated_gif(dev, gif_path, loops=loops)
        click.echo("Done.")
    except KeyboardInterrupt:
        click.echo("Stopped.")
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    finally:
        if dev is not None:
            dev.disconnect()


@lcd.command("liquid")
def lcd_liquid() -> None:
    """Switch to built-in liquid temperature display."""
    try:
        dev = _get_device()
        lcd_ops.set_liquid_mode(dev)
        click.echo("LCD set to liquid temperature mode.")
        dev.disconnect()
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@lcd.command("brightness")
@click.argument("value", type=click.IntRange(0, 100))
def lcd_brightness(value: int) -> None:
    """Set LCD brightness (0-100)."""
    try:
        dev = _get_device()
        lcd_ops.set_brightness(dev, value)
        click.echo(f"Brightness set to {value}%.")
        dev.disconnect()
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@lcd.command("orientation")
@click.argument("degrees", type=click.Choice(["0", "90", "180", "270"]))
def lcd_orientation(degrees: str) -> None:
    """Set LCD orientation (0, 90, 180, or 270 degrees)."""
    try:
        dev = _get_device()
        lcd_ops.set_orientation(dev, int(degrees))
        click.echo(f"Orientation set to {degrees} degrees.")
        dev.disconnect()
    except KrakenError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
