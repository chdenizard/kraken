"""Kraken CLI entry point."""

from __future__ import annotations

import click

from kraken import __version__
from kraken.cli.commands.carousel import carousel
from kraken.cli.commands.config_cmd import config
from kraken.cli.commands.device import device
from kraken.cli.commands.lcd import lcd
from kraken.cli.commands.status import status
from kraken.cli.commands.sysinfo import sysinfo
from kraken.cli.commands.tray import tray


@click.group()
@click.version_option(version=__version__, prog_name="kraken")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Kraken - NZXT Kraken LCD & sensor manager for Linux."""
    ctx.ensure_object(dict)


cli.add_command(device)
cli.add_command(status)
cli.add_command(lcd)
cli.add_command(carousel)
cli.add_command(sysinfo)
cli.add_command(tray)
cli.add_command(config)
