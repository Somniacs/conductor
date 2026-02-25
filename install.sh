#!/usr/bin/env bash
# conductor — Local orchestration for terminal sessions.
#
# Copyright (c) 2026 Max Rheiner / Somniacs AG
#
# Licensed under the MIT License. You may obtain a copy
# of the license at:
#
#     https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

# Installer for Linux/macOS — sets up Python 3.10+, pipx, and conductor.
set -e

echo "♭ conductor — install"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not found."
    echo "Install Python 3.10+ from https://python.org"
    exit 1
fi

# Check Python version
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "Error: Python 3.10+ required, found $PY_VERSION"
    exit 1
fi

echo "Python $PY_VERSION ✓"

# Install pipx if needed
if ! command -v pipx &>/dev/null; then
    echo "Installing pipx..."
    # On Debian/Ubuntu (PEP 668), pip install is blocked — use apt instead
    if ls /usr/lib/python3*/EXTERNALLY-MANAGED &>/dev/null; then
        echo "Detected externally-managed Python (PEP 668), using apt..."
        sudo apt install -y pipx
    else
        python3 -m pip install --user pipx
    fi
    python3 -m pipx ensurepath
    # Source the updated PATH
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "pipx ✓"

# Get the directory where install.sh lives
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Install conductor
echo ""
echo "Installing conductor..."
pipx install -e "$SCRIPT_DIR" --force

echo ""
echo "Done! Run 'conductor run claude research' to start."
echo ""
echo "If the command is not found, restart your terminal or run:"
echo "  source ~/.bashrc  # or ~/.zshrc"
