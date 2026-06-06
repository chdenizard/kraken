"""Animated GIF playback via frame-by-frame static uploads.

The Kraken firmware 2.x for the RGB LCD models (PIDs 0x300C/0x300E/0x3012/
0x3014) ignores GIF animation: only the first frame is shown. To work around
this, we explode the GIF into PNG frames once, cache them on disk, and replay
them as a sequence of static uploads.
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from PIL import Image

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice


CACHE_ROOT = Path.home() / ".cache" / "kraken" / "gif_frames"

# Hardware ceiling: ~120 ms per upload (~8 fps). Frames declaring shorter
# durations are clamped up to this floor so playback never overruns the bus.
MIN_FRAME_INTERVAL_MS = 120
DEFAULT_FRAME_DURATION_MS = 120

FRAME_SIZE = (240, 240)


@dataclass(frozen=True)
class GifFrame:
    """One extracted frame ready to upload."""

    path: Path
    duration_ms: int


def _cache_key(gif_path: Path) -> str:
    """Stable, cheap fingerprint: mtime + size + first 4KB of the file."""
    stat = gif_path.stat()
    h = hashlib.sha1()
    h.update(str(stat.st_mtime_ns).encode())
    h.update(str(stat.st_size).encode())
    with gif_path.open("rb") as f:
        h.update(f.read(4096))
    return h.hexdigest()


def _cache_dir(gif_path: Path, *, root: Path = CACHE_ROOT) -> Path:
    return root / _cache_key(gif_path)


def _is_cache_valid(cache_dir: Path) -> bool:
    if not cache_dir.is_dir():
        return False
    manifest = cache_dir / "manifest.txt"
    if not manifest.is_file():
        return False
    try:
        lines = manifest.read_text().splitlines()
    except OSError:
        return False
    if not lines:
        return False
    for line in lines:
        name, _, _ = line.partition("\t")
        if not (cache_dir / name).is_file():
            return False
    return True


def _read_manifest(cache_dir: Path) -> list[GifFrame]:
    frames: list[GifFrame] = []
    for line in (cache_dir / "manifest.txt").read_text().splitlines():
        name, _, dur = line.partition("\t")
        frames.append(GifFrame(path=cache_dir / name, duration_ms=int(dur)))
    return frames


def extract_frames(
    gif_path: str | Path,
    *,
    cache_root: Path = CACHE_ROOT,
) -> list[GifFrame]:
    """Extract all frames of ``gif_path`` to disk and return them in order.

    Frames are PNG-encoded at 240x240 in ``<cache_root>/<hash>/frame_NNNN.png``.
    Subsequent calls for the same (path, mtime, size, head) reuse the cache.
    """
    src = Path(gif_path).resolve()
    cache_dir = _cache_dir(src, root=cache_root)

    if _is_cache_valid(cache_dir):
        return _read_manifest(cache_dir)

    cache_dir.mkdir(parents=True, exist_ok=True)
    for stale in cache_dir.iterdir():
        if stale.is_file():
            stale.unlink()

    frames: list[GifFrame] = []
    manifest_lines: list[str] = []
    with Image.open(src) as img:
        n_frames = getattr(img, "n_frames", 1)
        for i in range(n_frames):
            img.seek(i)
            duration = int(img.info.get("duration", DEFAULT_FRAME_DURATION_MS) or 0)
            if duration <= 0:
                duration = DEFAULT_FRAME_DURATION_MS

            frame = img.convert("RGB")
            if frame.size != FRAME_SIZE:
                frame = frame.resize(FRAME_SIZE, Image.LANCZOS)

            name = f"frame_{i:04d}.png"
            out_path = cache_dir / name
            frame.save(out_path, format="PNG")

            frames.append(GifFrame(path=out_path, duration_ms=duration))
            manifest_lines.append(f"{name}\t{duration}")

    (cache_dir / "manifest.txt").write_text("\n".join(manifest_lines))
    return frames


def play_animated_gif(
    device: KrakenDevice,
    gif_path: str | Path,
    *,
    loops: int = 0,
    stop_event: threading.Event | None = None,
    deadline: float | None = None,
    on_frame: Callable[[int, int], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    cache_root: Path = CACHE_ROOT,
) -> None:
    """Play ``gif_path`` frame-by-frame on the LCD.

    Blocking. Uploads each frame as a static image, sleeping for at least
    ``MIN_FRAME_INTERVAL_MS`` between frames (and longer if the GIF declares
    a slower native rate).

    Each upload goes through ``device.set_screen("static", ...)`` which
    already drains the HID queue (workaround in commit 3d8009b).

    Args:
        loops: Number of full passes. ``0`` means loop forever (until
            ``stop_event``/``deadline``).
        stop_event: Cooperative cancel — checked between frames.
        deadline: ``time.monotonic()`` value at which playback must stop.
        on_frame: Called as ``(frame_index, total_frames)`` after each upload.
        on_error: Called with a string when a single frame upload fails;
            playback continues with the next frame.
    """
    frames = extract_frames(gif_path, cache_root=cache_root)
    if not frames:
        return

    total = len(frames)
    loop_count = 0
    while True:
        for i, frame in enumerate(frames):
            if stop_event is not None and stop_event.is_set():
                return
            if deadline is not None and time.monotonic() >= deadline:
                return

            try:
                device.set_screen("static", str(frame.path))
            except Exception as e:
                if on_error is not None:
                    try:
                        on_error(f"frame {i}: {e}")
                    except Exception:
                        pass

            if on_frame is not None:
                try:
                    on_frame(i, total)
                except Exception:
                    pass

            wait_ms = max(MIN_FRAME_INTERVAL_MS, frame.duration_ms)
            wait_s = wait_ms / 1000.0
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                wait_s = min(wait_s, remaining)
            if stop_event is not None:
                if stop_event.wait(timeout=wait_s):
                    return
            else:
                time.sleep(wait_s)

        loop_count += 1
        if loops and loop_count >= loops:
            return
