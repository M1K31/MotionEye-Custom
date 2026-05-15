# Copyright (c) 2020 Vlsarro
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

from motioneye.utils import GetCamerasResponse
from motioneye.utils.http import RtmpUrl

__all__ = ('check_rtmp_url',)


def check_rtmp_url(data: dict) -> GetCamerasResponse:
    """Stub camera discovery for RTMP/TCP URLs.

    NOTE: this function intentionally does not validate that the
    RTMP target is actually reachable. Implementing a proper
    SYN/ACK or RTMP-handshake probe is deferred until there is
    explicit demand — adding fake liveness here would mislead
    callers more than it would help.

    The `RtmpUrl.from_dict(data)` call still runs to surface
    malformed inputs (it raises on bad data), but its result is
    intentionally unused.
    """
    RtmpUrl.from_dict(data)  # validate shape, raises on bad input

    cameras = [{'id': 'tcp', 'name': 'RTMP/TCP Camera'}]
    return GetCamerasResponse(cameras, None)
