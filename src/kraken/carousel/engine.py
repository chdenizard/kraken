"""Carousel engine: cycles through images on a background thread."""

from __future__ import annotations

import io
import os
import tempfile
import threading
import time
from typing import TYPE_CHECKING, Callable

from kraken.core.exceptions import CarouselError
from kraken.core.gif import play_animated_gif
from kraken.core.lcd import set_liquid_mode, upload_image, upload_static
from kraken.core.models import CarouselItem
from kraken.sysinfo.collector import collect_stats
from kraken.sysinfo.renderer import render_stats_image

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice
    from kraken.carousel.playlist import Playlist


class CarouselEngine:
    """Background thread that cycles through a playlist of images on the LCD.

    The engine uploads each image, waits for its display_seconds, then moves
    to the next item. It supports stop, pause, and resume operations.
    Special items (sysinfo, liquid) are handled with dedicated logic.
    """

    def __init__(
        self,
        device: KrakenDevice,
        playlist: Playlist,
        loop: bool = True,
        on_item_changed: Callable[[int, CarouselItem], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        sysinfo_refresh_seconds: float = 5.0,
    ) -> None:
        self._device = device
        self._playlist = playlist
        self._loop = loop
        self._on_item_changed = on_item_changed
        self._on_error = on_error
        self._sysinfo_refresh_seconds = sysinfo_refresh_seconds
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        self._thread: threading.Thread | None = None
        self._current_index: int = -1

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    @property
    def current_index(self) -> int:
        return self._current_index

    def start(self) -> None:
        """Start the carousel in a background thread."""
        if self.is_running:
            raise CarouselError("Carousel is already running")
        if not self._playlist:
            raise CarouselError("Playlist is empty")

        self._stop_event.clear()
        self._pause_event.set()
        self._current_index = -1
        self._thread = threading.Thread(
            target=self._run_loop, name="carousel-engine", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the carousel."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock if paused
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        self._current_index = -1

    def pause(self) -> None:
        """Pause the carousel (keeps current image displayed)."""
        if not self.is_running:
            return
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume a paused carousel."""
        self._pause_event.set()

    def _run_loop(self) -> None:
        """Main carousel loop."""
        items = self._playlist.items
        if not items:
            return

        index = 0
        while not self._stop_event.is_set():
            # Wait if paused
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            item = items[index]
            self._current_index = index

            # Notify listener
            if self._on_item_changed:
                try:
                    self._on_item_changed(index, item)
                except Exception:
                    pass

            # Display item based on media_type
            try:
                if item.media_type == "liquid":
                    set_liquid_mode(self._device)
                elif item.media_type == "sysinfo":
                    self._display_sysinfo(item)
                    # _display_sysinfo handles its own timing
                    index += 1
                    if index >= len(items):
                        if self._loop:
                            index = 0
                        else:
                            break
                    continue
                elif item.media_type == "gif":
                    self._play_gif(item)
                    # _play_gif blocks for the full display_seconds window.
                    index += 1
                    if index >= len(items):
                        if self._loop:
                            index = 0
                        else:
                            break
                    continue
                else:
                    upload_image(self._device, item.path)
            except Exception as e:
                if self._on_error:
                    try:
                        self._on_error(f"Item {index} ({item.path}): {e}")
                    except Exception:
                        pass

            # Wait for display duration (interruptible)
            if self._stop_event.wait(timeout=item.display_seconds):
                break

            # Advance to next item
            index += 1
            if index >= len(items):
                if self._loop:
                    index = 0
                else:
                    break

        self._current_index = -1

    def _play_gif(self, item: CarouselItem) -> None:
        """Animate a GIF for item.display_seconds, then return."""
        deadline = time.monotonic() + item.display_seconds
        try:
            play_animated_gif(
                self._device,
                item.path,
                loops=0,
                stop_event=self._stop_event,
                deadline=deadline,
                on_error=self._on_error,
            )
        except Exception as e:
            if self._on_error:
                try:
                    self._on_error(f"gif playback ({item.path}): {e}")
                except Exception:
                    pass

    def _display_sysinfo(self, item: CarouselItem) -> None:
        """Display refreshing sysinfo stats for item.display_seconds."""
        deadline = time.monotonic() + item.display_seconds

        while time.monotonic() < deadline and not self._stop_event.is_set():
            self._pause_event.wait()
            if self._stop_event.is_set():
                return

            try:
                stats = collect_stats(include_cpu=True, include_gpu=True)
                lcd_res = (240, 240)
                if self._device.info:
                    lcd_res = self._device.info.lcd_resolution
                img = render_stats_image(stats, size=lcd_res)

                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(buf.getvalue())
                    tmp_path = tmp.name

                upload_static(self._device, tmp_path)
                os.unlink(tmp_path)
            except Exception as e:
                if self._on_error:
                    try:
                        self._on_error(f"sysinfo render: {e}")
                    except Exception:
                        pass

            # Wait for refresh interval or until deadline
            remaining = deadline - time.monotonic()
            wait_time = min(self._sysinfo_refresh_seconds, max(remaining, 0))
            if wait_time > 0:
                if self._stop_event.wait(timeout=wait_time):
                    return
