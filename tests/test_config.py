"""Tests for configuration loading and saving."""

from pathlib import Path

import pytest

from kraken.config.manager import load_config, save_config
from kraken.config.schema import config_from_dict, config_to_dict
from kraken.core.exceptions import ConfigError
from kraken.core.models import AppConfig, CarouselItem, LCDConfig


class TestConfigFromDict:
    def test_empty_dict(self) -> None:
        cfg = config_from_dict({})
        assert cfg.lcd.brightness == 50
        assert cfg.lcd.orientation == 0
        assert cfg.carousel.enabled is False
        assert cfg.carousel.items == []

    def test_full_config(self) -> None:
        data = {
            "device": {"serial": "ABC123"},
            "lcd": {"brightness": 80, "orientation": 90},
            "carousel": {
                "enabled": True,
                "loop": False,
                "items": [
                    {"path": "/img/a.png", "seconds": 5},
                    {"path": "/img/b.gif", "seconds": 15, "media_type": "gif"},
                ],
            },
            "sysinfo": {
                "enabled": True,
                "show_cpu_temp": True,
                "show_gpu_temp": True,
                "refresh_seconds": 3.0,
            },
            "tray": {"enabled": True, "show_temp": False},
        }
        cfg = config_from_dict(data)
        assert cfg.device_serial == "ABC123"
        assert cfg.lcd.brightness == 80
        assert cfg.lcd.orientation == 90
        assert cfg.carousel.enabled is True
        assert cfg.carousel.loop is False
        assert len(cfg.carousel.items) == 2
        assert cfg.carousel.items[0].path == "/img/a.png"
        assert cfg.carousel.items[0].display_seconds == 5
        assert cfg.carousel.items[0].media_type == "static"
        assert cfg.carousel.items[1].media_type == "gif"
        assert cfg.sysinfo.enabled is True
        assert cfg.sysinfo.show_gpu_temp is True
        assert cfg.tray.enabled is True
        assert cfg.tray.show_temp is False

    def test_partial_config(self) -> None:
        data = {"lcd": {"brightness": 75}}
        cfg = config_from_dict(data)
        assert cfg.lcd.brightness == 75
        assert cfg.lcd.orientation == 0
        assert cfg.carousel.enabled is False


class TestConfigToDict:
    def test_roundtrip(self) -> None:
        original = AppConfig(
            device_serial="XYZ",
            lcd=LCDConfig(brightness=90, orientation=180),
        )
        data = config_to_dict(original)
        restored = config_from_dict(data)
        assert restored.device_serial == "XYZ"
        assert restored.lcd.brightness == 90
        assert restored.lcd.orientation == 180

    def test_roundtrip_with_items(self) -> None:
        original = AppConfig()
        original.carousel.items.append(
            CarouselItem(path="/img/test.png", display_seconds=7.0)
        )
        data = config_to_dict(original)
        restored = config_from_dict(data)
        assert len(restored.carousel.items) == 1
        assert restored.carousel.items[0].path == "/img/test.png"
        assert restored.carousel.items[0].display_seconds == 7.0


    def test_roundtrip_with_special_items(self) -> None:
        original = AppConfig()
        original.carousel.items.append(
            CarouselItem(path="/img/test.png", display_seconds=5.0)
        )
        original.carousel.items.append(
            CarouselItem(path="", display_seconds=15.0, media_type="sysinfo")
        )
        original.carousel.items.append(
            CarouselItem(path="", display_seconds=10.0, media_type="liquid")
        )
        data = config_to_dict(original)
        restored = config_from_dict(data)
        assert len(restored.carousel.items) == 3
        assert restored.carousel.items[0].media_type == "static"
        assert restored.carousel.items[1].media_type == "sysinfo"
        assert restored.carousel.items[1].path == ""
        assert restored.carousel.items[1].display_seconds == 15.0
        assert restored.carousel.items[2].media_type == "liquid"


class TestLoadSaveConfig:
    def test_load_default_when_missing(self, tmp_path: Path) -> None:
        cfg = load_config(tmp_path / "nonexistent.toml")
        assert isinstance(cfg, AppConfig)
        assert cfg.lcd.brightness == 50

    def test_save_and_load(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        original = AppConfig(
            device_serial="TEST",
            lcd=LCDConfig(brightness=60, orientation=90),
        )
        save_config(original, config_file)
        assert config_file.exists()

        loaded = load_config(config_file)
        assert loaded.device_serial == "TEST"
        assert loaded.lcd.brightness == 60
        assert loaded.lcd.orientation == 90

    def test_load_invalid_toml(self, tmp_path: Path) -> None:
        config_file = tmp_path / "bad.toml"
        config_file.write_text("this is not valid toml [[[")
        with pytest.raises(ConfigError):
            load_config(config_file)

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        config_file = tmp_path / "sub" / "dir" / "config.toml"
        save_config(AppConfig(), config_file)
        assert config_file.exists()
