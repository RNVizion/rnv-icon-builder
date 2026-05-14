#!/bin/bash
# Exit on any error, treat unset vars as errors, fail on pipe errors.
set -euo pipefail

echo "========================================================================"
echo "  RNV Icon Builder - Linux Build"
echo "========================================================================"
echo

# Verify the spec file is here before touching anything.
if [ ! -f "RNV_Icon_Builder.spec" ]; then
    echo "[error] RNV_Icon_Builder.spec not found in current directory."
    echo "Run this script from the project root."
    exit 1
fi

# Verify PyInstaller is installed.
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "[error] pyinstaller not found on PATH."
    echo "Install it with: pip install pyinstaller"
    exit 1
fi

# ------------------------------------------------------------------------
# 1. Clean __pycache__ and stale .pyc files so they don't get bundled.
# ------------------------------------------------------------------------
echo "[1/4] Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# ------------------------------------------------------------------------
# 2. Clean previous PyInstaller outputs so the new build is clean.
# ------------------------------------------------------------------------
echo "[2/4] Removing previous build artifacts..."
rm -rf build dist

# ------------------------------------------------------------------------
# 3. Run PyInstaller using the project's .spec file.
# ------------------------------------------------------------------------
echo "[3/4] Running PyInstaller..."
echo
pyinstaller --clean --noconfirm RNV_Icon_Builder.spec

# ------------------------------------------------------------------------
# 4. Verify the binary exists and report its size.
# ------------------------------------------------------------------------
echo
echo "[4/4] Verifying build output..."

# On Linux, PyInstaller produces a binary without an .exe extension.
# The .spec file controls the actual output name; we check the common one.
BIN_PATH="dist/RNV_Icon_Builder"
if [ ! -f "$BIN_PATH" ]; then
    echo "[error] Build completed but $BIN_PATH was not created."
    echo "Check RNV_Icon_Builder.spec for the configured output name."
    echo "Contents of dist/:"
    ls -la dist/ 2>/dev/null || echo "  (dist/ does not exist)"
    exit 1
fi

# Make sure it's executable (PyInstaller usually does this but be safe).
chmod +x "$BIN_PATH"

# Report size in MB and bytes (du is more portable than stat across distros).
BIN_SIZE=$(wc -c < "$BIN_PATH")
BIN_MB=$((BIN_SIZE / 1048576))

echo
echo "========================================================================"
echo "  Build succeeded"
echo "========================================================================"
echo "  Output:  $BIN_PATH"
echo "  Size:    ${BIN_MB} MB  (${BIN_SIZE} bytes)"
echo "========================================================================"
echo
