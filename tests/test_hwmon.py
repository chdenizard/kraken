"""Tests for hwmon discovery and reader."""

from pathlib import Path

import pytest

from kraken.core.exceptions import HwmonNotFoundError
from kraken.hwmon.discovery import find_kraken_hwmon
from kraken.hwmon.reader import read_hwmon_sensors


def _create_hwmon(tmp_path: Path, name: str, idx: int = 0,
                  temp: int = 29200, pump: int = 2703, fan: int = 1050) -> Path:
    """Create a mock hwmon directory structure."""
    hwmon_dir = tmp_path / f"hwmon{idx}"
    hwmon_dir.mkdir()
    (hwmon_dir / "name").write_text(f"{name}\n")
    (hwmon_dir / "temp1_input").write_text(f"{temp}\n")
    (hwmon_dir / "fan1_input").write_text(f"{pump}\n")
    (hwmon_dir / "fan2_input").write_text(f"{fan}\n")
    return hwmon_dir


class TestFindKrakenHwmon:
    def test_find_kraken2023(self, tmp_path: Path) -> None:
        _create_hwmon(tmp_path, "coretemp", idx=0)
        kraken_dir = _create_hwmon(tmp_path, "kraken2023", idx=5)
        assert find_kraken_hwmon(tmp_path) == kraken_dir

    def test_find_nzxt_kraken3(self, tmp_path: Path) -> None:
        kraken_dir = _create_hwmon(tmp_path, "nzxt-kraken3", idx=0)
        assert find_kraken_hwmon(tmp_path) == kraken_dir

    def test_not_found(self, tmp_path: Path) -> None:
        _create_hwmon(tmp_path, "coretemp", idx=0)
        _create_hwmon(tmp_path, "amdgpu", idx=1)
        with pytest.raises(HwmonNotFoundError):
            find_kraken_hwmon(tmp_path)

    def test_empty_dir(self, tmp_path: Path) -> None:
        with pytest.raises(HwmonNotFoundError):
            find_kraken_hwmon(tmp_path)

    def test_base_not_exists(self, tmp_path: Path) -> None:
        with pytest.raises(HwmonNotFoundError):
            find_kraken_hwmon(tmp_path / "nonexistent")

    def test_no_name_file(self, tmp_path: Path) -> None:
        (tmp_path / "hwmon0").mkdir()
        with pytest.raises(HwmonNotFoundError):
            find_kraken_hwmon(tmp_path)


class TestReadHwmonSensors:
    def test_read_normal(self, tmp_path: Path) -> None:
        hwmon_dir = _create_hwmon(tmp_path, "kraken2023", temp=29200, pump=2703, fan=1050)
        data = read_hwmon_sensors(hwmon_dir)
        assert data.liquid_temp_c == pytest.approx(29.2)
        assert data.pump_rpm == 2703
        assert data.fan_rpm == 1050

    def test_read_high_temp(self, tmp_path: Path) -> None:
        hwmon_dir = _create_hwmon(tmp_path, "kraken2023", temp=45500, pump=3000, fan=1200)
        data = read_hwmon_sensors(hwmon_dir)
        assert data.liquid_temp_c == pytest.approx(45.5)

    def test_missing_temp_file(self, tmp_path: Path) -> None:
        hwmon_dir = tmp_path / "hwmon0"
        hwmon_dir.mkdir()
        (hwmon_dir / "fan1_input").write_text("2000\n")
        (hwmon_dir / "fan2_input").write_text("1000\n")
        with pytest.raises(HwmonNotFoundError, match="Missing"):
            read_hwmon_sensors(hwmon_dir)

    def test_missing_fan_file(self, tmp_path: Path) -> None:
        hwmon_dir = tmp_path / "hwmon0"
        hwmon_dir.mkdir()
        (hwmon_dir / "temp1_input").write_text("29000\n")
        (hwmon_dir / "fan1_input").write_text("2000\n")
        with pytest.raises(HwmonNotFoundError, match="Missing"):
            read_hwmon_sensors(hwmon_dir)
