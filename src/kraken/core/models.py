"""Data models for the Kraken project."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SensorData:
    """Snapshot of sensor readings from the Kraken device."""

    liquid_temp_c: float
    pump_rpm: int
    fan_rpm: int
    timestamp: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class DeviceInfo:
    """Static information about the connected Kraken device."""

    description: str
    firmware_version: str
    lcd_resolution: tuple[int, int]
    serial_number: str
    product_id: int


@dataclass
class LCDConfig:
    """LCD display settings."""

    brightness: int = 50
    orientation: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.brightness <= 100:
            raise ValueError(f"Brightness must be 0-100, got {self.brightness}")
        if self.orientation not in (0, 90, 180, 270):
            raise ValueError(f"Orientation must be 0/90/180/270, got {self.orientation}")


SPECIAL_MEDIA_TYPES = {"sysinfo", "liquid"}
VALID_MEDIA_TYPES = {"static", "gif", "sysinfo", "liquid", ""}


@dataclass
class CarouselItem:
    """A single item in the carousel playlist."""

    path: str
    display_seconds: float = 10.0
    media_type: str = ""

    def __post_init__(self) -> None:
        if self.display_seconds <= 0:
            raise ValueError(f"display_seconds must be positive, got {self.display_seconds}")
        if self.media_type not in VALID_MEDIA_TYPES:
            raise ValueError(
                f"Invalid media_type '{self.media_type}'. "
                f"Must be one of {sorted(VALID_MEDIA_TYPES - {''})}"
            )
        if not self.media_type:
            ext = Path(self.path).suffix.lower()
            self.media_type = "gif" if ext == ".gif" else "static"

    @property
    def is_special(self) -> bool:
        return self.media_type in SPECIAL_MEDIA_TYPES


@dataclass
class CarouselConfig:
    """Carousel configuration."""

    enabled: bool = False
    items: list[CarouselItem] = field(default_factory=list)
    loop: bool = True


@dataclass
class SysInfoConfig:
    """System info LCD overlay configuration."""

    enabled: bool = False
    show_cpu_temp: bool = True
    show_gpu_temp: bool = False
    refresh_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.refresh_seconds < 1.0:
            raise ValueError(f"refresh_seconds must be >= 1.0, got {self.refresh_seconds}")


@dataclass
class TrayConfig:
    """System tray configuration."""

    enabled: bool = False
    show_temp: bool = True


@dataclass
class AppConfig:
    """Top-level application configuration."""

    device_serial: str = ""
    lcd: LCDConfig = field(default_factory=LCDConfig)
    carousel: CarouselConfig = field(default_factory=CarouselConfig)
    sysinfo: SysInfoConfig = field(default_factory=SysInfoConfig)
    tray: TrayConfig = field(default_factory=TrayConfig)
