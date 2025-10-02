#!/bin/bash

# This script uninstalls motionEye and its dependencies on macOS.
# It must be run with root permissions.

echo "--- Checking for root permissions ---"
if (( UID )); then
  echo 'ERROR: Root permissions required. Please run this command with "sudo". Aborting...'
  exit 1
fi

echo "--- Unloading and removing motionEye service ---"
if [ -f /Library/LaunchDaemons/com.motioneye-project.motioneye.plist ]; then
    launchctl unload /Library/LaunchDaemons/com.motioneye-project.motioneye.plist || true
    rm -f /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
    echo "Removed launchd service."
fi

echo "--- Uninstalling motioneye Python package ---"
if python3 -m pip show motioneye &> /dev/null; then
    python3 -m pip uninstall -y motioneye
fi

echo "--- Uninstalling Python dependencies ---"
python3 -m pip uninstall -y opencv-python face_recognition paho-mqtt psutil || true

echo "--- Uninstalling Homebrew dependencies ---"
# This will uninstall dependencies installed by the build script.
# We check if they are installed before trying to remove them.
if brew list ffmpeg &> /dev/null; then
    brew uninstall ffmpeg
fi
if brew list pkg-config &> /dev/null; then
    brew uninstall pkg-config
fi
if brew list libjpeg &> /dev/null; then
    brew uninstall libjpeg
fi
if brew list libmicrohttpd &> /dev/null; then
    brew uninstall libmicrohttpd
fi
if brew list automake &> /dev/null; then
    brew uninstall automake
fi
if brew list gettext &> /dev/null; then
    brew uninstall gettext
fi


echo "--- Removing 'motion' binary ---"
rm -f /usr/local/bin/motion

echo "--- Removing configuration directory ---"
if [ -d /usr/local/etc/motioneye ]; then
    read -p "Do you want to remove the configuration directory /usr/local/etc/motioneye? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf /usr/local/etc/motioneye
        echo "Removed /usr/local/etc/motioneye."
    fi
fi

echo "--- A Note on Media Files ---"
echo "Your media files (recordings and pictures) are not removed by this script."
echo "Please check the 'Root Directory' setting for your cameras to find and manually delete them if desired."
echo ""
echo "--- A Note on the .app file ---"
echo "If you created a motionEye.app bundle, you must manually drag it from your /Applications folder to the Trash."
echo ""

echo "--- Uninstallation complete. ---"
