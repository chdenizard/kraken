"""CLI commands for configuration management."""

from __future__ import annotations

import os
import subprocess

import click

from kraken.config.manager import load_config
from kraken.config.paths import get_config_file
from kraken.config.schema import config_to_dict
from kraken.core.exceptions import ConfigError


@click.group("config")
def config() -> None:
    """Configuration management."""


@config.command("show")
def config_show() -> None:
    """Print current configuration."""
    try:
        cfg = load_config()
        data = config_to_dict(cfg)
        _print_dict(data)
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@config.command("path")
def config_path() -> None:
    """Print the configuration file path."""
    click.echo(get_config_file())


@config.command("edit")
def config_edit() -> None:
    """Open configuration file in $EDITOR."""
    config_file = get_config_file()
    if not config_file.exists():
        # Create default config
        from kraken.config.manager import save_config
        from kraken.core.models import AppConfig
        save_config(AppConfig(), config_file)
        click.echo(f"Created default config at {config_file}")

    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.run([editor, str(config_file)], check=True)
    except FileNotFoundError:
        click.echo(f"Editor '{editor}' not found. Set $EDITOR variable.", err=True)
        raise SystemExit(1)


def _print_dict(d: dict, indent: int = 0) -> None:
    prefix = "  " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            click.echo(f"{prefix}{key}:")
            _print_dict(value, indent + 1)
        elif isinstance(value, list):
            click.echo(f"{prefix}{key}:")
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    click.echo(f"{prefix}  [{i}]:")
                    _print_dict(item, indent + 2)
                else:
                    click.echo(f"{prefix}  - {item}")
        else:
            click.echo(f"{prefix}{key}: {value}")
