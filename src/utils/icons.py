"""Provides sidebar and UI icon text using Unicode symbols.

No external image files are required – icons are rendered as Unicode text
inside QLabel or QPushButton widgets styled with a monospace/icon font.
"""

from pathlib import Path

_ICONS_DIR = Path(__file__).parent.parent.parent / "assets" / "icons"

ICONS = {
    "dashboard": "⬛",
    "processes": "☰",
    "storage": "💾",
    "network": "🌐",
    "hardware": "🖥",
    "settings": "⚙",
    "cpu": "⚡",
    "memory": "🧠",
    "disk": "💿",
    "thermometer": "🌡",
    "battery": "🔋",
    "upload": "↑",
    "download": "↓",
    "refresh": "↺",
}


def icon(name: str, fallback: str = "•") -> str:
    return ICONS.get(name, fallback)


def icon_path(name: str) -> str:
    """Return absolute path to a named icon file, or empty string if not found."""
    for ext in ("svg", "png", "ico"):
        p = _ICONS_DIR / f"{name}.{ext}"
        if p.exists():
            return str(p)
    return ""
