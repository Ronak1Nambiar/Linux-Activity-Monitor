"""Session logger: writes JSON-lines metric snapshots to a log file."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path


_DEFAULT_LOG_DIR = Path.home() / ".config" / "linux-monitor" / "logs"


class SessionLogger:
    """Appends one JSON line per metric snapshot to a session log file."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self._dir = log_dir or _DEFAULT_LOG_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = self._dir / f"session_{ts}.jsonl"
        self._file = open(self._path, "a", encoding="utf-8")

    @property
    def path(self) -> Path:
        return self._path

    def log_system(self, data: dict) -> None:
        """Write a sanitized snapshot of system metrics to the log file."""
        try:
            snapshot = {
                "ts": time.time(),
                "cpu_pct": data.get("cpu", {}).get("percent", 0.0),
                "mem_pct": data.get("memory", {}).get("percent", 0.0),
                "mem_used": data.get("memory", {}).get("used", 0),
                "swap_pct": data.get("memory", {}).get("swap_percent", 0.0),
                "disk_read_bps": data.get("disk", {}).get("io", {}).get("read_bytes_ps", 0.0),
                "disk_write_bps": data.get("disk", {}).get("io", {}).get("write_bytes_ps", 0.0),
                "net_recv_bps": sum(
                    i.get("bytes_recv_ps", 0.0)
                    for i in data.get("network", {}).get("interfaces", [])
                ),
                "net_sent_bps": sum(
                    i.get("bytes_sent_ps", 0.0)
                    for i in data.get("network", {}).get("interfaces", [])
                ),
            }
            self._file.write(json.dumps(snapshot) + "\n")
            self._file.flush()
        except Exception:
            pass

    def close(self) -> None:
        try:
            self._file.close()
        except Exception:
            pass
