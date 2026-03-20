# Linux Activity Monitor

A polished, modern Linux desktop application for monitoring real-time system activity.  Built with **PySide6** (Qt6) and **psutil**, it provides a clean dark/light UI with live-updating charts, a process viewer, storage overview, network monitor, and hardware information — all in one window.

---

## Screenshots

The app opens to the **Dashboard** showing circular gauges for CPU and RAM, scrolling sparkline charts, disk I/O activity, network throughput, temperatures, battery status, and system uptime.

Navigate between five sections using the left sidebar:

| Page        | What you see |
|-------------|-------------|
| **Dashboard** | Live CPU, RAM, Disk, Network gauges + sparklines |
| **Processes** | Sortable, filterable process table |
| **Storage** | Mounted partitions with usage bars + I/O charts |
| **Network** | Per-interface upload/download speeds + charts |
| **Hardware** | Hostname, distro, kernel, CPU, RAM, GPU info |

---

## Why PySide6 + psutil?

| Criterion | PySide6 + psutil | Electron | Tauri | GTK4 |
|-----------|-----------------|----------|-------|------|
| Install size | ~80 MB | ~300 MB | ~20 MB | ~10 MB |
| Languages | Python only | JS + Node | Rust + JS | C / Python |
| Theming | Qt Style Sheets | CSS | CSS | GNOME only |
| Linux metrics | psutil (gold-std) | node-os-lib | sysinfo crate | manual |
| Packaging | PyInstaller/AppImage | electron-builder | cargo-bundle | Flatpak |

PySide6 gives a native-feeling desktop app in pure Python with the least complexity and the best available Linux metrics library.

---

## Requirements

- **OS**: Linux (Ubuntu 20.04+ / Debian 11+ recommended; any modern distro)
- **Python**: 3.9 or higher
- **Display**: X11 or Wayland desktop session

---

## Installation

### Quick start (one command)

```bash
git clone https://github.com/youruser/Linux-Activity-Monitor
cd Linux-Activity-Monitor
./install.sh      # installs PySide6 and psutil via pip
./run.sh          # launches the app
```

### Manual installation

```bash
pip install -r requirements.txt
python3 main.py
```

### System-wide installation (optional)

```bash
pip install --user -r requirements.txt
# Create a launcher
echo '#!/bin/bash
exec python3 /path/to/Linux-Activity-Monitor/main.py "$@"' > ~/.local/bin/linux-monitor
chmod +x ~/.local/bin/linux-monitor
```

---

## Running

```bash
python3 main.py
# or
./run.sh
```

The app reads/writes its settings to `~/.config/linux-monitor/config.json`.

---

## Building a Portable AppImage

```bash
pip install pyinstaller
# Download appimagetool and put it in PATH or ~/bin/
./build_appimage.sh
# Produces: linux-activity-monitor-1.0.0-x86_64.AppImage
```

### Building a .deb package

Install [`fpm`](https://fpm.readthedocs.io/), then:

```bash
pip install pyinstaller
pyinstaller --name linux-activity-monitor --onedir --add-data "assets:assets" main.py
fpm -s dir -t deb \
    -n linux-activity-monitor \
    -v 1.0.0 \
    --description "Linux system activity monitor" \
    --url "https://github.com/youruser/Linux-Activity-Monitor" \
    dist/linux-activity-monitor/=/opt/linux-activity-monitor
```

---

## Architecture

```
Linux-Activity-Monitor/
├── main.py                          # Entry point
├── requirements.txt
├── assets/
│   └── styles/
│       ├── dark.qss                 # Dark theme stylesheet
│       └── light.qss                # Light theme stylesheet
└── src/
    ├── app.py                       # QApplication factory + stylesheet loader
    ├── config.py                    # AppConfig dataclass + JSON persistence
    ├── collectors/
    │   ├── base.py                  # BaseCollector (QThread)
    │   ├── system_collector.py      # CPU / RAM / disk / network / sensors (1s)
    │   └── process_collector.py     # Running process list (2s)
    ├── ui/
    │   ├── main_window.py           # QMainWindow, wires collectors → pages
    │   ├── sidebar.py               # Navigation sidebar
    │   ├── settings_dialog.py       # Settings QDialog
    │   ├── pages/
    │   │   ├── dashboard.py
    │   │   ├── processes.py
    │   │   ├── storage.py
    │   │   ├── network.py
    │   │   └── hardware.py
    │   └── widgets/
    │       ├── circular_gauge.py    # QPainter arc gauge
    │       ├── mini_chart.py        # QPainter scrolling sparkline
    │       ├── metric_card.py       # Rounded card base widget
    │       ├── process_table.py     # Sortable/filterable QTableView
    │       └── section_header.py    # Styled section label
    └── utils/
        ├── formatting.py            # bytes_to_human, format_uptime, color helpers
        └── icons.py                 # Unicode icon map
```

### Data flow

```
SystemCollector (QThread)
  └─ psutil calls every 1s
  └─ emits data_ready(dict)
       └─ MainWindow._on_system_data()
            ├─ DashboardPage.update_data()
            ├─ StoragePage.update_data()
            ├─ NetworkPage.update_data()
            └─ HardwarePage.update_data()

ProcessCollector (QThread)
  └─ psutil.process_iter() every 2s
  └─ emits processes_ready(list)
       └─ ProcessesPage.update_processes()
```

All UI updates happen on the main thread via Qt's cross-thread signal/slot mechanism — completely safe and no manual locking required.

---

## Features

- **Live Dashboard** — CPU gauge, RAM gauge, Disk usage bar, Network speeds, all with 60-second scrolling sparklines
- **Process Viewer** — sortable by CPU/RAM/PID/Name, instant search filter, colour-coded high-CPU rows
- **Storage** — all mounted partitions with usage bars; disk read/write I/O charts
- **Network** — per-interface upload/download speeds with live charts and session totals
- **Hardware** — hostname, distro, kernel, architecture, CPU model, RAM, GPU (NVIDIA via nvidia-smi or lspci fallback)
- **Temperatures** — CPU and other hardware sensor temperatures (where available)
- **Battery** — charge percentage, charging status, time remaining (on laptops)
- **Dark + Light themes** — switch in Settings
- **Configurable refresh rate** — 1 s / 2 s / 5 s
- **Graceful fallbacks** — unavailable metrics show "N/A" instead of crashing

---

## Known Limitations

- GPU metrics require `nvidia-smi` (NVIDIA) or `lspci` (detection only for AMD/Intel)
- Temperature sensors depend on kernel driver support (`/sys/class/hwmon/`); may be unavailable in VMs or containers
- Battery info only available on laptops/UPS-equipped systems
- The app requires a graphical display (X11 or Wayland); does not run headless except with `QT_QPA_PLATFORM=offscreen` for testing
- High process counts (> 500) may cause a brief lag on the 2-second process refresh

---

## Future Improvements

- Per-core CPU usage bars in Dashboard
- AMD GPU support via ROCm/sysfs
- Historical data persistence (SQLite)
- CPU/RAM alert notifications
- .deb and .rpm packaging scripts
- Dark/light auto-switch based on system preference
- Tray icon with quick stats tooltip
- Docker container monitoring

---

## License

MIT License — see `LICENSE` for details.
