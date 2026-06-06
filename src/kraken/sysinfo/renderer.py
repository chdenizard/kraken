"""Render system stats as an image for the Kraken LCD."""

from __future__ import annotations

import io
import threading
from typing import TYPE_CHECKING, Callable

from PIL import Image, ImageDraw, ImageFont

from kraken.core.lcd import upload_static
from kraken.sysinfo.collector import SystemStats, collect_stats

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice
    from kraken.core.models import SysInfoConfig

# Color palette
BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
LABEL_COLOR = (180, 180, 180)


def _temp_color(temp: float) -> tuple[int, int, int]:
    """Map temperature to a color (blue -> green -> red)."""
    if temp <= 30:
        return (0, 120, 255)
    elif temp <= 50:
        t = (temp - 30) / 20.0
        r = int(255 * t)
        g = int(200 * (1 - t) + 120 * t)
        b = int(255 * (1 - t))
        return (r, g, b)
    elif temp <= 70:
        t = (temp - 50) / 20.0
        return (255, int(120 * (1 - t)), 0)
    else:
        return (255, 0, 0)


def render_stats_image(
    stats: SystemStats,
    size: tuple[int, int] = (240, 240),
) -> Image.Image:
    """Render system stats as a PIL Image.

    Args:
        stats: System stats to render.
        size: Image dimensions (width, height).

    Returns:
        PIL Image ready for upload.
    """
    img = Image.new("RGB", size, BG_COLOR)
    draw = ImageDraw.Draw(img)

    w, h = size

    # Count active sensors to adjust layout
    sensors = []
    if stats.cpu_temp_c is not None:
        sensors.append(("CPU", stats.cpu_temp_c))
    if stats.gpu_temp_c is not None:
        sensors.append(("GPU", stats.gpu_temp_c))

    single = len(sensors) == 1

    try:
        if single:
            font_temp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", w // 3)
            font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", w // 8)
        else:
            font_temp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", w // 5)
            font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", w // 10)
    except (OSError, IOError):
        font_temp = ImageFont.load_default()
        font_label = ImageFont.load_default()

    if single:
        label, temp = sensors[0]
        color = _temp_color(temp)
        temp_text = f"{temp:.0f}\u00b0C"

        y_offset = h // 6
        draw.text((w // 2, y_offset), label, fill=LABEL_COLOR, font=font_label, anchor="mt")
        y_offset += h // 5
        draw.text((w // 2, y_offset), temp_text, fill=color, font=font_temp, anchor="mt")
        y_offset += h // 3

        # Temperature bar
        bar_x = w // 8
        bar_w = w - 2 * bar_x
        bar_h = h // 12
        draw.rounded_rectangle([bar_x, y_offset, bar_x + bar_w, y_offset + bar_h], radius=bar_h // 2, outline=(60, 60, 60))
        fill_w = int(bar_w * min(temp / 100.0, 1.0))
        if fill_w > 0:
            draw.rounded_rectangle([bar_x, y_offset, bar_x + fill_w, y_offset + bar_h], radius=bar_h // 2, fill=color)
    else:
        y_offset = h // 16
        for label, temp in sensors:
            color = _temp_color(temp)
            temp_text = f"{temp:.0f}\u00b0C"

            draw.text((w // 2, y_offset), label, fill=LABEL_COLOR, font=font_label, anchor="mt")
            y_offset += h // 8
            draw.text((w // 2, y_offset), temp_text, fill=color, font=font_temp, anchor="mt")
            y_offset += h // 5

            # Temperature bar
            bar_x = w // 8
            bar_w = w - 2 * bar_x
            bar_h = h // 16
            draw.rounded_rectangle([bar_x, y_offset, bar_x + bar_w, y_offset + bar_h], radius=bar_h // 2, outline=(60, 60, 60))
            fill_w = int(bar_w * min(temp / 100.0, 1.0))
            if fill_w > 0:
                draw.rounded_rectangle([bar_x, y_offset, bar_x + fill_w, y_offset + bar_h], radius=bar_h // 2, fill=color)
            y_offset += h // 8

    return img


class SysInfoEngine:
    """Background thread that periodically renders system stats to the LCD."""

    def __init__(
        self,
        device: KrakenDevice,
        config: SysInfoConfig,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._device = device
        self._config = config
        self._on_error = on_error
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="sysinfo-engine", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _run_loop(self) -> None:
        import os
        import tempfile

        lcd_res = (240, 240)
        if self._device.info:
            lcd_res = self._device.info.lcd_resolution

        while not self._stop_event.is_set():
            try:
                stats = collect_stats(
                    include_cpu=self._config.show_cpu_temp,
                    include_gpu=self._config.show_gpu_temp,
                )
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
                        self._on_error(str(e))
                    except Exception:
                        pass

            self._stop_event.wait(timeout=self._config.refresh_seconds)
