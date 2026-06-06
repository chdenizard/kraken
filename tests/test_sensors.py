"""Tests for sensor reading."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kraken.core.sensors import read_sensors


def _create_hwmon(tmp_path: Path, temp: int = 29200, pump: int = 2703, fan: int = 1050) -> Path:
    hwmon_dir = tmp_path / "hwmon0"
    hwmon_dir.mkdir(exist_ok=True)
    (hwmon_dir / "name").write_text("kraken2023\n")
    (hwmon_dir / "temp1_input").write_text(f"{temp}\n")
    (hwmon_dir / "fan1_input").write_text(f"{pump}\n")
    (hwmon_dir / "fan2_input").write_text(f"{fan}\n")
    return hwmon_dir


class TestReadSensors:
    def test_hwmon_primary(self, tmp_path: Path) -> None:
        hwmon = _create_hwmon(tmp_path)
        data = read_sensors(hwmon_path=hwmon)
        assert data.liquid_temp_c == pytest.approx(29.2)
        assert data.pump_rpm == 2703
        assert data.fan_rpm == 1050

    def test_liquidctl_fallback(self) -> None:
        mock_device = MagicMock()
        mock_device.get_status.return_value = [
            ("Liquid temperature", 31.5, "C"),
            ("Pump speed", 2800, "rpm"),
            ("Fan speed", 1100, "rpm"),
        ]
        data = read_sensors(device=mock_device)
        assert data.liquid_temp_c == pytest.approx(31.5)
        assert data.pump_rpm == 2800
        assert data.fan_rpm == 1100

    def test_hwmon_preferred_over_liquidctl(self, tmp_path: Path) -> None:
        hwmon = _create_hwmon(tmp_path, temp=25000, pump=2000, fan=900)
        mock_device = MagicMock()
        mock_device.get_status.return_value = [
            ("Liquid temperature", 99.9, "C"),
        ]
        data = read_sensors(device=mock_device, hwmon_path=hwmon)
        assert data.liquid_temp_c == pytest.approx(25.0)
        mock_device.get_status.assert_not_called()

    def test_hwmon_fails_fallback_to_liquidctl(self, tmp_path: Path) -> None:
        bad_hwmon = tmp_path / "hwmon_bad"
        bad_hwmon.mkdir()
        mock_device = MagicMock()
        mock_device.get_status.return_value = [
            ("Liquid temperature", 28.0, "C"),
            ("Pump speed", 2500, "rpm"),
            ("Fan speed", 1000, "rpm"),
        ]
        data = read_sensors(device=mock_device, hwmon_path=bad_hwmon)
        assert data.liquid_temp_c == pytest.approx(28.0)

    def test_no_source_raises(self) -> None:
        with pytest.raises(RuntimeError, match="No sensor source"):
            read_sensors()

    def test_hwmon_fails_no_device_raises(self, tmp_path: Path) -> None:
        bad_hwmon = tmp_path / "hwmon_bad"
        bad_hwmon.mkdir()
        with pytest.raises(Exception):
            read_sensors(hwmon_path=bad_hwmon)
