"""XDG-compliant path resolution for Kraken configuration."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "kraken"


def get_config_dir() -> Path:
    """Return the configuration directory, creating it if needed."""
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".config"
    config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Return the path to the main configuration file."""
    return get_config_dir() / "config.toml"


def get_data_dir() -> Path:
    """Return the data directory for runtime state."""
    xdg = os.environ.get("XDG_DATA_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    data_dir = base / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
