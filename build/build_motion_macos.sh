#!/bin/bash

# This script automates the process of building the 'motion' dependency on macOS.
# It assumes that Homebrew is already installed on the system.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Installing dependencies with Homebrew ---"
brew install ffmpeg pkg-config libjpeg libmicrohttpd automake gettext

echo "--- Exporting required PATH for gettext ---"
# This is required for the build system to find the gettext tools
export PATH="/usr/local/opt/gettext/bin:$PATH"

echo "--- Cloning motion source code ---"
# Clone into a temporary directory
# If the directory already exists, remove it first for a clean build
rm -rf /tmp/motion-src
git clone https://github.com/Motion-Project/motion.git /tmp/motion-src
cd /tmp/motion-src

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
