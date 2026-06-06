"""Tests for core data models."""

import pytest

from kraken.core.models import (
    AppConfig,
    CarouselConfig,
    CarouselItem,
    LCDConfig,
    SensorData,
    SysInfoConfig,
    TrayConfig,
)


class TestSensorData:
    def test_creation(self, sample_sensor_data: SensorData) -> None:
        assert sample_sensor_data.liquid_temp_c == 29.2
        assert sample_sensor_data.pump_rpm == 2703
        assert sample_sensor_data.fan_rpm == 1050

    def test_frozen(self, sample_sensor_data: SensorData) -> None:
        with pytest.raises(AttributeError):
            sample_sensor_data.liquid_temp_c = 30.0  # type: ignore[misc]

    def test_default_timestamp(self) -> None:
        data = SensorData(liquid_temp_c=25.0, pump_rpm=2000, fan_rpm=900)
        assert data.timestamp > 0


class TestLCDConfig:
    def test_defaults(self) -> None:
        lcd = LCDConfig()
        assert lcd.brightness == 50
        assert lcd.orientation == 0

    def test_valid_values(self) -> None:
        lcd = LCDConfig(brightness=100, orientation=270)
        assert lcd.brightness == 100
        assert lcd.orientation == 270

    def test_invalid_brightness(self) -> None:
        with pytest.raises(ValueError, match="Brightness"):
            LCDConfig(brightness=101)

    def test_invalid_brightness_negative(self) -> None:
        with pytest.raises(ValueError, match="Brightness"):
            LCDConfig(brightness=-1)

    def test_invalid_orientation(self) -> None:
        with pytest.raises(ValueError, match="Orientation"):
            LCDConfig(orientation=45)


class TestCarouselItem:
    def test_auto_detect_static(self) -> None:
        item = CarouselItem(path="/img/test.png")
        assert item.media_type == "static"

    def test_auto_detect_gif(self) -> None:
        item = CarouselItem(path="/img/anim.gif")
        assert item.media_type == "gif"

    def test_auto_detect_jpg(self) -> None:
        item = CarouselItem(path="/img/photo.jpg")
        assert item.media_type == "static"

    def test_explicit_media_type(self) -> None:
        item = CarouselItem(path="/img/test.png", media_type="gif")
        assert item.media_type == "gif"

    def test_invalid_seconds(self) -> None:
        with pytest.raises(ValueError, match="display_seconds"):
            CarouselItem(path="/img/test.png", display_seconds=0)

    def test_negative_seconds(self) -> None:
        with pytest.raises(ValueError, match="display_seconds"):
            CarouselItem(path="/img/test.png", display_seconds=-5)


    def test_sysinfo_media_type(self) -> None:
        item = CarouselItem(path="", media_type="sysinfo", display_seconds=15)
        assert item.media_type == "sysinfo"
        assert item.is_special is True

    def test_liquid_media_type(self) -> None:
        item = CarouselItem(path="", media_type="liquid", display_seconds=10)
        assert item.media_type == "liquid"
        assert item.is_special is True

    def test_static_not_special(self) -> None:
        item = CarouselItem(path="/img/test.png")
        assert item.is_special is False

    def test_invalid_media_type(self) -> None:
        with pytest.raises(ValueError, match="Invalid media_type"):
            CarouselItem(path="/img/test.png", media_type="invalid")


class TestSysInfoConfig:
    def test_defaults(self) -> None:
        cfg = SysInfoConfig()
        assert cfg.show_cpu_temp is True
        assert cfg.show_gpu_temp is False
        assert cfg.refresh_seconds == 5.0

    def test_invalid_refresh(self) -> None:
        with pytest.raises(ValueError, match="refresh_seconds"):
            SysInfoConfig(refresh_seconds=0.5)


class TestAppConfig:
    def test_defaults(self) -> None:
        cfg = AppConfig()
        assert cfg.device_serial == ""
        assert isinstance(cfg.lcd, LCDConfig)
        assert isinstance(cfg.carousel, CarouselConfig)
        assert isinstance(cfg.sysinfo, SysInfoConfig)
        assert isinstance(cfg.tray, TrayConfig)
