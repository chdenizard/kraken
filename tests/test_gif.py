"""Tests for animated-GIF frame extraction and playback."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from kraken.core import gif as gif_mod
from kraken.core.gif import (
    GifFrame,
    MIN_FRAME_INTERVAL_MS,
    extract_frames,
    play_animated_gif,
)


def _make_gif(path: Path, *, frames: int = 3, duration: int = 50,
              size: tuple[int, int] = (32, 32)) -> Path:
    """Build a tiny multi-frame GIF for tests."""
    imgs = []
    for i in range(frames):
        img = Image.new("RGB", size, color=(i * 80 % 255, 0, 0))
        imgs.append(img)
    imgs[0].save(
        path,
        save_all=True,
        append_images=imgs[1:],
        format="GIF",
        duration=duration,
        loop=0,
    )
    return path


class TestExtractFrames:
    def test_extract_creates_cache(self, tmp_path: Path) -> None:
        gif = _make_gif(tmp_path / "a.gif", frames=3, duration=80)
        cache_root = tmp_path / "cache"

        frames = extract_frames(gif, cache_root=cache_root)

        assert len(frames) == 3
        for f in frames:
            assert f.path.exists()
            assert f.path.suffix == ".png"
            assert f.duration_ms == 80
            with Image.open(f.path) as im:
                assert im.size == (240, 240)

    def test_extract_uses_cache(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        gif = _make_gif(tmp_path / "a.gif", frames=2)
        cache_root = tmp_path / "cache"
        first = extract_frames(gif, cache_root=cache_root)

        # Block any further PIL.Image.open call — the second extraction must
        # be served from the manifest without reopening the source GIF.
        def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("Image.open should not be called on cache hit")

        monkeypatch.setattr(gif_mod.Image, "open", _boom)

        second = extract_frames(gif, cache_root=cache_root)
        assert [f.path for f in second] == [f.path for f in first]
        assert [f.duration_ms for f in second] == [f.duration_ms for f in first]

    def test_extract_invalidates_on_mtime(self, tmp_path: Path) -> None:
        gif = _make_gif(tmp_path / "a.gif", frames=2, duration=50)
        cache_root = tmp_path / "cache"
        first = extract_frames(gif, cache_root=cache_root)
        first_dir = first[0].path.parent

        # Rebuild the GIF with a different shape and bump mtime.
        time.sleep(0.01)
        _make_gif(gif, frames=4, duration=120)
        new_mtime = time.time()
        os.utime(gif, (new_mtime, new_mtime))

        second = extract_frames(gif, cache_root=cache_root)
        assert len(second) == 4
        assert second[0].duration_ms == 120
        # New cache directory because the hash changed.
        assert second[0].path.parent != first_dir

    def test_extract_zero_duration_falls_back_to_default(self, tmp_path: Path) -> None:
        gif = _make_gif(tmp_path / "a.gif", frames=2, duration=0)
        cache_root = tmp_path / "cache"
        frames = extract_frames(gif, cache_root=cache_root)
        assert all(f.duration_ms > 0 for f in frames)


class TestPlayAnimatedGif:
    def _three_frames(self, tmp_path: Path) -> list[GifFrame]:
        out = []
        for i in range(3):
            p = tmp_path / f"frame_{i}.png"
            p.write_bytes(b"\x89PNG\r\n\x1a\n")
            out.append(GifFrame(path=p, duration_ms=10))
        return out

    def test_loops_count(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        frames = self._three_frames(tmp_path)
        monkeypatch.setattr(gif_mod, "extract_frames", lambda *a, **kw: frames)
        monkeypatch.setattr(gif_mod, "MIN_FRAME_INTERVAL_MS", 0)
        monkeypatch.setattr(gif_mod.time, "sleep", lambda _s: None)

        device = MagicMock()
        play_animated_gif(device, "ignored.gif", loops=2)

        assert device.set_screen.call_count == 6
        called_paths = [c.args[1] for c in device.set_screen.call_args_list]
        expected = [str(frames[i % 3].path) for i in range(6)]
        assert called_paths == expected

    def test_stop_event_interrupts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        frames = self._three_frames(tmp_path)
        monkeypatch.setattr(gif_mod, "extract_frames", lambda *a, **kw: frames)
        monkeypatch.setattr(gif_mod, "MIN_FRAME_INTERVAL_MS", 0)

        evt = threading.Event()
        device = MagicMock()

        def _stop_after_first(*_args, **_kwargs):
            if device.set_screen.call_count >= 1:
                evt.set()

        device.set_screen.side_effect = _stop_after_first

        play_animated_gif(device, "ignored.gif", loops=0, stop_event=evt)
        assert device.set_screen.call_count == 1

    def test_deadline_stops_loops(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        frames = self._three_frames(tmp_path)
        monkeypatch.setattr(gif_mod, "extract_frames", lambda *a, **kw: frames)
        monkeypatch.setattr(gif_mod, "MIN_FRAME_INTERVAL_MS", 0)
        monkeypatch.setattr(gif_mod.time, "sleep", lambda _s: None)

        device = MagicMock()
        deadline = time.monotonic() + 0.05
        play_animated_gif(device, "ignored.gif", loops=0, deadline=deadline)

        # Without the deadline this would never return (loops=0 = infinite).
        assert device.set_screen.called

    def test_min_frame_interval_enforced(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        frame = GifFrame(path=tmp_path / "f.png", duration_ms=10)
        frame.path.write_bytes(b"")
        monkeypatch.setattr(gif_mod, "extract_frames", lambda *a, **kw: [frame])

        slept: list[float] = []
        monkeypatch.setattr(gif_mod.time, "sleep", lambda s: slept.append(s))

        device = MagicMock()
        play_animated_gif(device, "ignored.gif", loops=1)

        assert slept, "expected at least one inter-frame sleep"
        assert slept[0] == pytest.approx(MIN_FRAME_INTERVAL_MS / 1000.0)

    def test_on_frame_callback(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        frames = self._three_frames(tmp_path)
        monkeypatch.setattr(gif_mod, "extract_frames", lambda *a, **kw: frames)
        monkeypatch.setattr(gif_mod, "MIN_FRAME_INTERVAL_MS", 0)
        monkeypatch.setattr(gif_mod.time, "sleep", lambda _s: None)

        device = MagicMock()
        seen: list[tuple[int, int]] = []
        play_animated_gif(device, "ignored.gif", loops=1,
                          on_frame=lambda i, n: seen.append((i, n)))

        assert seen == [(0, 3), (1, 3), (2, 3)]

    def test_frame_error_is_swallowed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        frames = self._three_frames(tmp_path)
        monkeypatch.setattr(gif_mod, "extract_frames", lambda *a, **kw: frames)
        monkeypatch.setattr(gif_mod, "MIN_FRAME_INTERVAL_MS", 0)
        monkeypatch.setattr(gif_mod.time, "sleep", lambda _s: None)

        device = MagicMock()
        device.set_screen.side_effect = [RuntimeError("usb"), None, None]
        errors: list[str] = []

        play_animated_gif(
            device, "ignored.gif", loops=1,
            on_error=lambda msg: errors.append(msg),
        )

        assert device.set_screen.call_count == 3
        assert len(errors) == 1
        assert "frame 0" in errors[0]
