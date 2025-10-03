#!/bin/bash

# This script automates the process of building the 'motion' dependency on macOS.
# It assumes that Homebrew is already installed on the system.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Installing dependencies with Homebrew ---"
brew install ffmpeg pkg-config libjpeg libmicrohttpd automake gettext

echo "--- Cloning motion source code ---"
# Create a secure temporary directory for the source code
TEMP_DIR=$(mktemp -d)
# Ensure the temporary directory is cleaned up on script exit
trap 'rm -rf "$TEMP_DIR"' EXIT

# Clone into the secure temp directory
git clone https://github.com/Motion-Project/motion.git "$TEMP_DIR/motion-src"
cd "$TEMP_DIR/motion-src"

echo "--- Running autoreconf to generate configure script ---"
autoreconf -fiv

echo "--- Running configure script ---"
# We can add more flags here if needed in the future
./configure

echo "--- Building motion ---"
make

echo "--- Installing motion ---"
# This will typically install the 'motion' binary to /usr/local/bin/
sudo make install

echo "--- Build complete! The 'motion' executable should now be available. ---"
