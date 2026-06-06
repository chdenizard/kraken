"""Read sensor data from Kraken hwmon sysfs interface."""

from __future__ import annotations

from pathlib import Path

from kraken.core.exceptions import HwmonNotFoundError
from kraken.core.models import SensorData


def read_hwmon_sensors(hwmon_path: Path) -> SensorData:
    """Read sensor values from hwmon sysfs files.

    Expected files:
        temp1_input  - Liquid temperature in millidegrees Celsius
        fan1_input   - Pump speed in RPM
        fan2_input   - Fan speed in RPM

    Returns:
        SensorData with current readings.

    Raises:
        HwmonNotFoundError: If required sysfs files are missing.
    """
    try:
        temp_raw = (hwmon_path / "temp1_input").read_text().strip()
        pump_raw = (hwmon_path / "fan1_input").read_text().strip()
        fan_raw = (hwmon_path / "fan2_input").read_text().strip()
    except FileNotFoundError as e:
        raise HwmonNotFoundError(f"Missing hwmon sensor file: {e}") from e
    except OSError as e:
        raise HwmonNotFoundError(f"Failed to read hwmon sensor: {e}") from e

    return SensorData(
        liquid_temp_c=int(temp_raw) / 1000.0,
        pump_rpm=int(pump_raw),
        fan_rpm=int(fan_raw),
    )
