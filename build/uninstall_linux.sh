#!/bin/bash

# This script uninstalls motionEye and its dependencies on Debian/Ubuntu.
# It must be run with root permissions.

echo "--- Checking for root permissions ---"
if (( UID )); then
  echo 'ERROR: Root permissions required. Please run this command with "sudo". Aborting...'
  exit 1
fi

echo "--- Stopping and disabling motionEye service ---"
if systemctl -q is-active motioneye; then
    systemctl stop motioneye
fi
if systemctl -q is-enabled motioneye; then
    systemctl disable motioneye
fi

echo "--- Removing systemd service file ---"
rm -f /etc/systemd/system/motioneye.service
systemctl daemon-reload

echo "--- Uninstalling motioneye Python package ---"
if python3 -m pip show motioneye &> /dev/null; then
    python3 -m pip uninstall -y motioneye
fi

echo "--- Uninstalling Python dependencies ---"
# These were installed alongside motioneye if installed from source
python3 -m pip uninstall -y opencv-python face_recognition paho-mqtt psutil || true

echo "--- Removing system-level dependencies ---"
apt-get remove -y --purge motion ffmpeg v4l-utils
apt-get autoremove -y

echo "--- Removing configuration directory ---"
if [ -d /etc/motioneye ]; then
    read -p "Do you want to remove the configuration directory /etc/motioneye? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf /etc/motioneye
        echo "Removed /etc/motioneye."
    fi
fi

echo "--- Removing media directory ---"
# Default media path is /var/lib/motioneye, but could be changed.
# We will check the default path.
if [ -d /var/lib/motioneye ]; then
    read -p "WARNING: This will delete all your recordings. Do you want to remove the media directory /var/lib/motioneye? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf /var/lib/motioneye
        echo "Removed /var/lib/motioneye."
    fi
fi

echo "--- Uninstallation complete. ---"
