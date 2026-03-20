"""Utility functions for formatting metric values into human-readable strings."""

from __future__ import annotations


def bytes_to_human(n: float, suffix: str = "B") -> str:
    """Convert a byte count to a human-readable string (e.g. 1.4 GB)."""
    for unit in ("", "K", "M", "G", "T", "P"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}{suffix}"
        n /= 1024.0
    return f"{n:.1f} E{suffix}"


def speed_to_human(bytes_per_sec: float) -> str:
    """Format a transfer speed in bytes/sec to a human-readable string."""
    return bytes_to_human(bytes_per_sec, suffix="B/s")


def format_uptime(seconds: float) -> str:
    """Format an uptime in seconds to 'Xd HH:MM:SS'."""
    total = int(seconds)
    days = total // 86400
    hours = (total % 86400) // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def color_for_percent(percent: float) -> str:
    """Return a hex color string based on utilisation level."""
    if percent < 60:
        return "#4ade80"   # green
    if percent < 80:
        return "#fbbf24"   # amber
    return "#f87171"       # red


def color_for_temp(celsius: float) -> str:
    """Return a hex color string based on temperature level."""
    if celsius < 60:
        return "#4ade80"
    if celsius < 80:
        return "#fbbf24"
    return "#f87171"
