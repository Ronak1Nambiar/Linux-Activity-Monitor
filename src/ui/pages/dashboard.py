"""Dashboard overview page — the first thing users see."""

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

from src.ui.widgets.circular_gauge import CircularGauge
from src.ui.widgets.metric_card import MetricCard
from src.ui.widgets.mini_chart import MiniChart
from src.utils.formatting import (
    bytes_to_human,
    color_for_percent,
    color_for_temp,
    format_uptime,
    speed_to_human,
)


class DashboardPage(QWidget):
    """Displays live summary cards for all major metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

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

        # Page title
        title = QLabel("System Overview")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # --- Top row: CPU / RAM / Disk / Network ---
        top_grid = QGridLayout()
        top_grid.setSpacing(16)

        self._cpu_card = self._make_gauge_card("CPU")
        self._ram_card = self._make_gauge_card("Memory")
        self._disk_card = self._make_disk_card()
        self._net_card = self._make_net_card()

        top_grid.addWidget(self._cpu_card, 0, 0)
        top_grid.addWidget(self._ram_card, 0, 1)
        top_grid.addWidget(self._disk_card, 0, 2)
        top_grid.addWidget(self._net_card, 0, 3)
        layout.addLayout(top_grid)

        # --- Bottom row: Temperatures / Battery / Uptime ---
        bot_grid = QGridLayout()
        bot_grid.setSpacing(16)

        self._temp_card = self._make_temp_card()
        self._battery_card = self._make_battery_card()
        self._uptime_card = self._make_uptime_card()

        bot_grid.addWidget(self._temp_card, 0, 0)
        bot_grid.addWidget(self._battery_card, 0, 1)
        bot_grid.addWidget(self._uptime_card, 0, 2)
        layout.addLayout(bot_grid)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Card factories
    # ------------------------------------------------------------------

    def _make_gauge_card(self, title: str) -> MetricCard:
        card = MetricCard(title)
        card.setMinimumHeight(200)

        gauge = CircularGauge()
        gauge.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        gauge.setFixedHeight(120)

        chart = MiniChart(max_value=100, color="#4f8cff")
        chart.setFixedHeight(50)

        card.add_widget(gauge)
        card.add_widget(chart)

        # Stash for update
        card._gauge = gauge  # type: ignore[attr-defined]
        card._chart = chart  # type: ignore[attr-defined]
        return card

    def _make_disk_card(self) -> MetricCard:
        card = MetricCard("Disk")
        card.setMinimumHeight(200)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)

        io_label = QLabel("R: 0 B/s  |  W: 0 B/s")
        io_label.setObjectName("CardSubValue")

        read_chart = MiniChart(auto_scale=True, color="#4ade80")
        read_chart.setFixedHeight(40)
        write_chart = MiniChart(auto_scale=True, color="#f87171")
        write_chart.setFixedHeight(40)

        rw_labels = QHBoxLayout()
        rl = QLabel("Read")
        rl.setObjectName("CardTitle")
        wl = QLabel("Write")
        wl.setObjectName("CardTitle")
        rw_labels.addWidget(rl)
        rw_labels.addStretch()
        rw_labels.addWidget(wl)

        card.add_widget(bar)
        card.add_widget(io_label)
        card.add_layout(rw_labels)
        card.add_widget(read_chart)
        card.add_widget(write_chart)

        card._bar = bar  # type: ignore[attr-defined]
        card._io_label = io_label  # type: ignore[attr-defined]
        card._read_chart = read_chart  # type: ignore[attr-defined]
        card._write_chart = write_chart  # type: ignore[attr-defined]
        return card

    def _make_net_card(self) -> MetricCard:
        card = MetricCard("Network")
        card.setMinimumHeight(200)

        up_label = QLabel("↑  0 B/s")
        up_label.setObjectName("CardSubValue")
        down_label = QLabel("↓  0 B/s")
        down_label.setObjectName("CardSubValue")

        up_chart = MiniChart(auto_scale=True, color="#a78bfa")
        up_chart.setFixedHeight(40)
        down_chart = MiniChart(auto_scale=True, color="#38bdf8")
        down_chart.setFixedHeight(40)

        ud_labels = QHBoxLayout()
        ul = QLabel("Upload")
        ul.setObjectName("CardTitle")
        dl = QLabel("Download")
        dl.setObjectName("CardTitle")
        ud_labels.addWidget(ul)
        ud_labels.addStretch()
        ud_labels.addWidget(dl)

        card.add_widget(up_label)
        card.add_widget(down_label)
        card.add_layout(ud_labels)
        card.add_widget(up_chart)
        card.add_widget(down_chart)

        card._up_label = up_label  # type: ignore[attr-defined]
        card._down_label = down_label  # type: ignore[attr-defined]
        card._up_chart = up_chart  # type: ignore[attr-defined]
        card._down_chart = down_chart  # type: ignore[attr-defined]
        return card

    def _make_temp_card(self) -> MetricCard:
        card = MetricCard("Temperatures")
        card.setMinimumHeight(150)

        temps_widget = QWidget()
        temps_layout = QVBoxLayout(temps_widget)
        temps_layout.setContentsMargins(0, 0, 0, 0)
        temps_layout.setSpacing(4)
        card.add_widget(temps_widget)

        card._temps_layout = temps_layout  # type: ignore[attr-defined]
        card._temps_rows: dict[str, QLabel] = {}  # type: ignore[attr-defined]
        return card

    def _make_battery_card(self) -> MetricCard:
        card = MetricCard("Battery")
        card.setMinimumHeight(150)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        status_label = QLabel("Not available")
        status_label.setObjectName("CardSubValue")

        card.add_widget(bar)
        card.add_widget(status_label)

        card._bar = bar  # type: ignore[attr-defined]
        card._status_label = status_label  # type: ignore[attr-defined]
        return card

    def _make_uptime_card(self) -> MetricCard:
        card = MetricCard("System")
        card.setMinimumHeight(150)

        uptime_label = QLabel("0:00:00")
        uptime_label.setObjectName("CardSubValue")

        load_label = QLabel("Load: — — —")
        load_label.setObjectName("CardSubValue")

        swap_label = QLabel("Swap: —")
        swap_label.setObjectName("CardSubValue")

        card.add_widget(uptime_label)
        card.add_widget(load_label)
        card.add_widget(swap_label)

        card._uptime_label = uptime_label  # type: ignore[attr-defined]
        card._load_label = load_label  # type: ignore[attr-defined]
        card._swap_label = swap_label  # type: ignore[attr-defined]
        return card

    # ------------------------------------------------------------------
    # Live update
    # ------------------------------------------------------------------

    def update_data(self, data: dict) -> None:
        self._update_cpu(data.get("cpu", {}))
        self._update_memory(data.get("memory", {}))
        self._update_disk(data.get("disk", {}))
        self._update_network(data.get("network", {}))
        self._update_sensors(data.get("sensors", {}))
        self._update_uptime(
            data.get("uptime_seconds", 0),
            data.get("memory", {}),
            data.get("cpu", {}),
        )

    def _update_cpu(self, cpu: dict) -> None:
        pct = cpu.get("percent", 0.0)
        self._cpu_card._gauge.set_value(pct)
        self._cpu_card._chart.set_color(color_for_percent(pct))
        self._cpu_card._chart.add_value(pct)
        self._cpu_card.set_value(f"{pct:.1f}%")
        freq = cpu.get("freq_mhz")
        if freq:
            self._cpu_card.set_sub_value(f"{freq:.0f} MHz")

    def _update_memory(self, mem: dict) -> None:
        pct = mem.get("percent", 0.0)
        self._ram_card._gauge.set_value(pct)
        self._ram_card._chart.set_color(color_for_percent(pct))
        self._ram_card._chart.add_value(pct)
        used = mem.get("used", 0)
        total = mem.get("total", 0)
        if total:
            self._ram_card.set_value(f"{bytes_to_human(used)}")
            self._ram_card.set_sub_value(f"of {bytes_to_human(total)}  ({pct:.1f}%)")

    def _update_disk(self, disk: dict) -> None:
        partitions = disk.get("partitions", [])
        if partitions:
            # Show first (usually root) partition
            p = partitions[0]
            pct = p.get("percent", 0.0)
            self._disk_card._bar.setValue(int(pct))
            self._disk_card._bar.setStyleSheet(
                f"QProgressBar::chunk {{ background: {color_for_percent(pct)}; border-radius: 4px; }}"
            )
            self._disk_card.set_value(f"{bytes_to_human(p.get('used', 0))}")
            self._disk_card.set_sub_value(
                f"of {bytes_to_human(p.get('total', 0))}  ({pct:.1f}%)"
            )
        io = disk.get("io", {})
        r = io.get("read_bytes_ps", 0.0)
        w = io.get("write_bytes_ps", 0.0)
        self._disk_card._io_label.setText(f"R: {speed_to_human(r)}  |  W: {speed_to_human(w)}")
        self._disk_card._read_chart.add_value(r)
        self._disk_card._write_chart.add_value(w)

    def _update_network(self, net: dict) -> None:
        interfaces = net.get("interfaces", [])
        total_up = sum(i.get("bytes_sent_ps", 0.0) for i in interfaces)
        total_down = sum(i.get("bytes_recv_ps", 0.0) for i in interfaces)
        self._net_card._up_label.setText(f"↑  {speed_to_human(total_up)}")
        self._net_card._down_label.setText(f"↓  {speed_to_human(total_down)}")
        self._net_card._up_chart.add_value(total_up)
        self._net_card._down_chart.add_value(total_down)
        iface = interfaces[0]["name"] if interfaces else ""
        self._net_card.set_value(iface or "—")

    def _update_sensors(self, sensors: dict) -> None:
        # Temperatures
        temps = sensors.get("temperatures")
        if temps:
            for key, val in list(temps.items())[:6]:
                short_key = key.split("/")[-1] or key
                if short_key not in self._temp_card._temps_rows:
                    row = QLabel()
                    row.setObjectName("CardSubValue")
                    self._temp_card._temps_layout.addWidget(row)
                    self._temp_card._temps_rows[short_key] = row
                color = color_for_temp(val)
                self._temp_card._temps_rows[short_key].setText(
                    f'<span style="color:{color}">{val:.1f}°C</span>  {short_key}'
                )
            self._temp_card.set_value("—")
        else:
            self._temp_card.set_value("N/A")

        # Battery
        battery = sensors.get("battery")
        if battery:
            pct = battery.get("percent", 0.0)
            charging = battery.get("charging", False)
            time_left = battery.get("time_left", "")
            self._battery_card._bar.setValue(int(pct))
            color = "#4ade80" if charging else color_for_percent(pct)
            self._battery_card._bar.setStyleSheet(
                f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
            )
            self._battery_card.set_value(f"{pct:.0f}%")
            status = "Charging" if charging else "Discharging"
            self._battery_card._status_label.setText(f"{status} — {time_left}")
        else:
            self._battery_card.set_value("N/A")
            self._battery_card._status_label.setText("No battery detected")

    def _update_uptime(self, uptime_seconds: float, mem: dict, cpu: dict) -> None:
        self._uptime_card._uptime_label.setText(f"Uptime: {format_uptime(uptime_seconds)}")
        load = cpu.get("load_avg", (0.0, 0.0, 0.0))
        self._uptime_card._load_label.setText(
            f"Load avg: {load[0]:.2f}  {load[1]:.2f}  {load[2]:.2f}"
        )
        swap_pct = mem.get("swap_percent", 0.0)
        swap_used = mem.get("swap_used", 0)
        swap_total = mem.get("swap_total", 0)
        if swap_total:
            self._uptime_card._swap_label.setText(
                f"Swap: {bytes_to_human(swap_used)} / {bytes_to_human(swap_total)} ({swap_pct:.1f}%)"
            )
        else:
            self._uptime_card._swap_label.setText("Swap: None")
