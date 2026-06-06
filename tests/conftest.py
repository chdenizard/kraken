"""Shared test fixtures."""

from __future__ import annotations

import pytest

from kraken.core.models import DeviceInfo, SensorData


@pytest.fixture
def sample_sensor_data() -> SensorData:
    return SensorData(liquid_temp_c=29.2, pump_rpm=2703, fan_rpm=1050, timestamp=0.0)


@pytest.fixture
def sample_device_info() -> DeviceInfo:
    return DeviceInfo(
        description="NZXT Kraken 2023 Standard",
        firmware_version="2.0.3",
        lcd_resolution=(240, 240),
        serial_number="TEST123456",
        product_id=0x300E,
    )
