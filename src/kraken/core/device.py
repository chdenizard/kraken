"""KrakenDevice: thread-safe wrapper around liquidctl for NZXT Kraken."""

from __future__ import annotations

import threading
from typing import Any

from kraken.core.exceptions import (
    DeviceConnectionError,
    DeviceNotFoundError,
    DeviceNotInitializedError,
)
from kraken.core.models import DeviceInfo

# Kraken 2023 Standard PID
KRAKEN_2023_STANDARD_PID = 0x300E

# Known Kraken PIDs with LCD
KRAKEN_LCD_PIDS = {
    0x300C,  # Kraken 2023 Elite
    0x300E,  # Kraken 2023 Standard
    0x3012,  # Kraken 2024 Elite RGB
    0x3014,  # Kraken 2024 Plus
}

LCD_RESOLUTIONS: dict[int, tuple[int, int]] = {
    0x300C: (640, 640),
    0x300E: (240, 240),
    0x3012: (640, 640),
    0x3014: (240, 240),
}


class KrakenDevice:
    """Thread-safe wrapper around a liquidctl Kraken device.

    All USB operations are serialized through an internal lock to prevent
    contention between sensor reads and LCD uploads.
    """

    def __init__(self, lc_device: Any) -> None:
        self._dev = lc_device
        self._lock = threading.Lock()
        self._connected = False
        self._initialized = False
        self.info: DeviceInfo | None = None

    @classmethod
    def find(cls) -> KrakenDevice:
        """Find the first supported Kraken device.

        Raises:
            DeviceNotFoundError: If no supported device is found.
        """
        try:
            from liquidctl import find_liquidctl_devices
        except ImportError as e:
            raise DeviceNotFoundError(
                "liquidctl is not installed. Install with: pip install liquidctl>=1.14.0"
            ) from e

        devices = find_liquidctl_devices()
        for dev in devices:
            product_id = getattr(dev, "product_id", None) or getattr(
                dev.device, "product_id", None
            )
            if product_id in KRAKEN_LCD_PIDS:
                return cls(dev)

        raise DeviceNotFoundError(
            "No supported NZXT Kraken device found. "
            "Check USB connection and udev rules."
        )

    def connect(self) -> None:
        """Open connection to the device."""
        with self._lock:
            if self._connected:
                return
            try:
                self._dev.connect()
                self._connected = True
            except Exception as e:
                raise DeviceConnectionError(f"Failed to connect: {e}") from e

    def initialize(self) -> DeviceInfo:
        """Initialize the device (required after boot).

        Returns:
            DeviceInfo with device metadata.
        """
        with self._lock:
            if not self._connected:
                raise DeviceConnectionError("Device is not connected. Call connect() first.")
            try:
                init_data = self._dev.initialize()
                product_id = getattr(self._dev, "product_id", None) or getattr(
                    self._dev.device, "product_id", 0
                )
                firmware = ""
                serial = ""
                for key, value, *_ in (init_data or []):
                    key_lower = key.lower()
                    if "firmware" in key_lower:
                        firmware = str(value)
                    elif "serial" in key_lower:
                        serial = str(value)

                self.info = DeviceInfo(
                    description=str(self._dev.description),
                    firmware_version=firmware,
                    lcd_resolution=LCD_RESOLUTIONS.get(product_id, (240, 240)),
                    serial_number=serial,
                    product_id=product_id,
                )
                self._initialized = True
                return self.info
            except Exception as e:
                raise DeviceConnectionError(f"Failed to initialize: {e}") from e

    def disconnect(self) -> None:
        """Close the device connection."""
        with self._lock:
            if not self._connected:
                return
            try:
                self._dev.disconnect()
            except Exception:
                pass
            finally:
                self._connected = False
                self._initialized = False

    def get_status(self) -> list[tuple[str, Any, str]]:
        """Read device status (sensors) via liquidctl.

        Returns:
            List of (key, value, unit) tuples.
        """
        self._ensure_initialized()
        with self._lock:
            try:
                return self._dev.get_status() or []
            except Exception as e:
                raise DeviceConnectionError(f"Failed to read status: {e}") from e

    def set_screen(self, mode: str, value: Any = None) -> None:
        """Set the LCD screen mode.

        Args:
            mode: One of "static", "gif", "liquid", "brightness", "orientation".
            value: The value for the mode (file path, int, etc.).
        """
        self._ensure_initialized()
        with self._lock:
            # Drain unsolicited HID broadcasts that the Kraken emits
            # periodically. Without this, set_screen's internal _read_until
            # consumes those broadcasts and fails with "missing messages".
            try:
                self._dev.device.clear_enqueued_reports()
            except Exception:
                pass
            try:
                if mode == "brightness":
                    self._dev.set_screen("lcd", "brightness", value)
                elif mode == "orientation":
                    self._dev.set_screen("lcd", "orientation", value)
                elif mode == "liquid":
                    self._dev.set_screen("lcd", "liquid", value=None)
                elif mode in ("static", "gif"):
                    self._dev.set_screen("lcd", mode, value)
                else:
                    raise ValueError(f"Unknown LCD mode: {mode}")
            except ValueError:
                raise
            except Exception as e:
                raise DeviceConnectionError(f"Failed to set screen ({mode}): {e}") from e

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise DeviceNotInitializedError(
                "Device has not been initialized. Call initialize() first."
            )

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def initialized(self) -> bool:
        return self._initialized

    def __enter__(self) -> KrakenDevice:
        self.connect()
        self.initialize()
        return self

    def __exit__(self, *args: Any) -> None:
        self.disconnect()
