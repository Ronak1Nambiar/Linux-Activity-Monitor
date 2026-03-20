"""Process viewer page."""

from __future__ import annotations

import os
import signal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
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

        self._kill_btn = QPushButton("Kill Process")
        self._kill_btn.setObjectName("ActionButton")
        self._kill_btn.setEnabled(False)
        self._kill_btn.clicked.connect(self._on_kill)
        header_row.addWidget(self._kill_btn)

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
        self._table.selection_changed.connect(self._kill_btn.setEnabled)
        layout.addWidget(self._table)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_filter_changed(self, text: str) -> None:
        self._table.set_filter(text)

    def _on_kill(self) -> None:
        pid = self._table.get_selected_pid()
        if pid is None:
            return

        reply = QMessageBox.question(
            self,
            "Kill Process",
            f"Are you sure you want to kill process {pid}?\n\nThis will send SIGTERM.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                QMessageBox.warning(
                    self,
                    "Process Not Found",
                    f"Process {pid} no longer exists.",
                )
            except PermissionError:
                QMessageBox.critical(
                    self,
                    "Permission Denied",
                    f"Insufficient privileges to kill process {pid}.",
                )

    def update_processes(self, processes: list[dict]) -> None:
        self._table.update_processes(processes)
        self._count_label.setText(f"{len(processes)} processes")
