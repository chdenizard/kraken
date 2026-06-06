"""Configuration file manager: load and save TOML config."""

from __future__ import annotations

import tomllib
from pathlib import Path

import tomli_w

from kraken.config.paths import get_config_file
from kraken.config.schema import config_from_dict, config_to_dict
from kraken.core.exceptions import ConfigError
from kraken.core.models import AppConfig


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from a TOML file.

    Returns default config if the file does not exist.
    """
    config_path = path or get_config_file()

    if not config_path.exists():
        return AppConfig()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return config_from_dict(data)
    except (tomllib.TOMLDecodeError, KeyError, TypeError, ValueError) as e:
        raise ConfigError(f"Failed to load config from {config_path}: {e}") from e


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save configuration to a TOML file."""
    config_path = path or get_config_file()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        data = config_to_dict(config)
        with open(config_path, "wb") as f:
            tomli_w.dump(data, f)
    except OSError as e:
        raise ConfigError(f"Failed to save config to {config_path}: {e}") from e
