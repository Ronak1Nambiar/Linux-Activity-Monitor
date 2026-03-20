"""Rounded metric card widget used throughout the dashboard."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


class MetricCard(QFrame):
    """A styled card that displays a title, primary value, and optional sub-widget.

    Usage::

        card = MetricCard("CPU")
        card.set_value("42%")
        layout.addWidget(card)
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(16, 14, 16, 14)
        self._outer.setSpacing(6)

        # Title
        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("CardTitle")

        # Primary value
        self.value_label = QLabel("—")
        self.value_label.setObjectName("CardValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Sub-value (secondary info, smaller text)
        self.sub_label = QLabel("")
        self.sub_label.setObjectName("CardSubValue")
        self.sub_label.setVisible(False)

        self._outer.addWidget(self.title_label)
        self._outer.addWidget(self.value_label)
        self._outer.addWidget(self.sub_label)

        # Content area — subclasses / callers add extra widgets here
        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 4, 0, 0)
        self._content.setSpacing(4)
        self._outer.addLayout(self._content)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, text: str) -> None:
        self.value_label.setText(text)

    def set_sub_value(self, text: str) -> None:
        self.sub_label.setText(text)
        self.sub_label.setVisible(bool(text))

    def set_description(self, text: str) -> None:
        """Set a small description shown below the sub-value label."""
        if not hasattr(self, "_desc_label"):
            from PySide6.QtWidgets import QLabel
            self._desc_label = QLabel("")
            self._desc_label.setObjectName("CardSubValue")
            self._outer.addWidget(self._desc_label)
        self._desc_label.setText(text)
        self._desc_label.setVisible(bool(text))

    def add_widget(self, widget: QWidget) -> None:
        """Append a widget to the card's content area."""
        self._content.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._content.addLayout(layout)
