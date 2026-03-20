"""Docker containers page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.utils.formatting import bytes_to_human


_HEADERS = ["Name", "CPU %", "Mem Used", "Mem %", "Net RX", "Net TX", "PIDs"]


class DockerPage(QWidget):
    """Displays running Docker container resource usage."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Docker Containers")
        title.setObjectName("PageTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        self._count_label = QLabel("Checking…")
        self._count_label.setObjectName("CardSubValue")
        header_row.addWidget(self._count_label)
        layout.addLayout(header_row)

        self._status_label = QLabel("")
        self._status_label.setObjectName("HintLabel")
        layout.addWidget(self._status_label)

        self._model = QStandardItemModel(0, len(_HEADERS))
        self._model.setHorizontalHeaderLabels(_HEADERS)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(True)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(1, 80)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 100)
        self._table.setColumnWidth(5, 100)
        self._table.setColumnWidth(6, 60)

        layout.addWidget(self._table)

    def update_containers(self, containers: list[dict]) -> None:
        if not containers and self._model.rowCount() == 0:
            # Docker may not be available
            self._count_label.setText("No containers")
            self._status_label.setText("Docker is not running or no containers are active.")
            self._model.setRowCount(0)
            return

        self._status_label.setText("")
        self._count_label.setText(
            f"{len(containers)} container{'s' if len(containers) != 1 else ''}"
        )
        self._model.setRowCount(0)

        for c in containers:
            cpu_pct = c.get("cpu_pct", 0.0)
            mem_pct = c.get("mem_pct", 0.0)

            name_item = QStandardItem(c.get("name", ""))
            name_item.setEditable(False)

            cpu_item = QStandardItem(f"{cpu_pct:.1f}%")
            cpu_item.setEditable(False)
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if cpu_pct >= 80:
                cpu_item.setForeground(QColor("#f87171"))
            elif cpu_pct >= 40:
                cpu_item.setForeground(QColor("#fbbf24"))

            mem_used_item = QStandardItem(bytes_to_human(c.get("mem_used", 0)))
            mem_used_item.setEditable(False)
            mem_used_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            mem_pct_item = QStandardItem(f"{mem_pct:.1f}%")
            mem_pct_item.setEditable(False)
            mem_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            net_rx_item = QStandardItem(bytes_to_human(c.get("net_rx", 0)))
            net_rx_item.setEditable(False)
            net_rx_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            net_tx_item = QStandardItem(bytes_to_human(c.get("net_tx", 0)))
            net_tx_item.setEditable(False)
            net_tx_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            pids_item = QStandardItem(str(c.get("pids", "0")))
            pids_item.setEditable(False)
            pids_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self._model.appendRow([
                name_item, cpu_item, mem_used_item, mem_pct_item,
                net_rx_item, net_tx_item, pids_item,
            ])
