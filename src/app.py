"""QApplication factory and stylesheet loader."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.config import AppConfig

_STYLES_DIR = Path(__file__).parent.parent / "assets" / "styles"


def load_stylesheet(theme: str) -> str:
    """Load a QSS stylesheet by theme name ('dark' or 'light')."""
    path = _STYLES_DIR / f"{theme}.qss"
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def create_app(config: AppConfig) -> QApplication:
    """Create and configure the QApplication singleton."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("Linux Activity Monitor")
    app.setApplicationDisplayName("Linux Activity Monitor")
    app.setOrganizationName("linux-monitor")
    app.setApplicationVersion("1.0.0")

    # Set a clean base font
    font = QFont("Inter, Segoe UI, Helvetica Neue, Arial", 10)
    app.setFont(font)

    # Apply stylesheet
    stylesheet = load_stylesheet(config.theme)
    app.setStyleSheet(stylesheet)

    return app
