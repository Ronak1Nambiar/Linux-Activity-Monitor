#!/usr/bin/env python3
"""Linux Activity Monitor — entry point."""

import sys

# Ensure the project root is on the import path when run directly
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication

from src.app import create_app
from src.config import AppConfig
from src.ui.main_window import MainWindow


def main() -> int:
    config = AppConfig.load()
    app = create_app(config)

    window = MainWindow(config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
