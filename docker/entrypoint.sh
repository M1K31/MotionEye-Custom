#!/usr/bin/env sh
# Entrypoint script for motionEye Docker container
# Note: Volumes may be mounted as root, so we handle directory setup here

set -e

# Ensure runtime directory exists and has correct permissions
mkdir -p /run/motioneye
chown motion:motion /run/motioneye

# Copy sample config if no config exists
[ -f '/etc/motioneye/motioneye.conf' ] || cp -a /etc/motioneye.conf.sample /etc/motioneye/motioneye.conf

# Start motionEye server
# Note: We use 'su' here because volume mounts may need root to initially chown
exec su -g motion motion -s /bin/dash -c "LANGUAGE=en exec /usr/local/bin/meyectl startserver -c /etc/motioneye/motioneye.conf"
