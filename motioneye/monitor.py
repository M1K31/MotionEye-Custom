# Copyright (c) 2013 Calin Crisan
# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import sys
from threading import Thread

from motioneye import config

DEFAULT_INTERVAL = 1  # seconds

_monitor_info_cache_by_camera_id = {}
_last_call_time_by_camera_id = {}
_interval_by_camera_id = {}


class MotionDaemonMonitor:
    """Monitor and auto-restart Motion daemon on crashes"""

    def __init__(self, check_interval=10, max_restarts=5):
        self.check_interval = check_interval
        self.max_restarts = max_restarts
        self.restart_count = 0
        self.last_restart = 0
        self.monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start daemon monitoring"""
        self.monitoring = True
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logging.info("Motion daemon monitoring started")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Check if motion process is running
                result = subprocess.run(
                    ['pgrep', '-x', 'motion'],
                    capture_output=True
                )

                if result.returncode != 0:  # Motion not running
                    logging.error("Motion daemon not running!")
                    self._attempt_restart()

                # Reset restart count after 5 minutes of stability
                if time.time() - self.last_restart > 300:
                    self.restart_count = 0

                time.sleep(self.check_interval)

            except Exception as e:
                logging.error(f"Monitor error: {e}")
                time.sleep(5)

    def _attempt_restart(self):
        """Attempt to restart Motion daemon"""
        if self.restart_count >= self.max_restarts:
            logging.critical("Max restart attempts reached. Manual intervention required.")
            # Send alert to admin
            return

        try:
            logging.info(f"Attempting to restart Motion (attempt {self.restart_count + 1})")
            if sys.platform.startswith('linux'):
                subprocess.run(['systemctl', 'restart', 'motion'], check=True)
            elif sys.platform == 'darwin':
                # Assumes motion is managed by launchd on macOS.
                # The service name might need to be adjusted.
                subprocess.run(['launchctl', 'kickstart', '-k', 'system/org.motion.motiond'], check=True)
            else:
                logging.warning(f"Automatic restart not supported on this platform: {sys.platform}")
                return

            self.restart_count += 1
            self.last_restart = time.time()
            logging.info("Motion daemon restarted successfully")

        except Exception as e:
            logging.error(f"Failed to restart Motion: {e}")


def get_monitor_info(camera_id):
    now = time.time()
    command = config.get_monitor_command(camera_id)
    if command is None:
        return ''

    monitor_info = _monitor_info_cache_by_camera_id.get(camera_id)
    last_call_time = _last_call_time_by_camera_id.get(camera_id, 0)
    interval = _interval_by_camera_id.get(camera_id, DEFAULT_INTERVAL)
    if monitor_info is None or now - last_call_time > interval:
        monitor_info, interval = _exec_monitor_command(command)
        monitor_info = urllib.parse.quote(monitor_info, safe='')
        _interval_by_camera_id[camera_id] = interval
        _monitor_info_cache_by_camera_id[camera_id] = monitor_info
        _last_call_time_by_camera_id[camera_id] = now

    return monitor_info


def _exec_monitor_command(command):
    process = subprocess.Popen(
        [command], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = process.communicate()

    try:
        interval = int(err)

    except (ValueError, TypeError):
        interval = DEFAULT_INTERVAL

    out = out.strip()
    logging.debug(f'monitoring command "{command}" returned "{out}"')

    return out, interval