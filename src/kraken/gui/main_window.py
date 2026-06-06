"""Main window with tabbed interface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from kraken.core.device import KrakenDevice
from kraken.core.exceptions import KrakenError
from kraken.core.models import SensorData
from kraken.gui.threads import SensorWorker
from kraken.gui.widgets.carousel_panel import CarouselPanel
from kraken.gui.widgets.device_info import DeviceInfoPanel
from kraken.gui.widgets.lcd_panel import LCDPanel
from kraken.gui.widgets.status_panel import StatusPanel
from kraken.gui.widgets.sysinfo_panel import SysInfoPanel
from kraken.hwmon.discovery import find_kraken_hwmon


class MainWindow(QMainWindow):
    """Kraken main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Kraken - NZXT LCD Manager")
        self.setMinimumSize(600, 500)

        self._device: KrakenDevice | None = None
        self._hwmon_path: Path | None = None
        self._sensor_worker: SensorWorker | None = None

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Tabs
        self._tabs = QTabWidget()

        self._status_panel = StatusPanel()
        self._lcd_panel = LCDPanel()
        self._carousel_panel = CarouselPanel()
        self._sysinfo_panel = SysInfoPanel()
        self._device_panel = DeviceInfoPanel()

        self._tabs.addTab(self._status_panel, "Status")
        self._tabs.addTab(self._lcd_panel, "LCD")
        self._tabs.addTab(self._carousel_panel, "Carousel")
        self._tabs.addTab(self._sysinfo_panel, "System Info")
        self._tabs.addTab(self._device_panel, "Config")

        layout.addWidget(self._tabs)

        # Status bar
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar_label = QLabel("Initializing...")
        self._statusbar.addPermanentWidget(self._statusbar_label)

        # Initialize
        self._init_hwmon()
        self._init_device()
        self._start_sensor_polling()

    def _init_hwmon(self) -> None:
        try:
            self._hwmon_path = find_kraken_hwmon()
            self._statusbar_label.setText("hwmon found")
        except Exception:
            self._hwmon_path = None
            self._statusbar_label.setText("hwmon not found")

    def _init_device(self) -> None:
        try:
            self._device = KrakenDevice.find()
            self._device.connect()
            info = self._device.initialize()

            self._lcd_panel.set_device(self._device)
            self._carousel_panel.set_device(self._device)
            self._sysinfo_panel.set_device(self._device)
            self._device_panel.update_info(info)
            self._statusbar_label.setText(f"Connected: {info.description}")
        except KrakenError as e:
            self._statusbar_label.setText(f"Device error: {e}")
            self._device = None

    def _start_sensor_polling(self) -> None:
        if self._hwmon_path is None:
            return

        self._sensor_worker = SensorWorker(hwmon_path=self._hwmon_path, interval_ms=2000)
        self._sensor_worker.data_updated.connect(self._on_sensor_data)
        self._sensor_worker.error_occurred.connect(
            lambda e: self._statusbar_label.setText(f"Sensor error: {e}")
        )
        self._sensor_worker.start()

    def _on_sensor_data(self, data: SensorData) -> None:
        self._status_panel.update_data(data)
        self._statusbar_label.setText(
            f"Liquid: {data.liquid_temp_c:.1f}C | "
            f"Pump: {data.pump_rpm} RPM | "
            f"Fan: {data.fan_rpm} RPM"
        )

    def closeEvent(self, event) -> None:
        if self._sensor_worker:
            self._sensor_worker.stop()
        # Stop any GIF playback that may still be running so the worker thread
        # finishes before we close the USB connection.
        self._lcd_panel._stop_gif()
        if self._device:
            self._device.disconnect()
        super().closeEvent(event)
