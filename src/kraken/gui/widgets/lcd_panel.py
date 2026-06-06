"""LCD panel: image upload, brightness, orientation controls."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from kraken.gui.threads import GifPlaybackWorker, LCDUploadWorker

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice


class LCDPanel(QWidget):
    """LCD management panel."""

    def __init__(self, device: KrakenDevice | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device = device
        self._current_worker: LCDUploadWorker | None = None
        self._gif_worker: GifPlaybackWorker | None = None
        self._selected_file: str | None = None

        layout = QVBoxLayout(self)

        # Preview
        preview_group = QGroupBox("LCD Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview = QLabel("No image selected")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setMinimumSize(240, 240)
        self._preview.setMaximumSize(640, 640)
        self._preview.setStyleSheet("background-color: #111; border: 1px solid #333;")
        preview_layout.addWidget(self._preview)

        layout.addWidget(preview_group)

        # File selection
        file_group = QGroupBox("Image")
        file_layout = QHBoxLayout(file_group)

        self._file_label = QLabel("No file selected")
        self._file_label.setStyleSheet("color: #aaa;")
        file_layout.addWidget(self._file_label, 1)

        btn_choose = QPushButton("Choose Image/GIF...")
        btn_choose.clicked.connect(self._choose_file)
        file_layout.addWidget(btn_choose)

        btn_upload = QPushButton("Upload")
        btn_upload.clicked.connect(self._upload_image)
        file_layout.addWidget(btn_upload)

        self._btn_stop_gif = QPushButton("Stop GIF")
        self._btn_stop_gif.clicked.connect(self._stop_gif)
        self._btn_stop_gif.setVisible(False)
        file_layout.addWidget(self._btn_stop_gif)

        layout.addWidget(file_group)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Brightness
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(QLabel("Brightness:"))
        self._brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self._brightness_slider.setRange(0, 100)
        self._brightness_slider.setValue(50)
        bright_layout.addWidget(self._brightness_slider, 1)
        self._brightness_label = QLabel("50%")
        self._brightness_slider.valueChanged.connect(
            lambda v: self._brightness_label.setText(f"{v}%")
        )
        bright_layout.addWidget(self._brightness_label)
        btn_bright = QPushButton("Apply")
        btn_bright.clicked.connect(self._apply_brightness)
        bright_layout.addWidget(btn_bright)
        controls_layout.addLayout(bright_layout)

        # Orientation
        orient_layout = QHBoxLayout()
        orient_layout.addWidget(QLabel("Orientation:"))
        self._orientation_combo = QComboBox()
        self._orientation_combo.addItems(["0", "90", "180", "270"])
        orient_layout.addWidget(self._orientation_combo)
        btn_orient = QPushButton("Apply")
        btn_orient.clicked.connect(self._apply_orientation)
        orient_layout.addWidget(btn_orient)
        orient_layout.addStretch()
        controls_layout.addLayout(orient_layout)

        # Liquid mode
        btn_liquid = QPushButton("Liquid Temperature Mode")
        btn_liquid.clicked.connect(self._set_liquid_mode)
        controls_layout.addWidget(btn_liquid)

        layout.addWidget(controls_group)

        # Status
        self._status = QLabel("")
        self._status.setStyleSheet("color: #888;")
        layout.addWidget(self._status)

        layout.addStretch()

    def set_device(self, device: KrakenDevice) -> None:
        self._device = device

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Image or GIF",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;All Files (*)",
        )
        if path:
            self._selected_file = path
            self._file_label.setText(Path(path).name)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    240, 240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._preview.setPixmap(scaled)

    def _upload_image(self) -> None:
        if not self._selected_file:
            self._status.setText("No file selected.")
            return

        ext = Path(self._selected_file).suffix.lower()

        if ext == ".gif":
            self._start_gif_playback(self._selected_file)
            return

        self._current_worker = LCDUploadWorker(self._device, "static", self._selected_file)
        self._current_worker.upload_complete.connect(
            lambda: self._status.setText("Upload complete!")
        )
        self._current_worker.upload_error.connect(
            lambda e: self._status.setText(f"Error: {e}")
        )
        self._current_worker.start()
        self._status.setText("Uploading...")

    def _start_gif_playback(self, gif_path: str) -> None:
        # Cancel any existing playback before starting a new one.
        self._stop_gif()
        worker = GifPlaybackWorker(self._device, gif_path, loops=0)
        worker.frame_changed.connect(self._on_gif_frame)
        worker.playback_stopped.connect(self._on_gif_stopped)
        worker.playback_error.connect(self._on_gif_error)
        self._gif_worker = worker
        self._btn_stop_gif.setVisible(True)
        self._status.setText("Playing GIF…")
        worker.start()

    def _stop_gif(self) -> None:
        worker = self._gif_worker
        if worker is None:
            return
        worker.request_stop()
        worker.wait(3000)
        self._gif_worker = None
        self._btn_stop_gif.setVisible(False)

    def _on_gif_frame(self, index: int, total: int) -> None:
        self._status.setText(f"Playing GIF — frame {index + 1}/{total}")

    def _on_gif_stopped(self) -> None:
        self._gif_worker = None
        self._btn_stop_gif.setVisible(False)
        self._status.setText("GIF playback stopped.")

    def _on_gif_error(self, msg: str) -> None:
        self._status.setText(f"GIF error: {msg}")

    def _apply_brightness(self) -> None:
        value = self._brightness_slider.value()
        worker = LCDUploadWorker(self._device, "brightness", value)
        worker.upload_complete.connect(lambda: self._status.setText(f"Brightness set to {value}%"))
        worker.upload_error.connect(lambda e: self._status.setText(f"Error: {e}"))
        worker.start()
        self._current_worker = worker

    def _apply_orientation(self) -> None:
        degrees = int(self._orientation_combo.currentText())
        worker = LCDUploadWorker(self._device, "orientation", degrees)
        worker.upload_complete.connect(
            lambda: self._status.setText(f"Orientation set to {degrees}")
        )
        worker.upload_error.connect(lambda e: self._status.setText(f"Error: {e}"))
        worker.start()
        self._current_worker = worker

    def _set_liquid_mode(self) -> None:
        worker = LCDUploadWorker(self._device, "liquid")
        worker.upload_complete.connect(lambda: self._status.setText("Liquid mode set"))
        worker.upload_error.connect(lambda e: self._status.setText(f"Error: {e}"))
        worker.start()
        self._current_worker = worker
