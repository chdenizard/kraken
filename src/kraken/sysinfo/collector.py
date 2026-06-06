"""Collect system information (CPU/GPU temperatures)."""

from __future__ import annotations

from dataclasses import dataclass

import psutil


@dataclass(frozen=True)
class SystemStats:
    """System temperature and usage stats."""

    cpu_temp_c: float | None = None
    gpu_temp_c: float | None = None
    cpu_usage_percent: float | None = None


def collect_stats(include_cpu: bool = True, include_gpu: bool = False) -> SystemStats:
    """Collect system stats.

    Args:
        include_cpu: Whether to collect CPU temperature.
        include_gpu: Whether to attempt GPU temperature collection.
    """
    cpu_temp = None
    gpu_temp = None
    cpu_usage = None

    if include_cpu:
        cpu_temp = _get_cpu_temp()
        cpu_usage = psutil.cpu_percent(interval=None)

    if include_gpu:
        gpu_temp = _get_gpu_temp()

    return SystemStats(
        cpu_temp_c=cpu_temp,
        gpu_temp_c=gpu_temp,
        cpu_usage_percent=cpu_usage,
    )


def _get_cpu_temp() -> float | None:
    """Get CPU temperature from psutil."""
    try:
        temps = psutil.sensors_temperatures()
        for source in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
            if source in temps and temps[source]:
                return temps[source][0].current
        # Fallback: try first available
        for entries in temps.values():
            if entries:
                return entries[0].current
    except Exception:
        pass
    return None


def _get_gpu_temp() -> float | None:
    """Get GPU temperature from hwmon sysfs (amdgpu/nvidia)."""
    from pathlib import Path

    hwmon_base = Path("/sys/class/hwmon")
    if not hwmon_base.exists():
        return None

    for hwmon_dir in hwmon_base.iterdir():
        name_file = hwmon_dir / "name"
        if not name_file.exists():
            continue
        try:
            name = name_file.read_text().strip()
            if name in ("amdgpu", "nvidia"):
                temp_file = hwmon_dir / "temp1_input"
                if temp_file.exists():
                    return int(temp_file.read_text().strip()) / 1000.0
        except (OSError, ValueError):
            continue
    return None
