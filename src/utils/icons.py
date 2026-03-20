"""Provides sidebar and UI icon text using Unicode symbols.

No external image files are required – icons are rendered as Unicode text
inside QLabel or QPushButton widgets styled with a monospace/icon font.
"""

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
