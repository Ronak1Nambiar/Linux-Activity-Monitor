"""Process viewer page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.process_table import ProcessTable


class ProcessesPage(QWidget):
    """Shows a sortable, searchable process list."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header row
        header_row = QHBoxLayout()
        title = QLabel("Processes")
        title.setObjectName("PageTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        # Process count label
        self._count_label = QLabel("")
        self._count_label.setObjectName("CardSubValue")
        header_row.addWidget(self._count_label)

        layout.addLayout(header_row)

        # Search bar
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, user or PID…")
        self._search.setObjectName("SearchBar")
        self._search.textChanged.connect(self._on_filter_changed)
        search_row.addWidget(self._search)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("ActionButton")
        clear_btn.clicked.connect(self._search.clear)
        search_row.addWidget(clear_btn)

        layout.addLayout(search_row)

        # Sort hint
        hint = QLabel("Click a column header to sort  ·  sorted by CPU by default")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        # Table
        self._table = ProcessTable()
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_filter_changed(self, text: str) -> None:
        self._table.set_filter(text)

    def update_processes(self, processes: list[dict]) -> None:
        self._table.update_processes(processes)
        self._count_label.setText(f"{len(processes)} processes")
