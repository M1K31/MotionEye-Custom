#!/bin/bash

# This script automates the installation and setup of motionEye as a
# background service on macOS.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Checking for root permissions ---"
if (( UID )); then
  echo 'ERROR: Root permissions required. Please run this command with "sudo". Aborting...'
  exit 1
fi

echo "--- Creating configuration directory [/usr/local/etc/motioneye] ---"
mkdir -p /usr/local/etc/motioneye

if [ ! -f /usr/local/etc/motioneye/motioneye.conf ]; then
    echo "--- Installing default motioneye.conf.sample ---"
    cp motioneye/extra/motioneye.conf.sample /usr/local/etc/motioneye/motioneye.conf
else
    echo "--- /usr/local/etc/motioneye/motioneye.conf already exists, skipping. ---"
fi

# Replace lines 25-27 with:
echo "--- Creating log directory [/var/log] and log file ---"
mkdir -p /var/log
touch /var/log/motioneye.log
chmod 640 /var/log/motioneye.log  # Only owner and group can read
chown root:wheel /var/log/motioneye.log


echo "--- Installing launchd service file [motioneye.plist] ---"
# Unload the service if it's already running to ensure a clean start
if [ -f /Library/LaunchDaemons/com.motioneye-project.motioneye.plist ]; then
    echo "--- Unloading existing service ---"
    launchctl unload /Library/LaunchDaemons/com.motioneye-project.motioneye.plist || true
fi

cp motioneye/extra/motioneye.plist /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
chown root:wheel /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
chmod 644 /Library/LaunchDaemons/com.motioneye-project.motioneye.plist

echo "--- Loading and starting motionEye service ---"
launchctl load /Library/LaunchDaemons/com.motioneye-project.motioneye.plist

echo "--- Installation complete! ---"
echo "motionEye should now be running in the background."
echo "Configuration is at /usr/local/etc/motioneye/motioneye.conf"
echo "Logs are at /var/log/motioneye.log"
