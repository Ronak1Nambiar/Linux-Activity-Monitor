#!/usr/bin/env bash
# install.sh — Install Python dependencies for Linux Activity Monitor
set -euo pipefail

echo "==> Linux Activity Monitor — Dependency Installer"
echo ""

# Check Python version
PYTHON=$(command -v python3 || true)
if [ -z "$PYTHON" ]; then
    echo "ERROR: python3 not found. Please install Python 3.9+ first."
    exit 1
fi

PYVER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYMAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PYMINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")
if [ "$PYMAJOR" -lt 3 ] || { [ "$PYMAJOR" -eq 3 ] && [ "$PYMINOR" -lt 9 ]; }; then
    echo "ERROR: Python 3.9 or higher is required (found $PYVER)."
    exit 1
fi

echo "  Python $PYVER found at $PYTHON"
echo ""

# Upgrade pip quietly
echo "==> Upgrading pip..."
"$PYTHON" -m pip install --upgrade pip --quiet

# Install requirements
echo "==> Installing requirements..."
"$PYTHON" -m pip install -r "$(dirname "$0")/requirements.txt"

echo ""
echo "==> Done! Run the app with:"
echo "      python3 main.py"
echo "  or:"
echo "      ./run.sh"
