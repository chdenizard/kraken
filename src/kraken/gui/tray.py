"""System tray icon with sensor status."""

from __future__ import annotations

import signal
import sys
from pathlib import Path

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from kraken.core.models import SensorData
from kraken.gui.threads import SensorWorker
from kraken.hwmon.discovery import find_kraken_hwmon

ICON_PATH = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "kraken-icon.png"


class KrakenTray(QSystemTrayIcon):
    """System tray icon showing Kraken sensor status."""

    def __init__(self, parent: QApplication | None = None) -> None:
        super().__init__(parent)

        # Set icon
        if ICON_PATH.exists():
            self.setIcon(QIcon(str(ICON_PATH)))
        else:
            self.setIcon(QIcon.fromTheme("thermometer"))

        self.setToolTip("Kraken: Starting...")

        # Menu
        menu = QMenu()

        self._status_action = QAction("Liquid: -- C | Pump: -- RPM")
        self._status_action.setEnabled(False)
        menu.addAction(self._status_action)

        menu.addSeparator()

        show_action = QAction("Open Kraken GUI")
        show_action.triggered.connect(self._open_gui)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

        # Sensor worker
        try:
            hwmon = find_kraken_hwmon()
        except Exception:
            hwmon = None

        self._sensor_worker = SensorWorker(hwmon_path=hwmon, interval_ms=3000)
        self._sensor_worker.data_updated.connect(self._on_data)
        self._sensor_worker.start()

    def _on_data(self, data: SensorData) -> None:
        text = f"Liquid: {data.liquid_temp_c:.1f}C | Pump: {data.pump_rpm} RPM | Fan: {data.fan_rpm} RPM"
        self.setToolTip(f"Kraken: {data.liquid_temp_c:.1f}C")
        self._status_action.setText(text)

    def _open_gui(self) -> None:
        from kraken.gui.main_window import MainWindow

        if not hasattr(self, "_main_window"):
            self._main_window = MainWindow()
        self._main_window.show()
        self._main_window.raise_()

    def cleanup(self) -> None:
        self._sensor_worker.stop()


def run_tray(show_window: bool = True) -> None:
    """Run the system tray application."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Kraken")
    app.setQuitOnLastWindowClosed(False)

    # Allow Ctrl+C to terminate the Qt event loop
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    # Timer to let Python process signals (Qt blocks the Python signal handler)
    from PySide6.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(200)

    tray = KrakenTray()
    tray.show()

    if show_window:
        tray._open_gui()

    app.aboutToQuit.connect(tray.cleanup)
    sys.exit(app.exec())
