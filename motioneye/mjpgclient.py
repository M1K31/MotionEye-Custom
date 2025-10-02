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

import datetime
import errno
import logging
import re
import socket
import time
from typing import Any, Tuple

from tornado.concurrent import Future
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream

from motioneye import config, motionctl, settings, utils

# Global state for managing connection retries
_retry_state = {}


class MjpgClient(IOStream):
    """
    An asynchronous MJPEG client with robust connection handling.
    This client reads a continuous MJPEG stream from a motion camera,
    handles authentication, and implements an exponential backoff retry
    mechanism for connection errors.
    """
    _FPS_LEN = 10

    clients = {}  # dictionary of clients indexed by camera id

    def __init__(self, camera_id, port, username, password, auth_mode,
                 retry_delay=2, max_retries=5):
        self._camera_id = camera_id
        self._port = port
        self._username = username or ''
        self._password = password or ''
        self._auth_mode = auth_mode
        self._auth_digest_state = {}

        # Parameters for robust connection handling
        self._retry_delay = retry_delay
        self._max_retries = max_retries

        self._last_access = 0
        self._last_jpg = None
        self._last_jpg_times = []

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        IOStream.__init__(self, s)

        self.set_close_callback(self.on_close)

    def do_connect(self) -> 'Future[MjpgClient]':
        """Initiates the connection to the MJPEG stream."""
        f = self.connect(('localhost', self._port))
        f.add_done_callback(self._on_connect)
        return f

    def get_port(self):
        return self._port

    def on_close(self):
        """
        Callback executed when the stream is closed. If the closure was
        due to an error, a reconnection attempt is scheduled.
        """
        logging.debug(
            f'connection closed for mjpg client for camera {self._camera_id} on port {self._port}'
        )

        MjpgClient.clients.pop(self._camera_id, None)

        if getattr(self, 'error', None):
            logging.warning(
                f"MJPEG client for camera {self._camera_id} on port {self._port} "
                f"closed with error: {self.error}. Scheduling reconnect."
            )
            _schedule_reconnect(self._camera_id, self._retry_delay, self._max_retries)
        else:
            logging.info(f"MJPEG client for camera {self._camera_id} closed gracefully.")

    def get_last_jpg(self):
        self._last_access = time.time()
        return self._last_jpg

    def get_last_access(self):
        return self._last_access

    def get_last_jpg_time(self):
        if not self._last_jpg_times:
            self._last_jpg_times.append(time.time())
        return self._last_jpg_times[-1]

    def get_fps(self):
        if len(self._last_jpg_times) < self._FPS_LEN:
            return 0
        if time.time() - self._last_jpg_times[-1] > 1:
            return 0
        return (len(self._last_jpg_times) - 1) / (
            self._last_jpg_times[-1] - self._last_jpg_times[0]
        )

    def _check_error(self) -> bool:
        if self.socket is None:
            logging.warning(f'mjpg client connection for camera {self._camera_id} is closed')
            self.close()
            return True
        error = getattr(self, 'error', None)
        if (error is None) or (getattr(error, 'errno', None) == 0):
            return False
        self._error(error)
        return True

    def _error(self, error) -> None:
        logging.error(
            f'mjpg client for camera {self._camera_id} on port {self._port} error: {str(error)}',
            exc_info=True,
        )
        try:
            self.close()
        except Exception:
            pass

    def _get_future_result(self, future: Future) -> Tuple[bool, Any]:
        try:
            if self.closed():
                future.cancel()
                return False, None
            return True, future.result()
        except Exception as e:
            self._error(e)
            return False, None

    def _on_connect(self, future: Future) -> None:
        """Callback executed on connection attempt completion."""
        result, _ = self._get_future_result(future)
        if not result:
            return

        logging.info(f'mjpg client for camera {self._camera_id} connected on port {self._port}')

        # On successful connect, reset the retry state for this camera
        if self._camera_id in _retry_state:
            logging.debug(f"Connection successful, resetting retry state for camera {self._camera_id}")
            del _retry_state[self._camera_id]

        auth_header = ''
        if self._auth_mode == 'basic':
            logging.debug('mjpg client using basic authentication')
            auth_header = f"Authorization: {utils.build_basic_header(self._username, self._password)}\r\n"
        elif self._auth_mode == 'digest':
            logging.debug('digest authentication _on_connect, waiting for 401')

        self.write(f'GET / HTTP/1.0\r\n{auth_header}Connection: close\r\n\r\n'.encode())
        self._seek_http()

    def _seek_http(self, future: Future = False) -> None:
        result, _ = self._get_future_result(future) if future else (True, False)
        if not result or self._check_error():
            return
        future = utils.cast_future(self.read_until_regex(br'HTTP/1.\d \d+ '))
        future.add_done_callback(self._on_http)

    def _on_http(self, future: Future) -> None:
        result, data = self._get_future_result(future)
        if not result:
            return
        if data.endswith(b'401 '):
            self._seek_www_authenticate()
        else:
            self._seek_content_length()

    def _seek_www_authenticate(self) -> None:
        future = utils.cast_future(self.read_until(b'WWW-Authenticate:'))
        future.add_done_callback(self._on_before_www_authenticate)

    def _on_before_www_authenticate(self, future: Future) -> None:
        result, _ = self._get_future_result(future)
        if not result or self._check_error():
            return
        r_future = utils.cast_future(self.read_until(b'\r\n'))
        r_future.add_done_callback(self._on_www_authenticate)

    def _on_www_authenticate(self, future: Future) -> None:
        result, data = self._get_future_result(future)
        if not result or self._check_error():
            return

        data = data.strip()
        auth_header = ''
        if data.startswith(b'Digest'):
            logging.debug('mjpg client using digest authentication')
            parts_dict = dict(p.split('=', 1) for p in data[7:].decode().split(','))
            parts_dict = {p[0]: p[1].strip('"') for p in list(parts_dict.items())}
            self._auth_digest_state = parts_dict
            auth_header = utils.build_digest_header('GET', '/', self._username, self._password, self._auth_digest_state)
        elif data.startswith(b'Basic'):
            logging.debug('mjpg client using basic authentication')
            auth_header = utils.build_basic_header(self._username, self._password)
        else:
            logging.error(f'mjpg client unknown authentication header: {data}')
            self._seek_content_length()
            return

        w_data = f'GET / HTTP/1.0\r\nAuthorization: {auth_header}\r\nConnection: close\r\n\r\n'.encode()
        w_future = utils.cast_future(self.write(w_data))
        w_future.add_done_callback(self._seek_http)

    def _seek_content_length(self):
        if self._check_error():
            return
        r_future = utils.cast_future(self.read_until(b'Content-Length:'))
        r_future.add_done_callback(self._on_before_content_length)

    def _on_before_content_length(self, future: Future):
        result, _ = self._get_future_result(future)
        if not result or self._check_error():
            return
        r_future = utils.cast_future(self.read_until(b'\r\n\r\n'))
        r_future.add_done_callback(self._on_content_length)

    def _on_content_length(self, future: Future):
        result, data = self._get_future_result(future)
        if not result or self._check_error():
            return
        matches = re.findall(rb'(\d+)', data)
        if not matches:
            self._error(f'could not find content length in mjpg header line "{data}"')
            return
        length = int(matches[0])
        r_future = utils.cast_future(self.read_bytes(length))
        r_future.add_done_callback(self._on_jpg)

    def _on_jpg(self, future: Future):
        """
        Callback executed when a full JPG frame is received.
        Any error during reading will cause the stream to close,
        triggering the on_close logic for reconnection. This functions
        as a safe frame reading mechanism.
        """
        result, data = self._get_future_result(future)
        if not result:
            return
        self._last_jpg = data
        self._last_jpg_times.append(time.time())
        while len(self._last_jpg_times) > self._FPS_LEN:
            self._last_jpg_times.pop(0)
        self._seek_content_length()


