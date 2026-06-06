"""Status panel: live sensor gauges."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from kraken.core.models import SensorData


class SensorGauge(QWidget):
    """A single sensor display with label and value."""

    def __init__(self, label: str, unit: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._unit = unit

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("font-size: 14px; color: #aaa;")

        self._value = QLabel("--")
        self._value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value.setStyleSheet("font-size: 36px; font-weight: bold; color: #fff;")

        self._unit_label = QLabel(unit)
        self._unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._unit_label.setStyleSheet("font-size: 12px; color: #888;")

        layout.addWidget(self._label)
        layout.addWidget(self._value)
        layout.addWidget(self._unit_label)

    def set_value(self, value: str) -> None:
        self._value.setText(value)


class StatusPanel(QWidget):
    """Panel showing live sensor data."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        group = QGroupBox("Sensor Data")
        gauges_layout = QHBoxLayout(group)

        self.liquid_temp = SensorGauge("Liquid Temp", "C")
        self.pump_rpm = SensorGauge("Pump Speed", "RPM")
        self.fan_rpm = SensorGauge("Fan Speed", "RPM")

        gauges_layout.addWidget(self.liquid_temp)
        gauges_layout.addWidget(self.pump_rpm)
        gauges_layout.addWidget(self.fan_rpm)

        layout.addWidget(group)
        layout.addStretch()

    def update_data(self, data: SensorData) -> None:
        self.liquid_temp.set_value(f"{data.liquid_temp_c:.1f}")
        self.pump_rpm.set_value(str(data.pump_rpm))
        self.fan_rpm.set_value(str(data.fan_rpm))
