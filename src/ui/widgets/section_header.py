"""Simple section header label."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget


class SectionHeader(QLabel):
    """A styled section heading used to separate groups of content."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("SectionHeader")
