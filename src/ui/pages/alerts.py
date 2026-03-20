"""Alert history page — shows a log of past threshold alerts."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AlertsPage(QWidget):
    """Displays a scrollable list of past alerts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Alert History")
        title.setObjectName("PageTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._count_label = QLabel("0 alerts")
        self._count_label.setObjectName("CardSubValue")
        header_row.addWidget(self._count_label)

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("ActionButton")
        clear_btn.clicked.connect(self.clear_alerts)
        header_row.addWidget(clear_btn)

        layout.addLayout(header_row)

        hint = QLabel("Alerts are triggered when CPU or Memory usage exceeds configured thresholds.")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        # Scrollable list of alerts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

        self._alert_count = 0

    def add_alert(self, title: str, message: str) -> None:
        """Add a new alert entry to the top of the list."""
        ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        row = _AlertRow(title, message, ts)
        # Insert before the stretch item
        self._list_layout.insertWidget(0, row)
        self._alert_count += 1
        self._count_label.setText(f"{self._alert_count} alert{'s' if self._alert_count != 1 else ''}")

    def clear_alerts(self) -> None:
        """Remove all alert entries."""
        while self._list_layout.count() > 1:  # keep the stretch
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._alert_count = 0
        self._count_label.setText("0 alerts")


class _AlertRow(QFrame):
    """A single alert entry with timestamp, title, and message."""

    _COLORS = {
        "High CPU Usage": "#f87171",
        "High Memory Usage": "#fbbf24",
    }

    def __init__(self, title: str, message: str, timestamp: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(16)

        color = self._COLORS.get(title, "#8b8fa8")

        indicator = QLabel("●")
        indicator.setStyleSheet(f"color: {color}; font-size: 14px;")
        indicator.setFixedWidth(20)
        layout.addWidget(indicator)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("CardSubValue")
        msg_lbl.setWordWrap(True)
        text_col.addWidget(title_lbl)
        text_col.addWidget(msg_lbl)
        layout.addLayout(text_col, 1)

        ts_lbl = QLabel(timestamp)
        ts_lbl.setObjectName("HintLabel")
        ts_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(ts_lbl)
