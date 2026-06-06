"""Device info and settings panel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kraken.config.paths import get_config_file

if TYPE_CHECKING:
    from kraken.core.models import DeviceInfo


class DeviceInfoPanel(QWidget):
    """Device information and configuration panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QVBoxLayout(info_group)

        self._info_labels: dict[str, QLabel] = {}
        for field in ["Device", "Firmware", "LCD Resolution", "Serial", "Product ID"]:
            row = QLabel(f"{field}: --")
            row.setStyleSheet("font-size: 13px;")
            info_layout.addWidget(row)
            self._info_labels[field] = row

        layout.addWidget(info_group)

        # Config
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)

        config_path = QLabel(f"Config file: {get_config_file()}")
        config_path.setStyleSheet("font-size: 12px; color: #aaa;")
        config_layout.addWidget(config_path)

        btn_open = QPushButton("Open Config File")
        btn_open.clicked.connect(self._open_config)
        config_layout.addWidget(btn_open)

        layout.addWidget(config_group)
        layout.addStretch()

    def update_info(self, info: DeviceInfo) -> None:
        self._info_labels["Device"].setText(f"Device: {info.description}")
        self._info_labels["Firmware"].setText(f"Firmware: {info.firmware_version}")
        self._info_labels["LCD Resolution"].setText(
            f"LCD Resolution: {info.lcd_resolution[0]}x{info.lcd_resolution[1]}"
        )
        self._info_labels["Serial"].setText(f"Serial: {info.serial_number}")
        self._info_labels["Product ID"].setText(f"Product ID: 0x{info.product_id:04X}")

    def _open_config(self) -> None:
        import subprocess
        import os

        config_file = get_config_file()
        editor = os.environ.get("EDITOR", "xdg-open")
        try:
            subprocess.Popen([editor, str(config_file)])
        except FileNotFoundError:
            pass
