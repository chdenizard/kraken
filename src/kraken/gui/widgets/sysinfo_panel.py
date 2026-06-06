"""System info panel: configure and control system stats LCD overlay."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kraken.config.manager import load_config, save_config
from kraken.core.models import SysInfoConfig
from kraken.sysinfo.renderer import SysInfoEngine

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice


class SysInfoPanel(QWidget):
    """System info LCD overlay configuration and control."""

    def __init__(self, device: KrakenDevice | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device = device
        self._engine: SysInfoEngine | None = None

        layout = QVBoxLayout(self)

        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)

        self._cpu_check = QCheckBox("Show CPU Temperature")
        self._cpu_check.setChecked(True)
        settings_layout.addWidget(self._cpu_check)

        self._gpu_check = QCheckBox("Show GPU Temperature")
        self._gpu_check.setChecked(False)
        settings_layout.addWidget(self._gpu_check)

        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Refresh interval:"))
        self._refresh_spin = QDoubleSpinBox()
        self._refresh_spin.setRange(1.0, 60.0)
        self._refresh_spin.setValue(5.0)
        self._refresh_spin.setSuffix(" s")
        refresh_layout.addWidget(self._refresh_spin)
        refresh_layout.addStretch()
        settings_layout.addLayout(refresh_layout)

        layout.addWidget(settings_group)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)

        self._btn_start = QPushButton("Start")
        self._btn_start.clicked.connect(self._start)
        controls_layout.addWidget(self._btn_start)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.clicked.connect(self._stop)
        self._btn_stop.setEnabled(False)
        controls_layout.addWidget(self._btn_stop)

        btn_save = QPushButton("Save Config")
        btn_save.clicked.connect(self._save_config)
        controls_layout.addWidget(btn_save)

        layout.addWidget(controls_group)

        # Status
        self._status = QLabel("System info stopped")
        self._status.setStyleSheet("color: #888;")
        layout.addWidget(self._status)

        layout.addStretch()

        self._load_config()

    def set_device(self, device: KrakenDevice) -> None:
        self._device = device

    def _load_config(self) -> None:
        try:
            config = load_config()
            self._cpu_check.setChecked(config.sysinfo.show_cpu_temp)
            self._gpu_check.setChecked(config.sysinfo.show_gpu_temp)
            self._refresh_spin.setValue(config.sysinfo.refresh_seconds)
        except Exception:
            pass

    def _save_config(self) -> None:
        try:
            config = load_config()
            config.sysinfo.show_cpu_temp = self._cpu_check.isChecked()
            config.sysinfo.show_gpu_temp = self._gpu_check.isChecked()
            config.sysinfo.refresh_seconds = self._refresh_spin.value()
            save_config(config)
            self._status.setText("Configuration saved")
        except Exception as e:
            self._status.setText(f"Error: {e}")

    def _get_sysinfo_config(self) -> SysInfoConfig:
        return SysInfoConfig(
            enabled=True,
            show_cpu_temp=self._cpu_check.isChecked(),
            show_gpu_temp=self._gpu_check.isChecked(),
            refresh_seconds=self._refresh_spin.value(),
        )

    def _start(self) -> None:
        if not self._device:
            self._status.setText("No device connected")
            return

        def on_error(msg: str) -> None:
            self._status.setText(f"Error: {msg}")

        self._engine = SysInfoEngine(self._device, self._get_sysinfo_config(), on_error=on_error)
        self._engine.start()
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status.setText("System info running")

    def _stop(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine = None
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.setText("System info stopped")
