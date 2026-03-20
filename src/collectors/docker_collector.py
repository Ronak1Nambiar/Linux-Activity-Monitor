"""Background thread that collects Docker container statistics."""

from __future__ import annotations

import json
import subprocess

from PySide6.QtCore import Signal

from .base import BaseCollector


def _parse_size(s: str) -> int:
    """Parse a size string like '1.5MiB', '512kB', '2GiB' to bytes."""
    s = s.strip()
    units = [
        ("TiB", 1 << 40), ("GiB", 1 << 30), ("MiB", 1 << 20), ("KiB", 1 << 10),
        ("TB", 10**12), ("GB", 10**9), ("MB", 10**6), ("kB", 10**3), ("B", 1),
    ]
    for suffix, mult in units:
        if s.endswith(suffix):
            try:
                return int(float(s[: -len(suffix)].strip()) * mult)
            except ValueError:
                return 0
    try:
        return int(float(s))
    except ValueError:
        return 0


class DockerCollector(BaseCollector):
    """Emits ``containers_ready`` with a list of container dicts every interval."""

    containers_ready = Signal(list)

    def __init__(self, interval: int = 5, parent=None):
        super().__init__(interval, parent)
        self._docker_available: bool | None = None

    def _check_docker(self) -> bool:
        if self._docker_available is not None:
            return self._docker_available
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
            self._docker_available = r.returncode == 0
        except Exception:
            self._docker_available = False
        return self._docker_available

    def collect(self) -> None:
        if not self._check_docker():
            self.containers_ready.emit([])
            return

        containers = []
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        # CPU
                        cpu_str = obj.get("CPUPerc", "0%").rstrip("%")
                        cpu_pct = float(cpu_str) if cpu_str else 0.0

                        # Memory: "used / limit"
                        mem_str = obj.get("MemUsage", "0B / 0B")
                        mem_parts = [p.strip() for p in mem_str.split("/")]
                        mem_used = _parse_size(mem_parts[0]) if len(mem_parts) >= 1 else 0
                        mem_limit = _parse_size(mem_parts[1]) if len(mem_parts) >= 2 else 0
                        mem_pct_str = obj.get("MemPerc", "0%").rstrip("%")
                        mem_pct = float(mem_pct_str) if mem_pct_str else 0.0

                        # Network I/O: "rx / tx"
                        net_str = obj.get("NetIO", "0B / 0B")
                        net_parts = [p.strip() for p in net_str.split("/")]
                        net_rx = _parse_size(net_parts[0]) if len(net_parts) >= 1 else 0
                        net_tx = _parse_size(net_parts[1]) if len(net_parts) >= 2 else 0

                        containers.append({
                            "id": obj.get("ID", ""),
                            "name": obj.get("Name", ""),
                            "cpu_pct": cpu_pct,
                            "mem_used": mem_used,
                            "mem_limit": mem_limit,
                            "mem_pct": mem_pct,
                            "net_rx": net_rx,
                            "net_tx": net_tx,
                            "pids": obj.get("PIDs", "0"),
                        })
                    except Exception:
                        pass
        except Exception:
            pass

        self.containers_ready.emit(containers)
