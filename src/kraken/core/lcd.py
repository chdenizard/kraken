"""LCD operations: upload images/GIFs, set brightness/orientation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from kraken.core.exceptions import ImageValidationError, LCDError

if TYPE_CHECKING:
    from kraken.core.device import KrakenDevice

SUPPORTED_STATIC_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
SUPPORTED_GIF_EXTENSIONS = {".gif"}
SUPPORTED_EXTENSIONS = SUPPORTED_STATIC_EXTENSIONS | SUPPORTED_GIF_EXTENSIONS

VALID_ORIENTATIONS = (0, 90, 180, 270)
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 100


def validate_image_file(image_path: str | Path) -> Path:
    """Validate that the image file exists and has a supported extension.

    Returns:
        Resolved Path to the image file.
    """
    path = Path(image_path).resolve()

    if not path.exists():
        raise ImageValidationError(f"File not found: {path}")

    if not path.is_file():
        raise ImageValidationError(f"Not a file: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported format '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    return path


def upload_static(device: KrakenDevice, image_path: str | Path) -> None:
    """Upload a static image to the Kraken LCD.

    The image is automatically resized and rotated by liquidctl.
    """
    path = validate_image_file(image_path)
    ext = path.suffix.lower()

    if ext in SUPPORTED_GIF_EXTENSIONS:
        raise ImageValidationError(
            f"Use upload_gif() for GIF files. Got: {path.name}"
        )

    try:
        device.set_screen("static", str(path))
    except Exception as e:
        raise LCDError(f"Failed to upload static image: {e}") from e


def upload_gif(device: KrakenDevice, gif_path: str | Path) -> None:
    """Play an animated GIF on the Kraken LCD (one full pass).

    Firmware 2.x ignores GIF animation, so we replay the GIF as a sequence
    of static frames. This call blocks for one full pass; for infinite or
    bounded playback use :func:`kraken.core.gif.play_animated_gif` directly.
    """
    from kraken.core import gif as gif_player

    path = validate_image_file(gif_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_GIF_EXTENSIONS:
        raise ImageValidationError(
            f"Expected a GIF file, got '{ext}': {path.name}"
        )

    try:
        gif_player.play_animated_gif(device, path, loops=1)
    except Exception as e:
        raise LCDError(f"Failed to play GIF: {e}") from e


def upload_image(device: KrakenDevice, image_path: str | Path) -> None:
    """Upload an image or GIF to the LCD, auto-detecting the type."""
    path = validate_image_file(image_path)
    ext = path.suffix.lower()

    if ext in SUPPORTED_GIF_EXTENSIONS:
        upload_gif(device, path)
    else:
        upload_static(device, path)


def set_liquid_mode(device: KrakenDevice) -> None:
    """Switch the LCD to the built-in liquid temperature display."""
    try:
        device.set_screen("liquid")
    except Exception as e:
        raise LCDError(f"Failed to set liquid mode: {e}") from e


def set_brightness(device: KrakenDevice, value: int) -> None:
    """Set LCD brightness (0-100)."""
    if not BRIGHTNESS_MIN <= value <= BRIGHTNESS_MAX:
        raise ValueError(f"Brightness must be {BRIGHTNESS_MIN}-{BRIGHTNESS_MAX}, got {value}")

    try:
        device.set_screen("brightness", value)
    except Exception as e:
        raise LCDError(f"Failed to set brightness: {e}") from e


def set_orientation(device: KrakenDevice, degrees: int) -> None:
    """Set LCD orientation (0, 90, 180, or 270 degrees)."""
    if degrees not in VALID_ORIENTATIONS:
        raise ValueError(f"Orientation must be one of {VALID_ORIENTATIONS}, got {degrees}")

    try:
        device.set_screen("orientation", degrees)
    except Exception as e:
        raise LCDError(f"Failed to set orientation: {e}") from e
