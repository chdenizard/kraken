"""Tests for LCD operations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kraken.core.exceptions import ImageValidationError, LCDError
from kraken.core.lcd import (
    set_brightness,
    set_liquid_mode,
    set_orientation,
    upload_gif,
    upload_image,
    upload_static,
    validate_image_file,
)


@pytest.fixture
def mock_device() -> MagicMock:
    dev = MagicMock()
    dev.set_screen = MagicMock()
    return dev


@pytest.fixture
def png_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return f


@pytest.fixture
def gif_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.gif"
    f.write_bytes(b"GIF89a" + b"\x00" * 100)
    return f


class TestValidateImageFile:
    def test_valid_png(self, png_file: Path) -> None:
        result = validate_image_file(png_file)
        assert result == png_file.resolve()

    def test_valid_gif(self, gif_file: Path) -> None:
        result = validate_image_file(gif_file)
        assert result == gif_file.resolve()

    def test_file_not_found(self) -> None:
        with pytest.raises(ImageValidationError, match="not found"):
            validate_image_file("/nonexistent/image.png")

    def test_unsupported_format(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("not an image")
        with pytest.raises(ImageValidationError, match="Unsupported"):
            validate_image_file(f)

    def test_directory_not_file(self, tmp_path: Path) -> None:
        with pytest.raises(ImageValidationError, match="Not a file"):
            validate_image_file(tmp_path)

    def test_supported_extensions(self, tmp_path: Path) -> None:
        for ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"]:
            f = tmp_path / f"test{ext}"
            f.write_bytes(b"\x00" * 10)
            assert validate_image_file(f).suffix == ext


class TestUploadStatic:
    def test_upload_png(self, mock_device: MagicMock, png_file: Path) -> None:
        upload_static(mock_device, png_file)
        mock_device.set_screen.assert_called_once_with("static", str(png_file.resolve()))

    def test_reject_gif(self, mock_device: MagicMock, gif_file: Path) -> None:
        with pytest.raises(ImageValidationError, match="upload_gif"):
            upload_static(mock_device, gif_file)

    def test_device_error(self, mock_device: MagicMock, png_file: Path) -> None:
        mock_device.set_screen.side_effect = RuntimeError("USB error")
        with pytest.raises(LCDError, match="Failed to upload"):
            upload_static(mock_device, png_file)


class TestUploadGif:
    def test_upload_gif_delegates_to_player(self, mock_device: MagicMock, gif_file: Path) -> None:
        with patch("kraken.core.gif.play_animated_gif") as mock_play:
            upload_gif(mock_device, gif_file)
            mock_play.assert_called_once()
            args, kwargs = mock_play.call_args
            assert args[0] is mock_device
            assert Path(args[1]) == gif_file.resolve()
            assert kwargs.get("loops") == 1

    def test_reject_png(self, mock_device: MagicMock, png_file: Path) -> None:
        with pytest.raises(ImageValidationError, match="Expected a GIF"):
            upload_gif(mock_device, png_file)

    def test_player_failure_wraps_in_lcd_error(self, mock_device: MagicMock,
                                                gif_file: Path) -> None:
        with patch("kraken.core.gif.play_animated_gif", side_effect=RuntimeError("boom")):
            with pytest.raises(LCDError, match="Failed to play GIF"):
                upload_gif(mock_device, gif_file)


class TestUploadImage:
    def test_auto_static(self, mock_device: MagicMock, png_file: Path) -> None:
        upload_image(mock_device, png_file)
        mock_device.set_screen.assert_called_once_with("static", str(png_file.resolve()))

    def test_auto_gif(self, mock_device: MagicMock, gif_file: Path) -> None:
        with patch("kraken.core.gif.play_animated_gif") as mock_play:
            upload_image(mock_device, gif_file)
            mock_play.assert_called_once()


class TestSetLiquidMode:
    def test_success(self, mock_device: MagicMock) -> None:
        set_liquid_mode(mock_device)
        mock_device.set_screen.assert_called_once_with("liquid")

    def test_device_error(self, mock_device: MagicMock) -> None:
        mock_device.set_screen.side_effect = RuntimeError("fail")
        with pytest.raises(LCDError):
            set_liquid_mode(mock_device)


class TestSetBrightness:
    def test_valid_values(self, mock_device: MagicMock) -> None:
        for val in [0, 50, 100]:
            mock_device.reset_mock()
            set_brightness(mock_device, val)
            mock_device.set_screen.assert_called_once_with("brightness", val)

    def test_invalid_high(self, mock_device: MagicMock) -> None:
        with pytest.raises(ValueError, match="Brightness"):
            set_brightness(mock_device, 101)

    def test_invalid_negative(self, mock_device: MagicMock) -> None:
        with pytest.raises(ValueError, match="Brightness"):
            set_brightness(mock_device, -1)


class TestSetOrientation:
    def test_valid_values(self, mock_device: MagicMock) -> None:
        for deg in [0, 90, 180, 270]:
            mock_device.reset_mock()
            set_orientation(mock_device, deg)
            mock_device.set_screen.assert_called_once_with("orientation", deg)

    def test_invalid_value(self, mock_device: MagicMock) -> None:
        with pytest.raises(ValueError, match="Orientation"):
            set_orientation(mock_device, 45)
