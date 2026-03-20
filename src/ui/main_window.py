"""Main application window."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.collectors.process_collector import ProcessCollector
from src.collectors.system_collector import SystemCollector
from src.config import AppConfig
from src.ui.pages.dashboard import DashboardPage
from src.ui.pages.hardware import HardwarePage
from src.ui.pages.network import NetworkPage
from src.ui.pages.processes import ProcessesPage
from src.ui.pages.storage import StoragePage
from src.ui.settings_dialog import SettingsDialog
from src.ui.sidebar import Sidebar


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

        self._build_ui()
        self._setup_tray_icon()
        self._start_collectors()

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
        self._hardware = HardwarePage()

        self._pages: dict[str, QWidget] = {
            "dashboard": self._dashboard,
            "processes": self._processes,
            "storage": self._storage,
            "network": self._network,
            "hardware": self._hardware,
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

        from PySide6.QtWidgets import QPushButton
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
            # Create a simple coloured pixmap as the icon
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
                self._show_alert(
                    "High CPU Usage",
                    f"CPU usage is at {cpu_pct:.1f}% (threshold: {self._config.cpu_alert_threshold}%).",
                )

        if mem_pct >= self._config.mem_alert_threshold:
            if now - self._last_mem_alert >= self._alert_cooldown:
                self._last_mem_alert = now
                self._show_alert(
                    "High Memory Usage",
                    f"Memory usage is at {mem_pct:.1f}% (threshold: {self._config.mem_alert_threshold}%).",
                )

    def _show_alert(self, title: str, message: str) -> None:
        """Show an alert via system tray notification or fallback QMessageBox."""
        if self._tray_icon is not None and self._tray_icon.supportsMessages():
            self._tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 5000)
        else:
            # Non-blocking fallback using QTimer.singleShot
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, title, message))

    # ------------------------------------------------------------------
    # Collectors
    # ------------------------------------------------------------------

    def _start_collectors(self) -> None:
        self._sys_collector = SystemCollector(interval=self._config.refresh_interval)
        self._sys_collector.data_ready.connect(self._on_system_data)

        self._proc_collector = ProcessCollector(interval=max(2.0, self._config.refresh_interval))
        self._proc_collector.processes_ready.connect(self._on_process_data)

        self._sys_collector.start()
        self._proc_collector.start()

    def _stop_collectors(self) -> None:
        self._sys_collector.stop()
        self._proc_collector.stop()

    def _restart_collectors(self) -> None:
        self._stop_collectors()
        self._start_collectors()

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_system_data(self, data: dict) -> None:
        self._dashboard.update_data(data)
        self._storage.update_data(data)
        self._network.update_data(data)
        self._hardware.update_data(data)
        self._check_alerts(data)

    def _on_process_data(self, processes: list) -> None:
        self._processes.update_processes(processes)

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
        # Restart collectors with new interval
        self._restart_collectors()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_collectors()
        if self._tray_icon is not None:
            self._tray_icon.hide()
        # Save window geometry
        self._config.window_width = self.width()
        self._config.window_height = self.height()
        self._config.save()
        super().closeEvent(event)
