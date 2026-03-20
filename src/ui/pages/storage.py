"""Storage / disk page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.mini_chart import MiniChart
from src.ui.widgets.section_header import SectionHeader
from src.utils.formatting import bytes_to_human, color_for_percent, speed_to_human


class _PartitionCard(QFrame):
    """Card showing usage for one mounted partition."""

    def __init__(self, info: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Mountpoint / device
        title = QLabel(info["mountpoint"])
        title.setObjectName("CardValue")
        device = QLabel(f"{info['device']}  ·  {info['fstype']}")
        device.setObjectName("CardTitle")

        # Usage bar
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)

        pct = info.get("percent", 0.0)
        bar.setValue(int(pct))
        bar.setStyleSheet(
            f"QProgressBar::chunk {{ background: {color_for_percent(pct)}; border-radius: 4px; }}"
        )

        # Size labels
        used = info.get("used", 0)
        total = info.get("total", 0)
        free = info.get("free", 0)
        size_row = QHBoxLayout()
        used_label = QLabel(f"Used: {bytes_to_human(used)}")
        used_label.setObjectName("CardSubValue")
        free_label = QLabel(f"Free: {bytes_to_human(free)}")
        free_label.setObjectName("CardSubValue")
        total_label = QLabel(f"Total: {bytes_to_human(total)}")
        total_label.setObjectName("CardSubValue")
        size_row.addWidget(used_label)
        size_row.addStretch()
        size_row.addWidget(free_label)
        size_row.addStretch()
        size_row.addWidget(total_label)

        pct_label = QLabel(f"{pct:.1f}% used")
        pct_label.setObjectName("CardSubValue")

        layout.addWidget(title)
        layout.addWidget(device)
        layout.addWidget(bar)
        layout.addWidget(pct_label)
        layout.addLayout(size_row)


class StoragePage(QWidget):
    """Partition overview + I/O activity section."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._built_partitions: list[str] = []
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

        title = QLabel("Storage")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Partitions section
        layout.addWidget(SectionHeader("Mounted Partitions"))
        self._partitions_layout = QVBoxLayout()
        self._partitions_layout.setSpacing(12)
        layout.addLayout(self._partitions_layout)

        # Disk I/O section
        layout.addWidget(SectionHeader("Disk I/O Activity"))
        io_card = QFrame()
        io_card.setObjectName("MetricCard")
        io_layout = QVBoxLayout(io_card)
        io_layout.setContentsMargins(16, 14, 16, 14)
        io_layout.setSpacing(8)

        self._io_label = QLabel("Read: 0 B/s  |  Write: 0 B/s")
        self._io_label.setObjectName("CardValue")
        io_layout.addWidget(self._io_label)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(16)

        read_box = QVBoxLayout()
        read_title = QLabel("READ")
        read_title.setObjectName("CardTitle")
        self._read_chart = MiniChart(auto_scale=True, color="#4ade80")
        self._read_chart.setFixedHeight(80)
        read_box.addWidget(read_title)
        read_box.addWidget(self._read_chart)

        write_box = QVBoxLayout()
        write_title = QLabel("WRITE")
        write_title.setObjectName("CardTitle")
        self._write_chart = MiniChart(auto_scale=True, color="#f87171")
        self._write_chart.setFixedHeight(80)
        write_box.addWidget(write_title)
        write_box.addWidget(self._write_chart)

        chart_row.addLayout(read_box)
        chart_row.addLayout(write_box)
        io_layout.addLayout(chart_row)
        layout.addWidget(io_card)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Live update
    # ------------------------------------------------------------------

    def update_data(self, data: dict) -> None:
        disk = data.get("disk", {})
        partitions = disk.get("partitions", [])
        io = disk.get("io", {})

        # Rebuild partition cards only when the set of mountpoints changes
        mountpoints = [p["mountpoint"] for p in partitions]
        if mountpoints != self._built_partitions:
            self._built_partitions = mountpoints
            # Clear
            while self._partitions_layout.count():
                item = self._partitions_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            for p in partitions:
                self._partitions_layout.addWidget(_PartitionCard(p))

        r = io.get("read_bytes_ps", 0.0)
        w = io.get("write_bytes_ps", 0.0)
        self._io_label.setText(f"Read: {speed_to_human(r)}  |  Write: {speed_to_human(w)}")
        self._read_chart.add_value(r)
        self._write_chart.add_value(w)
