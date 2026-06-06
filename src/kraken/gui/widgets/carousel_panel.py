"""Carousel panel: playlist editor with drag-drop and controls."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDoubleSpinBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kraken.carousel.engine import CarouselEngine
from kraken.carousel.playlist import Playlist
from kraken.config.manager import load_config, save_config
from kraken.core.models import CarouselItem

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice


class CarouselPanel(QWidget):
    """Carousel playlist management and controls."""

    def __init__(self, device: KrakenDevice | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device = device
        self._engine: CarouselEngine | None = None
        self._playlist = Playlist()

        layout = QVBoxLayout(self)

        # Playlist
        playlist_group = QGroupBox("Playlist")
        playlist_layout = QVBoxLayout(playlist_group)

        self._list_widget = QListWidget()
        self._list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        playlist_layout.addWidget(self._list_widget)

        # Add/Remove buttons
        btn_layout = QHBoxLayout()

        btn_add = QPushButton("Add Image...")
        btn_add.clicked.connect(self._add_image)
        btn_layout.addWidget(btn_add)

        btn_add_sysinfo = QPushButton("Add SysInfo")
        btn_add_sysinfo.clicked.connect(self._add_sysinfo)
        btn_layout.addWidget(btn_add_sysinfo)

        btn_add_liquid = QPushButton("Add Liquid")
        btn_add_liquid.clicked.connect(self._add_liquid)
        btn_layout.addWidget(btn_add_liquid)

        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._remove_selected)
        btn_layout.addWidget(btn_remove)

        btn_clear = QPushButton("Clear All")
        btn_clear.clicked.connect(self._clear_all)
        btn_layout.addWidget(btn_clear)

        playlist_layout.addLayout(btn_layout)

        # Duration control
        dur_layout = QHBoxLayout()
        dur_layout.addWidget(QLabel("Display duration:"))
        self._duration_spin = QDoubleSpinBox()
        self._duration_spin.setRange(1.0, 300.0)
        self._duration_spin.setValue(10.0)
        self._duration_spin.setSuffix(" s")
        dur_layout.addWidget(self._duration_spin)
        dur_layout.addStretch()
        playlist_layout.addLayout(dur_layout)

        layout.addWidget(playlist_group)

        # Controls
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout(controls_group)

        self._btn_start = QPushButton("Start")
        self._btn_start.clicked.connect(self._start_carousel)
        controls_layout.addWidget(self._btn_start)

        self._btn_pause = QPushButton("Pause")
        self._btn_pause.clicked.connect(self._pause_carousel)
        self._btn_pause.setEnabled(False)
        controls_layout.addWidget(self._btn_pause)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.clicked.connect(self._stop_carousel)
        self._btn_stop.setEnabled(False)
        controls_layout.addWidget(self._btn_stop)

        layout.addWidget(controls_group)

        # Status
        self._status = QLabel("Carousel stopped")
        self._status.setStyleSheet("color: #888;")
        layout.addWidget(self._status)

        layout.addStretch()

        self._load_from_config()

    def set_device(self, device: KrakenDevice) -> None:
        self._device = device

    def _load_from_config(self) -> None:
        try:
            config = load_config()
            self._playlist = Playlist(config.carousel.items)
            self._refresh_list()
        except Exception:
            pass

    def _refresh_list(self) -> None:
        self._list_widget.clear()
        for item in self._playlist.items:
            if item.is_special:
                text = f"[{item.media_type}] ({item.display_seconds}s)"
            else:
                name = Path(item.path).name
                text = f"{name} ({item.media_type}, {item.display_seconds}s)"
            self._list_widget.addItem(text)

    def _add_image(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Images to Carousel",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.gif);;All Files (*)",
        )
        for path in paths:
            try:
                self._playlist.add(path, display_seconds=self._duration_spin.value())
            except Exception as e:
                self._status.setText(f"Error: {e}")
        self._refresh_list()
        self._save_to_config()

    def _add_sysinfo(self) -> None:
        self._playlist.add_special("sysinfo", display_seconds=self._duration_spin.value())
        self._refresh_list()
        self._save_to_config()

    def _add_liquid(self) -> None:
        self._playlist.add_special("liquid", display_seconds=self._duration_spin.value())
        self._refresh_list()
        self._save_to_config()

    def _remove_selected(self) -> None:
        row = self._list_widget.currentRow()
        if row >= 0:
            self._playlist.remove(row)
            self._refresh_list()
            self._save_to_config()

    def _clear_all(self) -> None:
        self._playlist.clear()
        self._refresh_list()
        self._save_to_config()

    def _save_to_config(self) -> None:
        try:
            config = load_config()
            config.carousel.items = self._playlist.items
            save_config(config)
        except Exception:
            pass

    def _start_carousel(self) -> None:
        if not self._playlist:
            self._status.setText("Playlist is empty")
            return

        if not self._device:
            self._status.setText("No device connected")
            return

        def on_changed(index: int, item: CarouselItem) -> None:
            label = f"[{item.media_type}]" if item.is_special else Path(item.path).name
            self._status.setText(f"[{index + 1}/{len(self._playlist)}] {label}")

        def on_engine_error(msg: str) -> None:
            self._status.setText(f"Error: {msg}")

        config = load_config()
        self._engine = CarouselEngine(
            self._device, self._playlist, loop=True,
            on_item_changed=on_changed,
            on_error=on_engine_error,
            sysinfo_refresh_seconds=config.sysinfo.refresh_seconds,
        )
        try:
            self._engine.start()
            self._btn_start.setEnabled(False)
            self._btn_pause.setEnabled(True)
            self._btn_stop.setEnabled(True)
            self._status.setText("Carousel running")
        except Exception as e:
            self._status.setText(f"Error: {e}")

    def _pause_carousel(self) -> None:
        if self._engine and self._engine.is_running:
            if self._engine.is_paused:
                self._engine.resume()
                self._btn_pause.setText("Pause")
                self._status.setText("Carousel resumed")
            else:
                self._engine.pause()
                self._btn_pause.setText("Resume")
                self._status.setText("Carousel paused")

    def _stop_carousel(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine = None
        self._btn_start.setEnabled(True)
        self._btn_pause.setEnabled(False)
        self._btn_pause.setText("Pause")
        self._btn_stop.setEnabled(False)
        self._status.setText("Carousel stopped")
