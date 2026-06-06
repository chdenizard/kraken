"""Kraken GUI application entry point."""

from __future__ import annotations

import sys


def main() -> None:
    """Launch the Kraken GUI application."""
    from PySide6.QtWidgets import QApplication

    from kraken.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Kraken")
    app.setApplicationDisplayName("Kraken - NZXT LCD Manager")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
