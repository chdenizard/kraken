"""CLI command for system tray."""

from __future__ import annotations

import click


@click.command()
@click.option("--no-gui", is_flag=True, help="Run tray icon without opening main window.")
def tray(no_gui: bool) -> None:
    """Start system tray icon with sensor status."""
    try:
        from kraken.gui.tray import run_tray
        run_tray(show_window=not no_gui)
    except ImportError:
        click.echo(
            "Error: PySide6 is required for system tray. "
            "Install with: pip install kraken[gui]",
            err=True,
        )
        raise SystemExit(1)
