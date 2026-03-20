"""Main application window."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
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

        self._build_ui()
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
    # Collectors
    # ------------------------------------------------------------------

    def _start_collectors(self) -> None:
        self._sys_collector = SystemCollector(interval=self._config.refresh_interval)
        self._sys_collector.data_ready.connect(self._on_system_data)

        self._proc_collector = ProcessCollector(interval=max(2, self._config.refresh_interval))
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
        # Save window geometry
        self._config.window_width = self.width()
        self._config.window_height = self.height()
        self._config.save()
        super().closeEvent(event)
