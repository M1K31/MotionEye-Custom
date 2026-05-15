#!/usr/bin/env sh
# Entrypoint for the motionEye container.
#
# This script starts as root (the Dockerfile intentionally does NOT
# set `USER motion`) so it can:
#   1. create the runtime directory under /run (root-owned),
#   2. fix ownership of volume-mounted directories — host bind
#      mounts and fresh named volumes arrive owned by root, and
#      /etc/motioneye is built as uid 100 before the Dockerfile
#      re-maps the motion user's uid/gid,
#   3. drop to the unprivileged `motion` user before exec'ing the
#      server.
#
# Privilege drop uses `setpriv` (util-linux). `su` is unavailable —
# the Dockerfile strips all SUID/SGID binaries as a hardening step.

set -e

MOTION_USER='motion'
MOTION_GROUP='motion'

# 1. Runtime directory (parent /run is root-owned, tmpfs on most hosts)
mkdir -p /run/motioneye

# 2. Make sure the motion user owns everything it needs to write.
#    Done every start so it survives volume re-mounts and image
#    rebuilds. chown is cheap on already-correct trees.
chown "${MOTION_USER}:${MOTION_GROUP}" \
    /run/motioneye \
    /etc/motioneye \
    /var/lib/motioneye \
    /var/log/motioneye
# Recurse into the config volume in case it was bind-mounted from a
# root-owned host directory.
chown -R "${MOTION_USER}:${MOTION_GROUP}" /etc/motioneye

# Seed the default config on first run.
[ -f '/etc/motioneye/motioneye.conf' ] \
    || cp -a /etc/motioneye.conf.sample /etc/motioneye/motioneye.conf

# 3. Drop privileges and start the server.
#    setpriv does not reset $HOME, so it would otherwise stay /root
#    (inherited from this root-run script) and the motion user could
#    not write ~/.motioneye_secret_key. Point HOME at the config
#    volume so the key persists and is owned by motion.
exec setpriv --reuid="${MOTION_USER}" --regid="${MOTION_GROUP}" --init-groups \
    env HOME=/etc/motioneye LANGUAGE=en \
    /usr/local/bin/meyectl startserver -c /etc/motioneye/motioneye.conf
