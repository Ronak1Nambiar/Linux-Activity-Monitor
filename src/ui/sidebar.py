"""Left-hand navigation sidebar."""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QLabel,
)

_NAV_ITEMS = [
    ("dashboard",  "Dashboard"),
    ("processes",  "Processes"),
    ("storage",    "Storage"),
    ("network",    "Network"),
    ("history",    "History"),
    ("hardware",   "Hardware"),
    ("alerts",     "Alerts"),
    ("docker",     "Docker"),
]

_NAV_ICONS = {
    "dashboard":  "⬛",
    "processes":  "☰ ",
    "storage":    "💾",
    "network":    "🌐",
    "history":    "📈",
    "hardware":   "🖥 ",
    "alerts":     "🔔",
    "docker":     "🐳",
}


class Sidebar(QWidget):
    """Emits ``page_changed(key)`` when the user clicks a nav item."""

    page_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(190)
        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(4)

        # App name header
        app_label = QLabel("Linux Monitor")
        app_label.setObjectName("SidebarAppName")
        app_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(app_label)

        layout.addSpacing(20)

        for key, label in _NAV_ITEMS:
            icon = _NAV_ICONS.get(key, "•")
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(40)
            btn.clicked.connect(lambda checked, k=key: self.page_changed.emit(k))
            self._group.addButton(btn)
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Settings button at bottom
        settings_btn = QPushButton("  ⚙    Settings")
        settings_btn.setObjectName("SidebarButton")
        settings_btn.setFixedHeight(40)
        settings_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        settings_btn.clicked.connect(lambda: self.page_changed.emit("settings"))
        self._buttons["settings"] = settings_btn
        layout.addWidget(settings_btn)

    def set_active(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn and btn.isCheckable():
            btn.setChecked(True)

    def select_default(self) -> None:
        self.set_active("dashboard")
        self.page_changed.emit("dashboard")
