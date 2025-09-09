#!/bin/bash

# This script automates the process of creating a .dmg installer for motionEye on macOS.
# It assumes that the 'motion' binary has already been built and installed
# (e.g., using build_motion_macos.sh) to /usr/local/bin/motion.

# Exit immediately if a command exits with a non-zero status.
set -e

APP_NAME="motionEye"
VERSION=$(python3 -c "import motioneye; print(motioneye.VERSION)")
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
VOL_NAME="${APP_NAME} ${VERSION}"
TEMP_DIR="dist/dmg"

echo "--- Preparing for DMG creation ---"
# Ensure we have a clean slate
rm -rf dist
pip3 install -q py2app

echo "--- Building the .app bundle with py2app ---"
python3 setup.py py2app -A # -A is for alias mode, faster for development

# The .app bundle is now in dist/launcher.app
# We need to rename it to motionEye.app
mv dist/launcher.app "dist/${APP_NAME}.app"

echo "--- Including the 'motion' binary ---"
# The 'motion' binary should be in /usr/local/bin from the previous build step.
# We need to copy it into the .app bundle so it's self-contained.
# The Resources directory is the standard place for this.
MOTION_BINARY="/usr/local/bin/motion"
if [ -f "$MOTION_BINARY" ]; then
    cp "$MOTION_BINARY" "dist/${APP_NAME}.app/Contents/Resources/"
else
    echo "ERROR: motion binary not found at $MOTION_BINARY."
    echo "Please run build_motion_macos.sh first."
    exit 1
fi


echo "--- Creating folder structure for DMG ---"
mkdir -p "${TEMP_DIR}"
mv "dist/${APP_NAME}.app" "${TEMP_DIR}/"
# Add a symbolic link to the Applications folder
ln -s /Applications "${TEMP_DIR}/Applications"

echo "--- Creating the DMG file: ${DMG_NAME} ---"
hdiutil create -volname "${VOL_NAME}" -srcfolder "${TEMP_DIR}" -ov -format UDZO "${DMG_NAME}"

echo "--- DMG creation complete! ---"
echo "Find the installer at ${DMG_NAME}"
# Cleanup the entire dist folder
rm -rf dist
