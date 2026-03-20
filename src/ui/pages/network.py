"""Network activity page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.mini_chart import MiniChart
from src.ui.widgets.section_header import SectionHeader
from src.utils.formatting import bytes_to_human, speed_to_human


class _InterfaceCard(QFrame):
    """Card for one network interface."""

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        title = QLabel(name)
        title.setObjectName("CardValue")

        self._up_label = QLabel("↑  0 B/s")
        self._up_label.setObjectName("CardSubValue")
        self._down_label = QLabel("↓  0 B/s")
        self._down_label.setObjectName("CardSubValue")

        self._total_label = QLabel("Total: sent 0 B / recv 0 B")
        self._total_label.setObjectName("HintLabel")

        self._packets_label = QLabel("Packets: — sent / — recv")
        self._packets_label.setObjectName("HintLabel")

        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)

        up_box = QVBoxLayout()
        ul = QLabel("UPLOAD")
        ul.setObjectName("CardTitle")
        self._up_chart = MiniChart(auto_scale=True, color="#a78bfa")
        self._up_chart.setFixedHeight(60)
        up_box.addWidget(ul)
        up_box.addWidget(self._up_chart)

        down_box = QVBoxLayout()
        dl = QLabel("DOWNLOAD")
        dl.setObjectName("CardTitle")
        self._down_chart = MiniChart(auto_scale=True, color="#38bdf8")
        self._down_chart.setFixedHeight(60)
        down_box.addWidget(dl)
        down_box.addWidget(self._down_chart)

        charts_layout.addLayout(up_box)
        charts_layout.addLayout(down_box)

        layout.addWidget(title)
        layout.addWidget(self._up_label)
        layout.addWidget(self._down_label)
        layout.addLayout(charts_layout)
        layout.addWidget(self._total_label)
        layout.addWidget(self._packets_label)

    def update_data(self, info: dict) -> None:
        up = info.get("bytes_sent_ps", 0.0)
        down = info.get("bytes_recv_ps", 0.0)
        self._up_label.setText(f"↑  {speed_to_human(up)}")
        self._down_label.setText(f"↓  {speed_to_human(down)}")
        self._up_chart.add_value(up)
        self._down_chart.add_value(down)
        sent = info.get("total_sent", 0)
        recv = info.get("total_recv", 0)
        self._total_label.setText(
            f"Session total  ↑ {bytes_to_human(sent)}  ↓ {bytes_to_human(recv)}"
        )
        pkts_sent = info.get("packets_sent", 0)
        pkts_recv = info.get("packets_recv", 0)
        self._packets_label.setText(f"Packets  ↑ {pkts_sent:,}  ↓ {pkts_recv:,}")


class NetworkPage(QWidget):
    """Per-interface network activity overview."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._interface_cards: dict[str, _InterfaceCard] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Network")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        layout.addWidget(SectionHeader("Interfaces"))
        self._ifaces_layout = QVBoxLayout()
        self._ifaces_layout.setSpacing(12)
        layout.addLayout(self._ifaces_layout)

        self._no_iface_label = QLabel("No active interfaces detected.")
        self._no_iface_label.setObjectName("CardSubValue")
        self._no_iface_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._no_iface_label)
        self._no_iface_label.setVisible(True)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Live update
    # ------------------------------------------------------------------

    def update_data(self, data: dict) -> None:
        interfaces = data.get("network", {}).get("interfaces", [])

        current_names = {i["name"] for i in interfaces}
        existing_names = set(self._interface_cards.keys())

        # Remove cards for gone interfaces
        for name in existing_names - current_names:
            card = self._interface_cards.pop(name)
            self._ifaces_layout.removeWidget(card)
            card.deleteLater()

        # Add cards for new interfaces
        for iface in interfaces:
            name = iface["name"]
            if name not in self._interface_cards:
                card = _InterfaceCard(name)
                self._interface_cards[name] = card
                self._ifaces_layout.addWidget(card)

        # Update all cards
        for iface in interfaces:
            name = iface["name"]
            if name in self._interface_cards:
                self._interface_cards[name].update_data(iface)

        self._no_iface_label.setVisible(len(interfaces) == 0)
