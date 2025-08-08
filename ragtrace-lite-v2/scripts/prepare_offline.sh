#!/bin/bash

# RAGTrace Lite Offline Deployment Preparation Script
# This script prepares everything needed for offline deployment

set -e

echo "========================================="
echo "RAGTrace Lite Offline Deployment Prep"
echo "========================================="
echo

# Configuration
PYTHON_VERSION=${1:-3.9}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WHEELS_DIR="$PROJECT_ROOT/offline_wheels"
PACKAGE_DIR="$PROJECT_ROOT/offline_package"

echo "Project root: $PROJECT_ROOT"
echo "Python version: $PYTHON_VERSION"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Create virtual environment for collection
echo "Creating temporary virtual environment..."
python3 -m venv /tmp/ragtrace_collect_env
source /tmp/ragtrace_collect_env/bin/activate

# Upgrade pip
pip install --upgrade pip wheel

# Install collection script dependencies
pip install requests

# Run wheel collection
echo "Collecting wheels for offline installation..."
python "$PROJECT_ROOT/scripts/collect_wheels.py" \
    --python-version "$PYTHON_VERSION" \
    --platforms win_amd64 win32 any \
    --create-package

# Deactivate and cleanup temp environment
deactivate
rm -rf /tmp/ragtrace_collect_env

echo
echo "========================================="
echo "Offline package preparation complete!"
echo "========================================="
echo
echo "Package location: $PROJECT_ROOT/ragtrace_lite_offline_${PYTHON_VERSION}.zip"
echo
echo "To deploy:"
echo "1. Copy the ZIP file to the target Windows machine"
echo "2. Extract the ZIP file"
echo "3. Run install_offline.bat as Administrator"
echo