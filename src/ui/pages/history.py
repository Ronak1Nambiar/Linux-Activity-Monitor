"""Historical metrics page — time-series charts for CPU, Memory, Disk I/O, Network."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.metric_card import MetricCard
from src.ui.widgets.mini_chart import MiniChart
from src.utils.formatting import bytes_to_human, speed_to_human


class HistoryPage(QWidget):
    """Displays long-running time-series charts (up to 300 data points each)."""

    _HISTORY = 300

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("History")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        hint = QLabel(f"Displaying last {self._HISTORY} samples per metric")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        # CPU chart
        self._cpu_chart = self._make_chart_card(
            "CPU Usage (%)", "#4f8cff", max_value=100
        )
        layout.addWidget(self._cpu_chart["card"])

        # Memory chart
        self._mem_chart = self._make_chart_card(
            "Memory Usage (%)", "#a78bfa", max_value=100
        )
        layout.addWidget(self._mem_chart["card"])

        # GPU chart (hidden until GPU data arrives)
        self._gpu_card_widget = self._make_chart_card(
            "GPU Usage (%)", "#fb923c", max_value=100
        )
        self._gpu_card_widget["card"].setVisible(False)
        layout.addWidget(self._gpu_card_widget["card"])

        # Disk I/O
        disk_card = MetricCard("Disk I/O")
        disk_layout = QVBoxLayout()
        disk_layout.setContentsMargins(0, 0, 0, 0)
        disk_layout.setSpacing(6)
        read_label = QLabel("Read  0 B/s")
        read_label.setObjectName("CardSubValue")
        write_label = QLabel("Write  0 B/s")
        write_label.setObjectName("CardSubValue")
        rw_row = QHBoxLayout()
        rw_row.addWidget(read_label)
        rw_row.addStretch()
        rw_row.addWidget(write_label)
        read_chart = MiniChart(auto_scale=True, color="#4ade80", history_size=self._HISTORY)
        read_chart.setFixedHeight(70)
        write_chart = MiniChart(auto_scale=True, color="#f87171", history_size=self._HISTORY)
        write_chart.setFixedHeight(70)
        rw_lbl_row = QHBoxLayout()
        rl = QLabel("Read")
        rl.setObjectName("CardTitle")
        wl = QLabel("Write")
        wl.setObjectName("CardTitle")
        rw_lbl_row.addWidget(rl)
        rw_lbl_row.addStretch()
        rw_lbl_row.addWidget(wl)
        disk_card.add_layout(rw_row)
        disk_card.add_layout(rw_lbl_row)
        disk_card.add_widget(read_chart)
        disk_card.add_widget(write_chart)
        self._disk_read_label = read_label
        self._disk_write_label = write_label
        self._disk_read_chart = read_chart
        self._disk_write_chart = write_chart
        layout.addWidget(disk_card)

        # Network I/O
        net_card = MetricCard("Network I/O")
        up_label = QLabel("Upload  0 B/s")
        up_label.setObjectName("CardSubValue")
        down_label = QLabel("Download  0 B/s")
        down_label.setObjectName("CardSubValue")
        ud_row = QHBoxLayout()
        ud_row.addWidget(up_label)
        ud_row.addStretch()
        ud_row.addWidget(down_label)
        up_chart = MiniChart(auto_scale=True, color="#a78bfa", history_size=self._HISTORY)
        up_chart.setFixedHeight(70)
        down_chart = MiniChart(auto_scale=True, color="#38bdf8", history_size=self._HISTORY)
        down_chart.setFixedHeight(70)
        ud_lbl_row = QHBoxLayout()
        ul = QLabel("Upload")
        ul.setObjectName("CardTitle")
        dl = QLabel("Download")
        dl.setObjectName("CardTitle")
        ud_lbl_row.addWidget(ul)
        ud_lbl_row.addStretch()
        ud_lbl_row.addWidget(dl)
        net_card.add_layout(ud_row)
        net_card.add_layout(ud_lbl_row)
        net_card.add_widget(up_chart)
        net_card.add_widget(down_chart)
        self._net_up_label = up_label
        self._net_down_label = down_label
        self._net_up_chart = up_chart
        self._net_down_chart = down_chart
        layout.addWidget(net_card)

        layout.addStretch()

    def _make_chart_card(self, title: str, color: str, max_value: float = 100) -> dict:
        card = MetricCard(title)
        chart = MiniChart(max_value=max_value, color=color, history_size=self._HISTORY)
        chart.setFixedHeight(100)
        value_label = QLabel("0%")
        value_label.setObjectName("CardSubValue")
        card.add_widget(value_label)
        card.add_widget(chart)
        return {"card": card, "chart": chart, "label": value_label}

    # ------------------------------------------------------------------
    # Live update
    # ------------------------------------------------------------------

    def update_data(self, data: dict) -> None:
        cpu_pct = data.get("cpu", {}).get("percent", 0.0)
        self._cpu_chart["chart"].add_value(cpu_pct)
        self._cpu_chart["label"].setText(f"{cpu_pct:.1f}%")

        mem_pct = data.get("memory", {}).get("percent", 0.0)
        self._mem_chart["chart"].add_value(mem_pct)
        self._mem_chart["label"].setText(f"{mem_pct:.1f}%")

        # GPU (first GPU if present)
        gpus = data.get("gpu", [])
        if gpus:
            self._gpu_card_widget["card"].setVisible(True)
            gpu_load = gpus[0].get("load_pct", 0.0)
            self._gpu_card_widget["chart"].add_value(gpu_load)
            self._gpu_card_widget["label"].setText(f"{gpu_load:.1f}%")

        disk_io = data.get("disk", {}).get("io", {})
        r = disk_io.get("read_bytes_ps", 0.0)
        w = disk_io.get("write_bytes_ps", 0.0)
        self._disk_read_chart.add_value(r)
        self._disk_write_chart.add_value(w)
        self._disk_read_label.setText(f"Read  {speed_to_human(r)}")
        self._disk_write_label.setText(f"Write  {speed_to_human(w)}")

        interfaces = data.get("network", {}).get("interfaces", [])
        total_up = sum(i.get("bytes_sent_ps", 0.0) for i in interfaces)
        total_down = sum(i.get("bytes_recv_ps", 0.0) for i in interfaces)
        self._net_up_chart.add_value(total_up)
        self._net_down_chart.add_value(total_down)
        self._net_up_label.setText(f"Upload  {speed_to_human(total_up)}")
        self._net_down_label.setText(f"Download  {speed_to_human(total_down)}")
