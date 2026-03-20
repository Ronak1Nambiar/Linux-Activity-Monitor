"""Background thread that collects all real-time system metrics each second."""

import os
import time

import psutil
from PySide6.QtCore import Signal

from .base import BaseCollector


class SystemCollector(BaseCollector):
    """Emits a ``data_ready`` signal with a snapshot dict every *interval* seconds."""

    data_ready = Signal(dict)

    def __init__(self, interval: int = 1, parent=None):
        super().__init__(interval, parent)
        self._prev_disk_io = None
        self._prev_net_io = None
        self._prev_time: float | None = None

    # ------------------------------------------------------------------
    # BaseCollector protocol
    # ------------------------------------------------------------------

    def _init(self):
        # Prime the cpu_percent counter so the first real reading is accurate
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(percpu=True, interval=None)
        except Exception:
            pass
        # Capture baseline IO counters
        try:
            self._prev_disk_io = psutil.disk_io_counters()
        except Exception:
            pass
        try:
            self._prev_net_io = psutil.net_io_counters(pernic=True)
        except Exception:
            pass
        self._prev_time = time.monotonic()

    def collect(self):
        now = time.monotonic()
        data: dict = {}

        data["cpu"] = self._get_cpu()
        data["memory"] = self._get_memory()
        data["disk"] = self._get_disk(now)
        data["network"] = self._get_network(now)
        data["sensors"] = self._get_sensors()
        data["uptime_seconds"] = self._get_uptime()

        self._prev_time = now
        self.data_ready.emit(data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_cpu(self) -> dict:
        try:
            freq = psutil.cpu_freq()
            try:
                load_avg = os.getloadavg()
            except AttributeError:
                load_avg = (0.0, 0.0, 0.0)
            return {
                "percent": psutil.cpu_percent(interval=None),
                "per_core": psutil.cpu_percent(percpu=True, interval=None),
                "freq_mhz": freq.current if freq else None,
                "load_avg": load_avg,
                "core_count": psutil.cpu_count(logical=False) or 1,
                "thread_count": psutil.cpu_count(logical=True) or 1,
            }
        except Exception:
            return {
                "percent": 0.0,
                "per_core": [],
                "freq_mhz": None,
                "load_avg": (0.0, 0.0, 0.0),
                "core_count": 1,
                "thread_count": 1,
            }

    def _get_memory(self) -> dict:
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                "total": vm.total,
                "used": vm.used,
                "available": vm.available,
                "percent": vm.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent,
            }
        except Exception:
            return {
                "total": 0,
                "used": 0,
                "available": 0,
                "percent": 0.0,
                "swap_total": 0,
                "swap_used": 0,
                "swap_percent": 0.0,
            }

    def _get_disk(self, now: float) -> dict:
        partitions = []
        try:
            for p in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    partitions.append(
                        {
                            "device": p.device,
                            "mountpoint": p.mountpoint,
                            "fstype": p.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                        }
                    )
                except Exception:
                    pass
        except Exception:
            pass

        io_read_ps = 0.0
        io_write_ps = 0.0
        try:
            current = psutil.disk_io_counters()
            if current and self._prev_disk_io and self._prev_time:
                dt = now - self._prev_time
                if dt > 0:
                    io_read_ps = (current.read_bytes - self._prev_disk_io.read_bytes) / dt
                    io_write_ps = (current.write_bytes - self._prev_disk_io.write_bytes) / dt
            self._prev_disk_io = current
        except Exception:
            self._prev_disk_io = None

        return {
            "partitions": partitions,
            "io": {
                "read_bytes_ps": max(0.0, io_read_ps),
                "write_bytes_ps": max(0.0, io_write_ps),
            },
        }

    def _get_network(self, now: float) -> dict:
        interfaces = []
        try:
            current = psutil.net_io_counters(pernic=True)
            for name, counters in current.items():
                if name == "lo":
                    continue
                sent_ps = 0.0
                recv_ps = 0.0
                if self._prev_net_io and name in self._prev_net_io and self._prev_time:
                    dt = now - self._prev_time
                    if dt > 0:
                        prev = self._prev_net_io[name]
                        sent_ps = (counters.bytes_sent - prev.bytes_sent) / dt
                        recv_ps = (counters.bytes_recv - prev.bytes_recv) / dt
                interfaces.append(
                    {
                        "name": name,
                        "bytes_sent_ps": max(0.0, sent_ps),
                        "bytes_recv_ps": max(0.0, recv_ps),
                        "total_sent": counters.bytes_sent,
                        "total_recv": counters.bytes_recv,
                    }
                )
            self._prev_net_io = current
        except Exception:
            self._prev_net_io = None

        return {"interfaces": interfaces}

    def _get_sensors(self) -> dict:
        sensors: dict = {"temperatures": None, "fans": [], "battery": None}

        # Temperatures
        try:
            raw = psutil.sensors_temperatures()
            if raw:
                result = {}
                for hw_name, entries in raw.items():
                    for entry in entries:
                        key = f"{hw_name}/{entry.label}" if entry.label else hw_name
                        result[key] = round(entry.current, 1)
                if result:
                    sensors["temperatures"] = result
        except Exception:
            pass

        # Fans
        try:
            raw_fans = psutil.sensors_fans()
            if raw_fans:
                for hw_name, entries in raw_fans.items():
                    for entry in entries:
                        sensors["fans"].append(
                            {
                                "label": entry.label or hw_name,
                                "rpm": entry.current,
                            }
                        )
        except Exception:
            pass

        # Battery
        try:
            bat = psutil.sensors_battery()
            if bat:
                if bat.secsleft == psutil.POWER_TIME_UNLIMITED:
                    time_str = "Plugged in"
                elif bat.secsleft == psutil.POWER_TIME_UNKNOWN or bat.secsleft < 0:
                    time_str = "Unknown"
                else:
                    h = int(bat.secsleft) // 3600
                    m = (int(bat.secsleft) % 3600) // 60
                    time_str = f"{h}h {m:02d}m remaining"
                sensors["battery"] = {
                    "percent": bat.percent,
                    "charging": bat.power_plugged,
                    "time_left": time_str,
                }
        except Exception:
            pass

        return sensors

    def _get_uptime(self) -> float:
        try:
            return time.time() - psutil.boot_time()
        except Exception:
            return 0.0
