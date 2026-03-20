"""Hardware / system information page (static + refreshed slowly)."""

from __future__ import annotations

import platform
import socket
import subprocess

import psutil
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

from src.ui.widgets.section_header import SectionHeader
from src.utils.formatting import bytes_to_human, format_uptime


def _read_cpu_model() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown"


def _get_distro() -> str:
    try:
        import distro  # type: ignore[import]
        return f"{distro.name()} {distro.version()}".strip()
    except Exception:
        pass
    try:
        with open("/etc/os-release") as f:
            info = {}
            for line in f:
                if "=" in line:
                    k, _, v = line.strip().partition("=")
                    info[k] = v.strip('"')
        return info.get("PRETTY_NAME") or info.get("NAME", platform.system())
    except Exception:
        return platform.system()


def _get_gpu_info() -> list[str]:
    # NVIDIA via nvidia-smi
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpus = []
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    gpus.append(f"{parts[0]}  ({parts[1]} MB VRAM)")
                else:
                    gpus.append(parts[0])
            return gpus
    except Exception:
        pass

    # Fallback: lspci
    try:
        result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.splitlines():
                lower = line.lower()
                if any(kw in lower for kw in ("vga", "3d controller", "display controller")):
                    after = line.split(": ", 1)
                    gpus.append(after[1].strip() if len(after) > 1 else line.strip())
            if gpus:
                return gpus
    except Exception:
        pass

    return ["No GPU detected"]


def _collect_system_info() -> dict:
    info: dict = {}
    info["hostname"] = socket.gethostname()
    info["distro"] = _get_distro()
    info["kernel"] = platform.release()
    info["architecture"] = platform.machine()
    info["python"] = platform.python_version()
    info["cpu_model"] = _read_cpu_model()
    info["cpu_cores"] = psutil.cpu_count(logical=False) or 1
    info["cpu_threads"] = psutil.cpu_count(logical=True) or 1
    try:
        freq = psutil.cpu_freq()
        info["cpu_freq_max"] = f"{freq.max:.0f} MHz" if freq and freq.max else "—"
    except Exception:
        info["cpu_freq_max"] = "—"
    try:
        vm = psutil.virtual_memory()
        info["total_ram"] = vm.total
    except Exception:
        info["total_ram"] = 0
    try:
        swap = psutil.swap_memory()
        info["total_swap"] = swap.total
    except Exception:
        info["total_swap"] = 0
    info["gpus"] = _get_gpu_info()
    import time as _time
    try:
        boot_ts = psutil.boot_time()
        import datetime
        boot_dt = datetime.datetime.fromtimestamp(boot_ts)
        info["boot_time"] = boot_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        info["boot_time"] = "—"
    return info


class _InfoRow(QWidget):
    """A two-column label / value row."""

    def __init__(self, label: str, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        lbl = QLabel(label)
        lbl.setObjectName("CardTitle")
        lbl.setFixedWidth(160)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._val = QLabel(value)
        self._val.setObjectName("CardSubValue")
        self._val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._val.setWordWrap(True)

        layout.addWidget(lbl)
        layout.addWidget(self._val, 1)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class HardwarePage(QWidget):
    """Displays static and slowly-changing system information."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._uptime_row: _InfoRow | None = None
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

        title = QLabel("Hardware & System")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        info = _collect_system_info()

        # System section
        layout.addWidget(SectionHeader("System"))
        sys_card = self._make_card(
            [
                ("Hostname", info.get("hostname", "—")),
                ("Distribution", info.get("distro", "—")),
                ("Kernel", info.get("kernel", "—")),
                ("Architecture", info.get("architecture", "—")),
                ("Uptime", "—"),
                ("Boot Time", info.get("boot_time", "—")),
                ("Python", info.get("python", "—")),
            ],
            uptime_slot=True,
        )
        layout.addWidget(sys_card)

        # CPU section
        layout.addWidget(SectionHeader("CPU"))
        layout.addWidget(
            self._make_card(
                [
                    ("Model", info.get("cpu_model", "—")),
                    ("Physical Cores", str(info.get("cpu_cores", "—"))),
                    ("Logical Threads", str(info.get("cpu_threads", "—"))),
                    ("Max Frequency", info.get("cpu_freq_max", "—")),
                ]
            )
        )

        # Memory section
        layout.addWidget(SectionHeader("Memory"))
        layout.addWidget(
            self._make_card(
                [
                    ("Total RAM", bytes_to_human(info.get("total_ram", 0))),
                    ("Total Swap", bytes_to_human(info.get("total_swap", 0)) if info.get("total_swap") else "None"),
                ]
            )
        )

        # GPU section
        layout.addWidget(SectionHeader("GPU"))
        gpus = info.get("gpus", ["No GPU detected"])
        gpu_rows = [(f"GPU {i + 1}", g) for i, g in enumerate(gpus)]
        layout.addWidget(self._make_card(gpu_rows or [("GPU", "No GPU detected")]))

        layout.addStretch()

    def _make_card(self, rows: list[tuple[str, str]], uptime_slot: bool = False) -> QFrame:
        card = QFrame()
        card.setObjectName("MetricCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(8)

        for label, value in rows:
            row = _InfoRow(label, value)
            card_layout.addWidget(row)
            if uptime_slot and label == "Uptime":
                self._uptime_row = row

        return card

    # ------------------------------------------------------------------
    # Live update (only uptime refreshes)
    # ------------------------------------------------------------------

    def update_data(self, data: dict) -> None:
        uptime = data.get("uptime_seconds", 0.0)
        if self._uptime_row:
            self._uptime_row.set_value(format_uptime(uptime))
