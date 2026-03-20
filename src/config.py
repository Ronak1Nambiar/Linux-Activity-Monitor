"""Application configuration — persisted to ~/.config/linux-monitor/config.json."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


_CONFIG_DIR = Path.home() / ".config" / "linux-monitor"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_VALID_THEMES = {"dark", "light"}
_VALID_INTERVALS = {0.5, 1, 2, 5}


@dataclass
class AppConfig:
    theme: str = "dark"
    refresh_interval: float = 1
    window_width: int = 1200
    window_height: int = 800
    cpu_alert_threshold: int = 90
    mem_alert_threshold: int = 90

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "AppConfig":
        try:
            with open(_CONFIG_FILE) as f:
                data = json.load(f)
            # Filter to known keys only so future removals don't error
            known = {k for k in cls.__dataclass_fields__}
            filtered = {k: v for k, v in data.items() if k in known}
            cfg = cls(**filtered)
            # Validate
            if cfg.theme not in _VALID_THEMES:
                cfg.theme = "dark"
            if cfg.refresh_interval not in _VALID_INTERVALS:
                cfg.refresh_interval = 1
            if not (50 <= cfg.cpu_alert_threshold <= 99):
                cfg.cpu_alert_threshold = 90
            if not (50 <= cfg.mem_alert_threshold <= 99):
                cfg.mem_alert_threshold = 90
            return cfg
        except Exception:
            return cls()
