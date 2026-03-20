"""Main application window."""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.collectors.docker_collector import DockerCollector
from src.collectors.process_collector import ProcessCollector
from src.collectors.system_collector import SystemCollector
from src.config import AppConfig
from src.ui.pages.alerts import AlertsPage
from src.ui.pages.dashboard import DashboardPage
from src.ui.pages.docker_page import DockerPage
from src.ui.pages.hardware import HardwarePage
from src.ui.pages.history import HistoryPage
from src.ui.pages.network import NetworkPage
from src.ui.pages.processes import ProcessesPage
from src.ui.pages.storage import StoragePage
from src.ui.settings_dialog import SettingsDialog
from src.ui.sidebar import Sidebar
from src.utils.session_logger import SessionLogger


class MainWindow(QMainWindow):
    """Top-level window that orchestrates collectors, sidebar, and page stack."""

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Linux Activity Monitor")
        self.resize(config.window_width, config.window_height)
        self.setMinimumSize(900, 600)

        # Alert cooldown tracking (monotonic timestamps of last alert)
        self._last_cpu_alert: float = 0.0
        self._last_mem_alert: float = 0.0
        self._alert_cooldown: float = 60.0  # seconds

        # Last system snapshot for export
        self._last_system_data: dict = {}

        # Session logger (may be None if disabled)
        self._session_logger: SessionLogger | None = None
        if config.session_logging_enabled:
            self._session_logger = SessionLogger()

        self._build_ui()
        self._setup_tray_icon()
        self._start_collectors()
        self._apply_dashboard_visibility()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- Header bar ----
        header = self._make_header()
        outer.addWidget(header)

        # ---- Body: sidebar + page stack ----
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._navigate)
        body.addWidget(self._sidebar)

        # Thin separator
        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setObjectName("Separator")
        body.addWidget(sep)

        self._stack = QStackedWidget()
        body.addWidget(self._stack, 1)

        outer.addLayout(body, 1)

        # ---- Pages ----
        self._dashboard = DashboardPage()
        self._processes = ProcessesPage()
        self._storage = StoragePage()
        self._network = NetworkPage()
        self._history = HistoryPage()
        self._hardware = HardwarePage()
        self._alerts = AlertsPage()
        self._docker = DockerPage()

        self._pages: dict[str, QWidget] = {
            "dashboard": self._dashboard,
            "processes": self._processes,
            "storage": self._storage,
            "network": self._network,
            "history": self._history,
            "hardware": self._hardware,
            "alerts": self._alerts,
            "docker": self._docker,
        }
        for page in self._pages.values():
            self._stack.addWidget(page)

        # Navigate to dashboard
        self._sidebar.select_default()

    def _make_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(52)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        logo = QLabel("Linux Activity Monitor")
        logo.setObjectName("HeaderTitle")
        layout.addWidget(logo)
        layout.addStretch()

        self._status_label = QLabel("●  Running")
        self._status_label.setObjectName("StatusLabel")
        layout.addWidget(self._status_label)

        export_btn = QPushButton("Export Snapshot")
        export_btn.setObjectName("HeaderButton")
        export_btn.setFixedHeight(32)
        export_btn.setToolTip("Export current system metrics snapshot")
        export_btn.clicked.connect(self._on_export_snapshot)
        layout.addWidget(export_btn)

        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("HeaderButton")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        return header

    # ------------------------------------------------------------------
    # System tray
    # ------------------------------------------------------------------

    def _setup_tray_icon(self) -> None:
        """Create a system tray icon if the platform supports it."""
        self._tray_icon: QSystemTrayIcon | None = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.darkCyan)
            icon = QIcon(pixmap)
            self._tray_icon = QSystemTrayIcon(icon, self)
            self._tray_icon.setToolTip("Linux Activity Monitor")
            self._tray_icon.show()

    # ------------------------------------------------------------------
    # Threshold alerts
    # ------------------------------------------------------------------

    def _check_alerts(self, data: dict) -> None:
        """Compare CPU/memory values against configured thresholds and alert."""
        now = time.monotonic()

        cpu_pct = data.get("cpu", {}).get("percent", 0.0)
        mem_pct = data.get("memory", {}).get("percent", 0.0)

        if cpu_pct >= self._config.cpu_alert_threshold:
            if now - self._last_cpu_alert >= self._alert_cooldown:
                self._last_cpu_alert = now
                msg = f"CPU usage is at {cpu_pct:.1f}% (threshold: {self._config.cpu_alert_threshold}%)."
                self._show_alert("High CPU Usage", msg)
                self._alerts.add_alert("High CPU Usage", msg)

        if mem_pct >= self._config.mem_alert_threshold:
            if now - self._last_mem_alert >= self._alert_cooldown:
                self._last_mem_alert = now
                msg = f"Memory usage is at {mem_pct:.1f}% (threshold: {self._config.mem_alert_threshold}%)."
                self._show_alert("High Memory Usage", msg)
                self._alerts.add_alert("High Memory Usage", msg)

    def _show_alert(self, title: str, message: str) -> None:
        """Show an alert via system tray notification or fallback QMessageBox."""
        if self._tray_icon is not None and self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 5000)
        else:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, title, message))

    # ------------------------------------------------------------------
    # System metrics export
    # ------------------------------------------------------------------

    def _on_export_snapshot(self) -> None:
        """Export the last system metrics snapshot to JSON or CSV."""
        if not self._last_system_data:
            QMessageBox.information(self, "No Data", "No system data available yet.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export System Snapshot",
            f"system_snapshot_{ts}",
            "JSON Files (*.json);;CSV Files (*.csv)",
        )
        if not path:
            return

        try:
            if selected_filter.startswith("CSV") or path.endswith(".csv"):
                self._export_snapshot_csv(path)
            else:
                self._export_snapshot_json(path)
            QMessageBox.information(self, "Export Successful", f"Snapshot exported to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Could not export snapshot:\n{e}")

    def _export_snapshot_json(self, path: str) -> None:
        data = self._last_system_data
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "cpu": data.get("cpu", {}),
            "memory": data.get("memory", {}),
            "disk": {
                "partitions": data.get("disk", {}).get("partitions", []),
                "io": data.get("disk", {}).get("io", {}),
            },
            "network": data.get("network", {}),
            "gpu": data.get("gpu", []),
            "sensors": {
                "temperatures": data.get("sensors", {}).get("temperatures"),
                "battery": data.get("sensors", {}).get("battery"),
            },
            "uptime_seconds": data.get("uptime_seconds", 0),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

    def _export_snapshot_csv(self, path: str) -> None:
        data = self._last_system_data
        rows = []
        rows.append(("metric", "value"))
        rows.append(("timestamp", datetime.now().isoformat()))
        cpu = data.get("cpu", {})
        rows.append(("cpu_percent", cpu.get("percent", 0.0)))
        rows.append(("cpu_freq_mhz", cpu.get("freq_mhz", "")))
        rows.append(("cpu_core_count", cpu.get("core_count", "")))
        mem = data.get("memory", {})
        rows.append(("mem_percent", mem.get("percent", 0.0)))
        rows.append(("mem_used_bytes", mem.get("used", 0)))
        rows.append(("mem_total_bytes", mem.get("total", 0)))
        rows.append(("mem_cached_bytes", mem.get("cached", 0)))
        rows.append(("mem_buffers_bytes", mem.get("buffers", 0)))
        rows.append(("swap_percent", mem.get("swap_percent", 0.0)))
        disk_io = data.get("disk", {}).get("io", {})
        rows.append(("disk_read_bps", disk_io.get("read_bytes_ps", 0.0)))
        rows.append(("disk_write_bps", disk_io.get("write_bytes_ps", 0.0)))
        ifaces = data.get("network", {}).get("interfaces", [])
        rows.append(("net_total_recv_bps", sum(i.get("bytes_recv_ps", 0.0) for i in ifaces)))
        rows.append(("net_total_sent_bps", sum(i.get("bytes_sent_ps", 0.0) for i in ifaces)))
        rows.append(("uptime_seconds", data.get("uptime_seconds", 0)))
        gpus = data.get("gpu", [])
        for i, g in enumerate(gpus):
            rows.append((f"gpu_{i}_load_pct", g.get("load_pct", 0.0)))
            rows.append((f"gpu_{i}_mem_used_mb", g.get("mem_used_mb", 0)))
            rows.append((f"gpu_{i}_temp_c", g.get("temp_c", "")))
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    # ------------------------------------------------------------------
    # Dashboard visibility
    # ------------------------------------------------------------------

    def _apply_dashboard_visibility(self) -> None:
        self._dashboard.apply_visibility(self._config.dashboard_hidden_cards)

    # ------------------------------------------------------------------
    # Collectors
    # ------------------------------------------------------------------

    def _start_collectors(self) -> None:
        self._sys_collector = SystemCollector(interval=self._config.refresh_interval)
        self._sys_collector.data_ready.connect(self._on_system_data)

        self._proc_collector = ProcessCollector(interval=max(2.0, self._config.refresh_interval))
        self._proc_collector.processes_ready.connect(self._on_process_data)

        self._docker_collector = DockerCollector(interval=5)
        self._docker_collector.containers_ready.connect(self._on_docker_data)

        self._sys_collector.start()
        self._proc_collector.start()
        self._docker_collector.start()

    def _stop_collectors(self) -> None:
        self._sys_collector.stop()
        self._proc_collector.stop()
        self._docker_collector.stop()

    def _restart_collectors(self) -> None:
        self._stop_collectors()
        self._start_collectors()

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_system_data(self, data: dict) -> None:
        self._last_system_data = data
        self._dashboard.update_data(data)
        self._storage.update_data(data)
        self._network.update_data(data)
        self._hardware.update_data(data)
        self._history.update_data(data)
        self._check_alerts(data)
        if self._session_logger is not None:
            self._session_logger.log_system(data)

    def _on_process_data(self, processes: list) -> None:
        self._processes.update_processes(processes)

    def _on_docker_data(self, containers: list) -> None:
        self._docker.update_containers(containers)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, key: str) -> None:
        if key == "settings":
            self._open_settings()
            return
        page = self._pages.get(key)
        if page:
            self._stack.setCurrentWidget(page)
            self._sidebar.set_active(key)

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._config, parent=self)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()

    def _apply_settings(self, config: AppConfig) -> None:
        self._config = config
        # Reload stylesheet
        from src.app import load_stylesheet
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(load_stylesheet(config.theme))
        # Update session logger
        if config.session_logging_enabled and self._session_logger is None:
            self._session_logger = SessionLogger()
        elif not config.session_logging_enabled and self._session_logger is not None:
            self._session_logger.close()
            self._session_logger = None
        # Apply dashboard card visibility
        self._apply_dashboard_visibility()
        # Restart collectors with new interval
        self._restart_collectors()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_collectors()
        if self._tray_icon is not None:
            self._tray_icon.hide()
        if self._session_logger is not None:
            self._session_logger.close()
        # Save window geometry
        self._config.window_width = self.width()
        self._config.window_height = self.height()
        self._config.save()
        super().closeEvent(event)
