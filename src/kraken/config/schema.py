"""TOML configuration schema: serialization and deserialization."""

from __future__ import annotations

from typing import Any

from kraken.core.models import (
    AppConfig,
    CarouselConfig,
    CarouselItem,
    LCDConfig,
    SysInfoConfig,
    TrayConfig,
)


def config_from_dict(data: dict[str, Any]) -> AppConfig:
    """Build an AppConfig from a parsed TOML dictionary."""
    device = data.get("device", {})
    lcd_data = data.get("lcd", {})
    carousel_data = data.get("carousel", {})
    sysinfo_data = data.get("sysinfo", {})
    tray_data = data.get("tray", {})

    lcd = LCDConfig(
        brightness=lcd_data.get("brightness", 50),
        orientation=lcd_data.get("orientation", 0),
    )

    items = []
    for item_data in carousel_data.get("items", []):
        items.append(
            CarouselItem(
                path=item_data.get("path", ""),
                display_seconds=item_data.get("seconds", 10.0),
                media_type=item_data.get("media_type", ""),
            )
        )

    carousel = CarouselConfig(
        enabled=carousel_data.get("enabled", False),
        items=items,
        loop=carousel_data.get("loop", True),
    )

    sysinfo = SysInfoConfig(
        enabled=sysinfo_data.get("enabled", False),
        show_cpu_temp=sysinfo_data.get("show_cpu_temp", True),
        show_gpu_temp=sysinfo_data.get("show_gpu_temp", False),
        refresh_seconds=sysinfo_data.get("refresh_seconds", 5.0),
    )

    tray = TrayConfig(
        enabled=tray_data.get("enabled", False),
        show_temp=tray_data.get("show_temp", True),
    )

    return AppConfig(
        device_serial=device.get("serial", ""),
        lcd=lcd,
        carousel=carousel,
        sysinfo=sysinfo,
        tray=tray,
    )


def config_to_dict(config: AppConfig) -> dict[str, Any]:
    """Convert an AppConfig to a TOML-serializable dictionary."""
    items = []
    for item in config.carousel.items:
        items.append(
            {
                "path": item.path,
                "seconds": item.display_seconds,
                "media_type": item.media_type,
            }
        )

    return {
        "device": {
            "serial": config.device_serial,
        },
        "lcd": {
            "brightness": config.lcd.brightness,
            "orientation": config.lcd.orientation,
        },
        "carousel": {
            "enabled": config.carousel.enabled,
            "loop": config.carousel.loop,
            "items": items,
        },
        "sysinfo": {
            "enabled": config.sysinfo.enabled,
            "show_cpu_temp": config.sysinfo.show_cpu_temp,
            "show_gpu_temp": config.sysinfo.show_gpu_temp,
            "refresh_seconds": config.sysinfo.refresh_seconds,
        },
        "tray": {
            "enabled": config.tray.enabled,
            "show_temp": config.tray.show_temp,
        },
    }
