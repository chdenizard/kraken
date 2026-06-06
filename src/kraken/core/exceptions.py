"""Custom exceptions for the Kraken project."""


class KrakenError(Exception):
    """Base exception for all Kraken errors."""


class DeviceNotFoundError(KrakenError):
    """No supported Kraken device was found."""


class DeviceConnectionError(KrakenError):
    """Failed to connect or communicate with the Kraken device."""


class DeviceNotInitializedError(KrakenError):
    """Device has not been initialized yet."""


class LCDError(KrakenError):
    """Error during LCD operations."""


class ImageValidationError(LCDError):
    """Image file is invalid or unsupported."""


class CarouselError(KrakenError):
    """Error in carousel operations."""


class ConfigError(KrakenError):
    """Error loading or saving configuration."""


class HwmonNotFoundError(KrakenError):
    """Kraken hwmon device not found in sysfs."""
