"""CLI commands for device management."""

from __future__ import annotations

import click

from kraken.core.device import KrakenDevice
from kraken.core.exceptions import DeviceNotFoundError, DeviceConnectionError


@click.group()
def device() -> None:
    """Device discovery and initialization."""


@device.command("list")
def device_list() -> None:
    """List detected Kraken devices."""
    try:
        dev = KrakenDevice.find()
        click.echo(f"Found: {dev._dev.description}")
    except DeviceNotFoundError as e:
        click.echo(f"No devices found: {e}", err=True)


@device.command("init")
def device_init() -> None:
    """Initialize the Kraken device (required after boot)."""
    try:
        dev = KrakenDevice.find()
        dev.connect()
        info = dev.initialize()
        click.echo(f"Initialized: {info.description}")
        click.echo(f"  Firmware: {info.firmware_version}")
        click.echo(f"  LCD: {info.lcd_resolution[0]}x{info.lcd_resolution[1]}")
        click.echo(f"  Serial: {info.serial_number}")
        dev.disconnect()
    except (DeviceNotFoundError, DeviceConnectionError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@device.command("info")
def device_info() -> None:
    """Show device information."""
    try:
        with KrakenDevice.find() as dev:
            info = dev.info
            if info:
                click.echo(f"Device:     {info.description}")
                click.echo(f"Firmware:   {info.firmware_version}")
                click.echo(f"LCD:        {info.lcd_resolution[0]}x{info.lcd_resolution[1]}")
                click.echo(f"Serial:     {info.serial_number}")
                click.echo(f"Product ID: 0x{info.product_id:04X}")
    except (DeviceNotFoundError, DeviceConnectionError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
