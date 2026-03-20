"""Settings dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.config import AppConfig


class SettingsDialog(QDialog):
    """Modal settings dialog.  Emits ``settings_changed(AppConfig)`` on accept."""

    settings_changed = Signal(object)

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(360)
        self.setObjectName("SettingsDialog")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Preferences")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Theme
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        self._theme_combo.setCurrentText(self._config.theme.capitalize())
        form.addRow("Theme:", self._theme_combo)

        # Refresh interval
        self._interval_combo = QComboBox()
        self._interval_combo.addItems(["0.5 seconds", "1 second", "2 seconds", "5 seconds"])
        idx = {0.5: 0, 1: 1, 2: 2, 5: 3}.get(self._config.refresh_interval, 1)
        self._interval_combo.setCurrentIndex(idx)
        form.addRow("Refresh Interval:", self._interval_combo)

        layout.addLayout(form)

        # ---- Alerts section ----
        alerts_title = QLabel("Alerts")
        alerts_title.setObjectName("PageTitle")
        layout.addWidget(alerts_title)

        alerts_form = QFormLayout()
        alerts_form.setSpacing(12)
        alerts_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._cpu_threshold_spin = QSpinBox()
        self._cpu_threshold_spin.setRange(50, 99)
        self._cpu_threshold_spin.setSuffix("%")
        self._cpu_threshold_spin.setValue(self._config.cpu_alert_threshold)
        alerts_form.addRow("CPU Alert Threshold:", self._cpu_threshold_spin)

        self._mem_threshold_spin = QSpinBox()
        self._mem_threshold_spin.setRange(50, 99)
        self._mem_threshold_spin.setSuffix("%")
        self._mem_threshold_spin.setValue(self._config.mem_alert_threshold)
        alerts_form.addRow("Memory Alert Threshold:", self._mem_threshold_spin)

        layout.addLayout(alerts_form)

        # ---- Logging section ----
        logging_title = QLabel("Logging")
        logging_title.setObjectName("PageTitle")
        layout.addWidget(logging_title)

        logging_form = QFormLayout()
        logging_form.setSpacing(12)
        logging_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._session_log_check = QCheckBox("Write metrics to session log file")
        self._session_log_check.setChecked(self._config.session_logging_enabled)
        logging_form.addRow("Session Logging:", self._session_log_check)
        layout.addLayout(logging_form)

        # ---- Dashboard customization section ----
        dash_title = QLabel("Dashboard Cards")
        dash_title.setObjectName("PageTitle")
        layout.addWidget(dash_title)

        dash_hint = QLabel("Uncheck cards to hide them from the dashboard.")
        dash_hint.setObjectName("HintLabel")
        layout.addWidget(dash_hint)

        self._dash_card_checks: dict[str, QCheckBox] = {}
        _card_labels = {
            "cpu": "CPU",
            "memory": "Memory",
            "disk": "Disk",
            "network": "Network",
            "gpu": "GPU",
            "temperatures": "Temperatures",
            "battery": "Battery",
            "system": "System / Uptime",
        }
        dash_form = QFormLayout()
        dash_form.setSpacing(8)
        hidden = set(self._config.dashboard_hidden_cards)
        for key, label in _card_labels.items():
            cb = QCheckBox(label)
            cb.setChecked(key not in hidden)
            self._dash_card_checks[key] = cb
            dash_form.addRow("", cb)
        layout.addLayout(dash_form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        theme = self._theme_combo.currentText().lower()
        interval_map = {0: 0.5, 1: 1.0, 2: 2.0, 3: 5.0}
        interval = interval_map.get(self._interval_combo.currentIndex(), 1.0)

        self._config.theme = theme
        self._config.refresh_interval = interval
        self._config.cpu_alert_threshold = self._cpu_threshold_spin.value()
        self._config.mem_alert_threshold = self._mem_threshold_spin.value()
        self._config.session_logging_enabled = self._session_log_check.isChecked()
        self._config.dashboard_hidden_cards = [
            key for key, cb in self._dash_card_checks.items() if not cb.isChecked()
        ]
        self._config.save()
        self.settings_changed.emit(self._config)
        self.accept()
