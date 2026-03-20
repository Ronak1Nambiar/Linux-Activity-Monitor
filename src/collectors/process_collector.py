"""Background thread that refreshes the running process list."""

import psutil
from PySide6.QtCore import Signal

from .base import BaseCollector


class ProcessCollector(BaseCollector):
    """Emits ``processes_ready`` with a list of process dicts every *interval* seconds."""

    processes_ready = Signal(list)

    def __init__(self, interval: int = 2, parent=None):
        super().__init__(interval, parent)

    def collect(self):
        processes = []
        try:
            attrs = ["pid", "name", "username", "cpu_percent", "memory_percent", "memory_info", "status"]
            for proc in psutil.process_iter(attrs):
                try:
                    info = proc.info
                    processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"] or "",
                            "username": info["username"] or "",
                            "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                            "memory_percent": round(info["memory_percent"] or 0.0, 2),
                            "memory_rss": info["memory_info"].rss if info.get("memory_info") else 0,
                            "status": info["status"] or "",
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass

        self.processes_ready.emit(processes)
