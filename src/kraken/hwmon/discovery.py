"""Discover Kraken hwmon device in sysfs."""

from __future__ import annotations

from pathlib import Path

from kraken.core.exceptions import HwmonNotFoundError

HWMON_BASE = Path("/sys/class/hwmon")
KRAKEN_HWMON_NAMES = {"kraken2023", "nzxt-kraken3", "kraken3"}


def find_kraken_hwmon(base: Path | None = None) -> Path:
    """Find the hwmon directory for the Kraken device.

    Scans /sys/class/hwmon/*/name for known Kraken driver names.

    Returns:
        Path to the hwmon directory (e.g., /sys/class/hwmon/hwmon5).

    Raises:
        HwmonNotFoundError: If no Kraken hwmon device is found.
    """
    hwmon_base = base or HWMON_BASE

    if not hwmon_base.exists():
        raise HwmonNotFoundError(f"hwmon base path does not exist: {hwmon_base}")

    for hwmon_dir in sorted(hwmon_base.iterdir()):
        name_file = hwmon_dir / "name"
        if not name_file.exists():
            continue
        try:
            name = name_file.read_text().strip()
            if name in KRAKEN_HWMON_NAMES:
                return hwmon_dir
        except OSError:
            continue

    raise HwmonNotFoundError(
        "No Kraken hwmon device found. Is the nzxt-kraken3 kernel module loaded?"
    )
