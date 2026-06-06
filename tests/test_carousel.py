"""Tests for carousel playlist and engine."""

import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from kraken.carousel.engine import CarouselEngine
from kraken.carousel.playlist import Playlist
from kraken.core.exceptions import CarouselError


def _make_image(tmp_path: Path, name: str) -> Path:
    f = tmp_path / name
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return f


class TestPlaylist:
    def test_empty(self) -> None:
        pl = Playlist()
        assert len(pl) == 0
        assert not pl

    def test_add(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        item = pl.add(img, display_seconds=5.0)
        assert len(pl) == 1
        assert item.media_type == "static"
        assert item.display_seconds == 5.0

    def test_add_at_position(self, tmp_path: Path) -> None:
        a = _make_image(tmp_path, "a.png")
        b = _make_image(tmp_path, "b.png")
        c = _make_image(tmp_path, "c.png")
        pl = Playlist()
        pl.add(a)
        pl.add(c)
        pl.add(b, position=1)
        assert pl.get(1).path == str(b.resolve())

    def test_add_invalid_position(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        with pytest.raises(CarouselError, match="Position"):
            pl.add(img, position=5)

    def test_remove(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img)
        removed = pl.remove(0)
        assert removed.path == str(img.resolve())
        assert len(pl) == 0

    def test_remove_invalid_index(self) -> None:
        pl = Playlist()
        with pytest.raises(CarouselError, match="Index"):
            pl.remove(0)

    def test_move(self, tmp_path: Path) -> None:
        a = _make_image(tmp_path, "a.png")
        b = _make_image(tmp_path, "b.png")
        pl = Playlist()
        pl.add(a)
        pl.add(b)
        pl.move(0, 1)
        assert pl.get(0).path == str(b.resolve())
        assert pl.get(1).path == str(a.resolve())

    def test_clear(self, tmp_path: Path) -> None:
        pl = Playlist()
        pl.add(_make_image(tmp_path, "a.png"))
        pl.add(_make_image(tmp_path, "b.png"))
        pl.clear()
        assert len(pl) == 0

    def test_validate_paths(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img)
        assert pl.validate_paths() == []

        img.unlink()
        errors = pl.validate_paths()
        assert len(errors) == 1

    def test_add_special_sysinfo(self) -> None:
        pl = Playlist()
        item = pl.add_special("sysinfo", display_seconds=15)
        assert len(pl) == 1
        assert item.media_type == "sysinfo"
        assert item.display_seconds == 15
        assert item.path == ""
        assert item.is_special is True

    def test_add_special_liquid(self) -> None:
        pl = Playlist()
        item = pl.add_special("liquid", display_seconds=10)
        assert len(pl) == 1
        assert item.media_type == "liquid"
        assert item.is_special is True

    def test_add_special_invalid_type(self) -> None:
        pl = Playlist()
        with pytest.raises(CarouselError, match="Not a special"):
            pl.add_special("static")

    def test_add_special_at_position(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img)
        pl.add_special("sysinfo", position=0)
        assert pl.get(0).media_type == "sysinfo"
        assert pl.get(1).media_type == "static"

    def test_validate_paths_skips_special(self) -> None:
        pl = Playlist()
        pl.add_special("sysinfo")
        pl.add_special("liquid")
        assert pl.validate_paths() == []

    def test_gif_detection(self, tmp_path: Path) -> None:
        f = tmp_path / "anim.gif"
        f.write_bytes(b"GIF89a" + b"\x00" * 100)
        pl = Playlist()
        item = pl.add(f)
        assert item.media_type == "gif"


class TestCarouselEngine:
    def test_start_stop(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img, display_seconds=0.1)

        device = MagicMock()
        engine = CarouselEngine(device, pl)
        engine.start()
        assert engine.is_running
        time.sleep(0.2)
        engine.stop()
        assert not engine.is_running

    def test_empty_playlist_raises(self) -> None:
        device = MagicMock()
        pl = Playlist()
        engine = CarouselEngine(device, pl)
        with pytest.raises(CarouselError, match="empty"):
            engine.start()

    def test_double_start_raises(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img, display_seconds=1.0)

        device = MagicMock()
        engine = CarouselEngine(device, pl)
        engine.start()
        try:
            with pytest.raises(CarouselError, match="already running"):
                engine.start()
        finally:
            engine.stop()

    def test_callback_on_item_changed(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img, display_seconds=0.1)

        device = MagicMock()
        callback = MagicMock()
        engine = CarouselEngine(device, pl, on_item_changed=callback)
        engine.start()
        time.sleep(0.2)
        engine.stop()
        assert callback.called
        args = callback.call_args[0]
        assert args[0] == 0  # index

    def test_no_loop_stops(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img, display_seconds=0.1)

        device = MagicMock()
        engine = CarouselEngine(device, pl, loop=False)
        engine.start()
        time.sleep(0.5)
        assert not engine.is_running

    def test_liquid_item_calls_set_liquid_mode(self) -> None:
        pl = Playlist()
        pl.add_special("liquid", display_seconds=0.2)

        device = MagicMock()
        with patch("kraken.carousel.engine.set_liquid_mode") as mock_liquid:
            engine = CarouselEngine(device, pl, loop=False)
            engine.start()
            time.sleep(0.5)
            engine.stop()
            mock_liquid.assert_called_once_with(device)

    def test_sysinfo_item_renders_and_uploads(self) -> None:
        pl = Playlist()
        pl.add_special("sysinfo", display_seconds=0.3)

        device = MagicMock()
        device.info = None

        with patch("kraken.carousel.engine.collect_stats") as mock_stats, \
             patch("kraken.carousel.engine.render_stats_image") as mock_render, \
             patch("kraken.carousel.engine.upload_static") as mock_upload:
            from kraken.sysinfo.collector import SystemStats
            mock_stats.return_value = SystemStats(cpu_temp_c=45.0, gpu_temp_c=None)
            from PIL import Image
            mock_render.return_value = Image.new("RGB", (240, 240))

            engine = CarouselEngine(device, pl, loop=False, sysinfo_refresh_seconds=0.1)
            engine.start()
            time.sleep(0.6)
            engine.stop()
            assert mock_stats.call_count >= 1
            assert mock_upload.call_count >= 1

    def test_gif_item_routes_to_player(self, tmp_path: Path) -> None:
        f = tmp_path / "anim.gif"
        f.write_bytes(b"GIF89a" + b"\x00" * 100)
        pl = Playlist()
        pl.add(f, display_seconds=0.2)

        device = MagicMock()
        with patch("kraken.carousel.engine.play_animated_gif") as mock_play:
            engine = CarouselEngine(device, pl, loop=False)
            engine.start()
            time.sleep(0.5)
            engine.stop()

            mock_play.assert_called_once()
            kwargs = mock_play.call_args.kwargs
            assert kwargs.get("loops") == 0
            assert kwargs.get("stop_event") is engine._stop_event
            assert kwargs.get("deadline") is not None

    def test_pause_resume(self, tmp_path: Path) -> None:
        img = _make_image(tmp_path, "a.png")
        pl = Playlist()
        pl.add(img, display_seconds=0.1)

        device = MagicMock()
        engine = CarouselEngine(device, pl)
        engine.start()
        engine.pause()
        assert engine.is_paused
        engine.resume()
        assert not engine.is_paused
        time.sleep(0.2)
        engine.stop()
