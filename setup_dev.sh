#!/usr/bin/env bash
set -euo pipefail

# Simple helper to set up the macOS development venv and install dependencies.
# Run from repo root: ./setup_dev.sh

echo "==> Ensure Xcode command line tools are installed (may prompt)..."
if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install || true
fi

echo "==> Ensure Homebrew packages are installed..."
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Please install Homebrew first: https://brew.sh"
  exit 1
fi

brew install cmake pkg-config || true
brew install openblas libjpeg libpng libtiff || true
brew install libomp boost || true

echo "==> Recreate virtualenv (motioneye_env)"
rm -rf motioneye_env
python3 -m venv motioneye_env
source motioneye_env/bin/activate
python -m pip install --upgrade pip setuptools wheel

echo "==> Install project and test dependencies"
python -m pip install .
python -m pip install pytest

echo "==> Done. Run 'source motioneye_env/bin/activate' then 'python -m pytest -q' to run tests."
