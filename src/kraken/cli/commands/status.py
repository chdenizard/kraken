"""CLI command for sensor status."""

from __future__ import annotations

import json
import time

import click

from kraken.core.exceptions import HwmonNotFoundError, KrakenError
from kraken.core.sensors import read_sensors
from kraken.hwmon.discovery import find_kraken_hwmon


@click.command()
@click.option("--watch", "-w", is_flag=True, help="Continuous monitoring.")
@click.option("--interval", "-i", default=2.0, help="Poll interval in seconds (default: 2).")
@click.option("--json-output", "--json", "use_json", is_flag=True, help="Output as JSON.")
def status(watch: bool, interval: float, use_json: bool) -> None:
    """Show current sensor readings."""
    try:
        hwmon_path = find_kraken_hwmon()
    except HwmonNotFoundError:
        hwmon_path = None

    if hwmon_path is None:
        click.echo("Warning: hwmon not found, trying liquidctl...", err=True)
        try:
            from kraken.core.device import KrakenDevice
            dev = KrakenDevice.find()
            dev.connect()
            dev.initialize()
        except KrakenError as e:
            click.echo(f"Error: No sensor source available: {e}", err=True)
            raise SystemExit(1)
    else:
        dev = None

    try:
        if watch:
            _watch_loop(hwmon_path, dev, interval, use_json)
        else:
            _print_once(hwmon_path, dev, use_json)
    except KeyboardInterrupt:
        click.echo()
    finally:
        if dev is not None:
            dev.disconnect()


def _print_once(hwmon_path, dev, use_json: bool) -> None:
    data = read_sensors(device=dev, hwmon_path=hwmon_path)
    if use_json:
        click.echo(
            json.dumps(
                {
                    "liquid_temp_c": data.liquid_temp_c,
                    "pump_rpm": data.pump_rpm,
                    "fan_rpm": data.fan_rpm,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Liquid Temp: {data.liquid_temp_c:.1f} C")
        click.echo(f"Pump Speed:  {data.pump_rpm} RPM")
        click.echo(f"Fan Speed:   {data.fan_rpm} RPM")


def _watch_loop(hwmon_path, dev, interval: float, use_json: bool) -> None:
    while True:
        data = read_sensors(device=dev, hwmon_path=hwmon_path)
        if use_json:
            click.echo(
                json.dumps(
                    {
                        "liquid_temp_c": data.liquid_temp_c,
                        "pump_rpm": data.pump_rpm,
                        "fan_rpm": data.fan_rpm,
                    }
                )
            )
        else:
            click.echo(
                f"\rLiquid: {data.liquid_temp_c:.1f}C | "
                f"Pump: {data.pump_rpm} RPM | "
                f"Fan: {data.fan_rpm} RPM   ",
                nl=False,
            )
        time.sleep(interval)
