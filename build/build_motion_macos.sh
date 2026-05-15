#!/bin/bash

# This script automates the process of building the 'motion' dependency on macOS.
# It assumes that Homebrew is already installed on the system.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Installing dependencies with Homebrew ---"
# autoconf and libtool are required by autoreconf below; the upstream
# script omitted them, which caused `aclocal: command not found` /
# `libtoolize: not found` failures on fresh systems.
brew install ffmpeg pkg-config libjpeg libmicrohttpd automake autoconf libtool gettext

echo "--- Cloning motion source code ---"
# Create a secure temporary directory for the source code
TEMP_DIR=$(mktemp -d)
# Ensure the temporary directory is cleaned up on script exit
trap 'rm -rf "$TEMP_DIR"' EXIT

# Clone into the secure temp directory
git clone --depth 1 https://github.com/Motion-Project/motion.git "$TEMP_DIR/motion-src"
cd "$TEMP_DIR/motion-src"

# macOS portability patch:
#
# Motion uses the non-standard `ulong` typedef in jpegutils.cpp,
# webu_ans.hpp, and webu_ans.cpp. `ulong` is provided by Linux
# <sys/types.h> as an SVID extension, but is NOT defined on macOS
# (clang). Without this fix, `make` fails with:
#
#   error: unknown type name 'ulong'
#   error: use of undeclared identifier 'ulong'
#
# Replace each occurrence with the portable `unsigned long`. Word-
# boundary regex via perl (BSD sed does not support \b).
echo "--- Applying macOS portability patch (ulong -> unsigned long) ---"
for f in src/jpegutils.cpp src/webu_ans.cpp src/webu_ans.hpp; do
    if [[ -f "$f" ]]; then
        perl -i -pe 's/\bulong\b/unsigned long/g' "$f"
    fi
done

echo "--- Running autoreconf to generate configure script ---"
autoreconf -fiv

echo "--- Running configure script ---"
# Help configure find Homebrew-installed deps (different prefix on
# Apple Silicon vs Intel; pkg-config will resolve both).
HOMEBREW_PREFIX=$(brew --prefix)
export PKG_CONFIG_PATH="$HOMEBREW_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
./configure

echo "--- Building motion ---"
make -j"$(sysctl -n hw.ncpu)"

echo "--- Installing motion ---"
# This will typically install the 'motion' binary to /usr/local/bin/
sudo make install

echo "--- Build complete! The 'motion' executable should now be available. ---"
