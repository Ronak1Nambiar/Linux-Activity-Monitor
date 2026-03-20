#!/usr/bin/env bash
# run.sh — Launch Linux Activity Monitor
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check that dependencies are installed
python3 -c "import PySide6" 2>/dev/null || {
    echo "PySide6 is not installed. Running install.sh first..."
    bash "$SCRIPT_DIR/install.sh"
}

python3 -c "import psutil" 2>/dev/null || {
    echo "psutil is not installed. Running install.sh first..."
    bash "$SCRIPT_DIR/install.sh"
}

exec python3 main.py "$@"
