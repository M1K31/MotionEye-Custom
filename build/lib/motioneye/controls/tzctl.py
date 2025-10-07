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

import hashlib
import logging
import os

from motioneye import settings, utils
from motioneye.config import additional_config

LOCAL_TIME_FILE = settings.LOCAL_TIME_FILE  # @UndefinedVariable


def get_time_zone():
    return _get_time_zone_symlink() or _get_time_zone_md5() or 'UTC'


def _get_time_zone_symlink():
    f = settings.LOCAL_TIME_FILE
    if not f:
        return None

    for i in range(8):  # recursively follow the symlinks @UnusedVariable
        try:
            f = os.readlink(f)

        except OSError:
            break

    if f and f.startswith('/usr/share/zoneinfo/'):
        f = f[20:]

    else:
        f = None

    time_zone = f or None
    if time_zone:
        logging.debug('found time zone by symlink method: %s' % time_zone)

    return time_zone


def _get_time_zone_md5():
    if settings.LOCAL_TIME_FILE:
        return None

    time_zone_by_md5 = {}
    zoneinfo_dir = '/usr/share/zoneinfo'

    try:
        for root, _, files in os.walk(zoneinfo_dir):
            for name in files:
                path = os.path.join(root, name)
                if not os.path.isfile(path) or os.path.islink(path):
                    continue
                try:
                    with open(path, 'rb') as f:
                        data = f.read()
                    md5 = hashlib.md5(data).hexdigest()
                    rel_path = os.path.relpath(path, zoneinfo_dir)
                    time_zone_by_md5[md5] = rel_path
                except Exception:
                    continue  # Ignore files that can't be read
    except Exception as e:
        logging.error('getting md5 of zoneinfo files failed: %s' % e)
        return None

    try:
        with open(settings.LOCAL_TIME_FILE, 'rb') as f:
            data = f.read()

    except Exception as e:
        logging.error('failed to read local time file: %s' % e)

        return None

    md5 = hashlib.md5(data).hexdigest()
    time_zone = time_zone_by_md5.get(md5)

    if time_zone:
        logging.debug('found time zone by md5 method: %s' % time_zone)

    return time_zone


def _set_time_zone(time_zone):
    time_zone = time_zone or 'UTC'

    zoneinfo_file = '/usr/share/zoneinfo/' + time_zone
    if not os.path.exists(zoneinfo_file):
        logging.error('%s file does not exist' % zoneinfo_file)

        return False

    logging.debug(f'linking "{settings.LOCAL_TIME_FILE}" to "{zoneinfo_file}"')

    try:
        os.remove(settings.LOCAL_TIME_FILE)

    except:
        pass  # nevermind

    try:
        os.symlink(zoneinfo_file, settings.LOCAL_TIME_FILE)

        return True

    except Exception as e:
        logging.error(
            f'failed to link "{settings.LOCAL_TIME_FILE}" to "{zoneinfo_file}": {e}'
        )

        return False


@additional_config
def timeZone():
    if not LOCAL_TIME_FILE:
        return

    import pytz

    timezones = pytz.common_timezones

    return {
        'label': 'Time Zone',
        'description': 'selecting the right timezone assures a correct timestamp displayed on pictures and movies',
        'type': 'choices',
        'choices': [(t, t) for t in timezones],
        'section': 'general',
        'reboot': True,
        'get': get_time_zone,
        'set': _set_time_zone,
    }