def _schedule_reconnect(camera_id, retry_delay, max_retries):
    """
    Manages the exponential backoff retry logic for a given camera.
    """
    state = _retry_state.get(camera_id, {'count': 0})
    retry_count = state['count']

    if retry_count >= max_retries:
        logging.critical(
            f"Max retries ({max_retries}) reached for camera {camera_id}. "
            "Manual intervention may be required."
        )
        if settings.MOTION_RESTART_ON_ERRORS:
            logging.error("Falling back to restarting motion service.")
            motionctl.stop(invalidate=True)
            motionctl.start(deferred=True)
        if camera_id in _retry_state:
            del _retry_state[camera_id]
        return

    retry_count += 1
    _retry_state[camera_id] = {'count': retry_count}
    wait_time = retry_delay * (2 ** (retry_count - 1))
    logging.warning(
        f"Connection for camera {camera_id} failed. Retrying in {wait_time}s "
        f"(attempt {retry_count}/{max_retries})."
    )

    def reconnect_callback():
        logging.info(f"Attempting to reconnect camera {camera_id} now.")
        get_jpg(camera_id)

    IOLoop.current().add_timeout(datetime.timedelta(seconds=wait_time), reconnect_callback)


def start():
    io_loop = IOLoop.current()
    io_loop.add_timeout(
        datetime.timedelta(seconds=settings.MJPG_CLIENT_TIMEOUT), _garbage_collector
    )


