"""Carousel playlist management."""

from __future__ import annotations

from pathlib import Path

from kraken.core.exceptions import CarouselError, ImageValidationError
from kraken.core.lcd import validate_image_file
from kraken.core.models import SPECIAL_MEDIA_TYPES, CarouselItem


class Playlist:
    """Manages an ordered list of carousel items."""

    def __init__(self, items: list[CarouselItem] | None = None) -> None:
        self._items: list[CarouselItem] = list(items) if items else []

    @property
    def items(self) -> list[CarouselItem]:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return len(self._items) > 0

    def add(
        self,
        path: str | Path,
        display_seconds: float = 10.0,
        position: int | None = None,
    ) -> CarouselItem:
        """Add an image/GIF to the playlist.

        Args:
            path: Path to the image file.
            display_seconds: How long to display this item.
            position: Insert at this position (default: append to end).

        Returns:
            The created CarouselItem.
        """
        resolved = validate_image_file(path)
        item = CarouselItem(path=str(resolved), display_seconds=display_seconds)

        if position is not None:
            if position < 0 or position > len(self._items):
                raise CarouselError(
                    f"Position {position} out of range (0-{len(self._items)})"
                )
            self._items.insert(position, item)
        else:
            self._items.append(item)

        return item

    def add_special(
        self,
        media_type: str,
        display_seconds: float = 10.0,
        position: int | None = None,
    ) -> CarouselItem:
        """Add a special item (sysinfo or liquid) to the playlist."""
        if media_type not in SPECIAL_MEDIA_TYPES:
            raise CarouselError(
                f"Not a special media type: {media_type}. Use add() for images."
            )
        item = CarouselItem(path="", display_seconds=display_seconds, media_type=media_type)

        if position is not None:
            if position < 0 or position > len(self._items):
                raise CarouselError(
                    f"Position {position} out of range (0-{len(self._items)})"
                )
            self._items.insert(position, item)
        else:
            self._items.append(item)

        return item

    def remove(self, index: int) -> CarouselItem:
        """Remove an item by index.

        Returns:
            The removed CarouselItem.
        """
        if not 0 <= index < len(self._items):
            raise CarouselError(f"Index {index} out of range (0-{len(self._items) - 1})")
        return self._items.pop(index)

    def move(self, from_index: int, to_index: int) -> None:
        """Move an item from one position to another."""
        if not 0 <= from_index < len(self._items):
            raise CarouselError(f"from_index {from_index} out of range")
        if not 0 <= to_index < len(self._items):
            raise CarouselError(f"to_index {to_index} out of range")
        item = self._items.pop(from_index)
        self._items.insert(to_index, item)

    def clear(self) -> None:
        """Remove all items."""
        self._items.clear()

    def validate_paths(self) -> list[str]:
        """Check that all item paths still exist.

        Returns:
            List of error messages for invalid items.
        """
        errors = []
        for i, item in enumerate(self._items):
            if item.is_special:
                continue
            try:
                validate_image_file(item.path)
            except ImageValidationError as e:
                errors.append(f"Item {i} ({item.path}): {e}")
        return errors

    def get(self, index: int) -> CarouselItem:
        """Get item by index."""
        if not 0 <= index < len(self._items):
            raise CarouselError(f"Index {index} out of range")
        return self._items[index]
