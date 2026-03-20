# Linux Activity Monitor

A modern, real-time Linux system monitor built with **PySide6** and **psutil**. It provides a polished dark/light UI with live-updating gauges, sparkline charts, per-core CPU bars, a full-featured process viewer, disk and network I/O monitoring, and hardware information — all in a single desktop window.

> *Screenshot: Dark theme dashboard with CPU/RAM gauges, per-core bars, and live sparklines*

---

## Features

- **Live CPU monitoring** with ring gauge, sparkline history, and per-core utilisation bars
- **Memory (RAM + swap) monitoring** with usage gauge
- **Disk partition usage** with live I/O read/write charts
- **Network per-interface monitoring** with upload/download speeds and packet counters
- **Process viewer**: sortable table with Threads column, multi-column search (name/user/PID), color-coded status, Kill Process button
- **Hardware info**: CPU model, cores, RAM, GPU detection, boot time
- **Dark and light themes**, switchable at runtime
- **Configurable refresh interval**: 0.5s, 1s, 2s, 5s
- **Settings persisted** to `~/.config/linux-monitor/config.json`

---

## Requirements

- Python 3.10+
- PySide6
- psutil
- distro

---

## Installation

```bash
git clone https://github.com/Ronak1Nambiar/Linux-Activity-Monitor.git
cd Linux-Activity-Monitor
bash install.sh
```

---

## Running

```bash
bash run.sh
# or
python3 main.py
```

---

## Project Structure

```
Linux-Activity-Monitor/
├── main.py
├── requirements.txt
├── src/
│   ├── collectors/        # QThread-based data collectors (CPU, RAM, processes, etc.)
│   ├── ui/
│   │   ├── pages/         # Dashboard, Processes, Storage, Network, Hardware pages
│   │   └── widgets/       # Reusable widgets (gauges, sparklines, metric cards)
│   └── utils/             # Formatting helpers, icon utilities
└── assets/
    └── styles/            # Dark and light QSS theme stylesheets
```

---

## License

MIT
