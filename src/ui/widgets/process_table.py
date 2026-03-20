"""Sortable, filterable process table widget."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableView,
    QWidget,
)

from src.utils.formatting import bytes_to_human

_HEADERS = ["PID", "Name", "User", "CPU %", "RAM %", "RAM", "Status", "Threads"]
_COL_PID = 0
_COL_NAME = 1
_COL_USER = 2
_COL_CPU = 3
_COL_RAM_PCT = 4
_COL_RAM = 5
_COL_STATUS = 6
_COL_THREADS = 7


class _NumericItem(QStandardItem):
    """QStandardItem that sorts numerically."""

    def __init__(self, display: str, sort_key: float) -> None:
        super().__init__(display)
        self._sort_key = sort_key
        self.setEditable(False)

    def __lt__(self, other: "_NumericItem") -> bool:  # type: ignore[override]
        if isinstance(other, _NumericItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


class _MultiColumnFilterProxy(QSortFilterProxyModel):
    """Proxy model that searches across Name, User, and PID columns."""

    def filterAcceptsRow(self, source_row, source_parent):
        pattern = self.filterRegularExpression().pattern()
        if not pattern:
            return True
        model = self.sourceModel()
        # search across: Name(1), User(2), PID(0)
        for col in (_COL_NAME, _COL_USER, _COL_PID):
            idx = model.index(source_row, col, source_parent)
            if pattern.lower() in (model.data(idx) or "").lower():
                return True
        return False


class ProcessTable(QTableView):
    """A read-only QTableView showing system processes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._model = QStandardItemModel(0, len(_HEADERS))
        self._model.setHorizontalHeaderLabels(_HEADERS)

        self._proxy = _MultiColumnFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(_COL_NAME)

        self.setModel(self._proxy)
        self.setSortingEnabled(True)
        self.sortByColumn(_COL_CPU, Qt.SortOrder.DescendingOrder)

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(_COL_NAME, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionsMovable(False)

        # Column widths
        self.setColumnWidth(_COL_PID, 65)
        self.setColumnWidth(_COL_NAME, 180)
        self.setColumnWidth(_COL_USER, 110)
        self.setColumnWidth(_COL_CPU, 70)
        self.setColumnWidth(_COL_RAM_PCT, 70)
        self.setColumnWidth(_COL_RAM, 90)
        self.setColumnWidth(_COL_THREADS, 75)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_filter(self, text: str) -> None:
        self._proxy.setFilterRegularExpression(text)

    def update_processes(self, processes: list[dict]) -> None:
        self._model.setRowCount(0)
        for proc in processes:
            cpu = proc.get("cpu_percent", 0.0)
            ram_pct = proc.get("memory_percent", 0.0)
            ram_bytes = proc.get("memory_rss", 0)

            pid_item = _NumericItem(str(proc.get("pid", "")), float(proc.get("pid", 0)))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            name_item = QStandardItem(proc.get("name", ""))
            name_item.setEditable(False)

            user_item = QStandardItem(proc.get("username", ""))
            user_item.setEditable(False)

            cpu_item = _NumericItem(f"{cpu:.1f}", cpu)
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if cpu >= 20:
                cpu_item.setForeground(QColor("#f87171"))
            elif cpu >= 5:
                cpu_item.setForeground(QColor("#fbbf24"))

            ram_pct_item = _NumericItem(f"{ram_pct:.1f}", ram_pct)
            ram_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            ram_item = _NumericItem(bytes_to_human(ram_bytes), float(ram_bytes))
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            status_item = QStandardItem(proc.get("status", ""))
            status_item.setEditable(False)

            threads_item = _NumericItem(str(proc.get("threads", 0)), float(proc.get("threads", 0)))
            threads_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self._model.appendRow(
                [pid_item, name_item, user_item, cpu_item, ram_pct_item, ram_item, status_item, threads_item]
            )
