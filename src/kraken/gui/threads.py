"""QThread workers for background operations."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal

from kraken.core.models import CarouselItem, SensorData
from kraken.core.sensors import read_sensors

if TYPE_CHECKING:
    from kraken.carousel.engine import CarouselEngine
    from kraken.core.device import KrakenDevice
    from kraken.sysinfo.renderer import SysInfoEngine


class SensorWorker(QThread):
    """Polls hwmon sensors at a regular interval."""

    data_updated = Signal(SensorData)
    error_occurred = Signal(str)

    def __init__(self, hwmon_path: Path | None = None, interval_ms: int = 2000) -> None:
        super().__init__()
        self.hwmon_path = hwmon_path
        self.interval_ms = interval_ms
        self._running = True

    def run(self) -> None:
        while self._running:
            try:
                data = read_sensors(hwmon_path=self.hwmon_path)
                self.data_updated.emit(data)
            except Exception as e:
                self.error_occurred.emit(str(e))
            self.msleep(self.interval_ms)

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class LCDUploadWorker(QThread):
    """Uploads an image to the LCD in background using the shared device."""

    upload_complete = Signal()
    upload_error = Signal(str)

    def __init__(self, device: KrakenDevice, mode: str, value: str | int | None = None) -> None:
        super().__init__()
        self._device = device
        self._mode = mode
        self._value = value

    def run(self) -> None:
        try:
            from kraken.core import lcd as lcd_ops

            if self._device is None:
                raise RuntimeError("No device available")

            if self._mode == "static":
                lcd_ops.upload_static(self._device, self._value)
            elif self._mode == "gif":
                lcd_ops.upload_gif(self._device, self._value)
            elif self._mode == "liquid":
                lcd_ops.set_liquid_mode(self._device)
            elif self._mode == "brightness":
                lcd_ops.set_brightness(self._device, self._value)
            elif self._mode == "orientation":
                lcd_ops.set_orientation(self._device, self._value)

            self.upload_complete.emit()
        except Exception as e:
            self.upload_error.emit(str(e))


class GifPlaybackWorker(QThread):
    """Plays an animated GIF on the LCD frame-by-frame.

    Emits ``frame_changed(index, total)`` after each frame upload, plus
    ``playback_stopped()`` when the loop exits cleanly and
    ``playback_error(str)`` on a fatal error.
    """

    frame_changed = Signal(int, int)
    playback_stopped = Signal()
    playback_error = Signal(str)

    def __init__(self, device: KrakenDevice, gif_path: str, loops: int = 0) -> None:
        super().__init__()
        self._device = device
        self._gif_path = gif_path
        self._loops = loops
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        try:
            from kraken.core.gif import play_animated_gif

            if self._device is None:
                raise RuntimeError("No device available")

            play_animated_gif(
                self._device,
                self._gif_path,
                loops=self._loops,
                stop_event=self._stop_event,
                on_frame=lambda i, n: self.frame_changed.emit(i, n),
                on_error=lambda msg: self.playback_error.emit(msg),
            )
            self.playback_stopped.emit()
        except Exception as e:
            self.playback_error.emit(str(e))
