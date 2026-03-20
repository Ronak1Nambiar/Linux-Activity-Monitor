"""Background thread that refreshes the running process list."""

import time

import psutil
from PySide6.QtCore import Signal

from .base import BaseCollector


class ProcessCollector(BaseCollector):
    """Emits ``processes_ready`` with a list of process dicts every *interval* seconds."""

    processes_ready = Signal(list)

    def __init__(self, interval: int = 2, parent=None):
        super().__init__(interval, parent)
        self._prev_io: dict[int, tuple[int, int, float]] = {}

    def collect(self):
        now = time.monotonic()
        processes = []
        seen_pids: set[int] = set()
        try:
            attrs = ["pid", "name", "username", "cpu_percent", "memory_percent", "memory_info", "status", "num_threads", "cmdline", "io_counters"]
            for proc in psutil.process_iter(attrs):
                try:
                    info = proc.info
                    pid = info["pid"]
                    seen_pids.add(pid)
                    mem_info = info.get("memory_info")
                    mem_rss = mem_info.rss if mem_info is not None else 0
                    cmdline_parts = info.get("cmdline") or []
                    cmdline_str = " ".join(cmdline_parts) if cmdline_parts else ""
                    cmdline_str = cmdline_str[:80]

                    io_info = info.get("io_counters")
                    io_read_bps = 0.0
                    io_write_bps = 0.0
                    if io_info is not None:
                        prev = self._prev_io.get(pid)
                        if prev:
                            prev_read, prev_write, prev_time = prev
                            dt = now - prev_time
                            if dt > 0:
                                io_read_bps = max(0.0, (io_info.read_bytes - prev_read) / dt)
                                io_write_bps = max(0.0, (io_info.write_bytes - prev_write) / dt)
                        self._prev_io[pid] = (io_info.read_bytes, io_info.write_bytes, now)

                    processes.append(
                        {
                            "pid": pid,
                            "name": info["name"] or "",
                            "username": info["username"] or "",
                            "cpu_percent": round(info["cpu_percent"] or 0.0, 1),
                            "memory_percent": round(info["memory_percent"] or 0.0, 2),
                            "memory_rss": mem_rss,
                            "status": info["status"] or "",
                            "threads": info.get("num_threads") or 0,
                            "cmdline": cmdline_str,
                            "io_read_bps": io_read_bps,
                            "io_write_bps": io_write_bps,
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception:
            pass

        # Clean up stale PIDs
        stale = [pid for pid in self._prev_io if pid not in seen_pids]
        for pid in stale:
            del self._prev_io[pid]

        self.processes_ready.emit(processes)
