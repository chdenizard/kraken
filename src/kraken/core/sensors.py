"""Unified sensor reading: hwmon primary, liquidctl fallback."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from kraken.core.models import SensorData
from kraken.hwmon.reader import read_hwmon_sensors

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice


def read_sensors(
    device: KrakenDevice | None = None,
    hwmon_path: Path | None = None,
) -> SensorData:
    """Read sensor data, preferring hwmon over liquidctl.

    Args:
        device: Optional KrakenDevice for liquidctl fallback.
        hwmon_path: Path to hwmon sysfs directory.

    Returns:
        SensorData with current readings.

    Raises:
        RuntimeError: If neither hwmon nor device is available.
    """
    if hwmon_path is not None:
        try:
            return read_hwmon_sensors(hwmon_path)
        except Exception:
            if device is None:
                raise

    if device is not None:
        return _read_from_liquidctl(device)

    raise RuntimeError("No sensor source available: provide hwmon_path or device.")


def _read_from_liquidctl(device: KrakenDevice) -> SensorData:
    """Read sensors via liquidctl get_status()."""
    status = device.get_status()

    liquid_temp = 0.0
    pump_rpm = 0
    fan_rpm = 0

    for key, value, *_ in status:
        key_lower = key.lower()
        if "liquid" in key_lower and "temp" in key_lower:
            liquid_temp = float(value)
        elif "pump" in key_lower and ("speed" in key_lower or "rpm" in key_lower):
            pump_rpm = int(value)
        elif "fan" in key_lower and ("speed" in key_lower or "rpm" in key_lower):
            fan_rpm = int(value)

    return SensorData(
        liquid_temp_c=liquid_temp,
        pump_rpm=pump_rpm,
        fan_rpm=fan_rpm,
    )