def get_jpg(camera_id):
    """
    Gets the latest JPG from a camera's MJPEG stream, creating a new
    client if one doesn't exist for the given camera_id.
    """
    if camera_id not in MjpgClient.clients:
        # If a reconnect is already scheduled, don't create a new client.
        if camera_id in _retry_state:
            logging.debug(f"Reconnect already scheduled for camera {camera_id}, skipping new client creation.")
            return None

        logging.debug(f'creating mjpg client for camera {camera_id}')
        camera_config = config.get_camera(camera_id)
        if not camera_config['@enabled'] or not utils.is_local_motion_camera(camera_config):
            logging.error(f'could not start mjpg client for camera id {camera_id}: not enabled or not local')
            return None

        port = camera_config['stream_port']
        username, password, auth_mode = None, None, None
        if camera_config.get('stream_auth_method') > 0:
            username, password = camera_config.get('stream_authentication', ':').split(':')
            auth_mode = 'digest' if camera_config.get('stream_auth_method') > 1 else 'basic'

        client = MjpgClient(camera_id, port, username, password, auth_mode)
        client.do_connect()
        MjpgClient.clients[camera_id] = client

    client = MjpgClient.clients.get(camera_id)
    return client.get_last_jpg() if client else None


def get_fps(camera_id):
    client = MjpgClient.clients.get(camera_id)
    return client.get_fps() if client else 0


def close_all(invalidate=False):
    for client in list(MjpgClient.clients.values()):
        client.close()
    if invalidate:
        MjpgClient.clients = {}
        _retry_state.clear()


def _garbage_collector():
    io_loop = IOLoop.current()
    io_loop.add_timeout(
        datetime.timedelta(seconds=settings.MJPG_CLIENT_TIMEOUT), _garbage_collector
    )

    now = time.time()
    for camera_id, client in list(MjpgClient.clients.items()):
        if client.closed():
            continue

        # check for jpeg frame timeout (stream is connected but no data arrives)
        if now - client.get_last_jpg_time() > settings.MJPG_CLIENT_TIMEOUT:
            logging.error(
                f'mjpg client timed out receiving data for camera {camera_id} on port {client.get_port()}'
            )
            client.close()  # This will trigger on_close and the reconnect logic
            break # Stop processing further clients this round

        # check for last access timeout (no component is asking for frames)
        if (settings.MJPG_CLIENT_IDLE_TIMEOUT and
                now - client.get_last_access() > settings.MJPG_CLIENT_IDLE_TIMEOUT):
            logging.debug(
                f'mjpg client for camera {camera_id} on port {client.get_port()} '
                f'has been idle for {settings.MJPG_CLIENT_IDLE_TIMEOUT} seconds, removing it'
            )
            client.close()
            continue