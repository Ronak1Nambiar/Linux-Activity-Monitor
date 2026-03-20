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
            attrs = ["pid", "name", "username", "cpu_percent", "memory_percent", "memory_info", "status", "num_threads", "cmdline"]
            for proc in psutil.process_iter(attrs):
                try:
                    info = proc.info
                    mem_info = info.get("memory_info")
                    mem_rss = mem_info.rss if mem_info is not None else 0
                    cmdline_parts = info.get("cmdline") or []
                    cmdline_str = " ".join(cmdline_parts) if cmdline_parts else ""
                    cmdline_str = cmdline_str[:80]
                    processes.append(
                        {
                            "pid": info["pid"],
                            "name": info["name"] or "",
                            "username": info["username"] or "",
                            "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                            "memory_percent": round(info["memory_percent"] or 0.0, 2),
                            "memory_rss": mem_rss,
                            "status": info["status"] or "",
                            "threads": info.get("num_threads") or 0,
                            "cmdline": cmdline_str,
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass

        self.processes_ready.emit(processes)
