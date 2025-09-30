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

import fcntl
import logging
import os.path
import re
import stat
import subprocess
import time

# Secure utility functions integrated directly
def make_str(s):
    """Convert bytes to string safely"""
    if isinstance(s, bytes):
        return s.decode('utf-8', errors='ignore')
    return str(s) if s is not None else ''

def execute_secure_command(cmd_args, timeout=30, cwd=None):
    """Securely execute command without shell injection vulnerabilities"""
    if not isinstance(cmd_args, list):
        raise ValueError("Command arguments must be provided as a list")

    if not cmd_args:
        raise ValueError("Command arguments list cannot be empty")

    # Validate arguments for dangerous characters
    dangerous_chars = ['|', '&', ';', '(', ')', '$', '`', '\\', '"', "'", '<', '>', '\n', '\r']
    for i, arg in enumerate(cmd_args):
        arg_str = str(arg)
        for char in dangerous_chars:
            if char in arg_str:
                logging.warning(f"Potentially unsafe character '{char}' in command argument {i}: {arg_str}")

    try:
        result = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
            text=True,
            check=False
        )

        logging.debug(f'Command executed: {" ".join(cmd_args)}, return code: {result.returncode}')
        return result

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out after {timeout} seconds: {' '.join(cmd_args)}")
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {cmd_args[0]}")
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {e}")

# Common resolutions for fallback
COMMON_RESOLUTIONS = [
    (320, 240), (640, 480), (800, 600), (1024, 768),
    (1280, 720), (1280, 1024), (1600, 1200), (1920, 1080)
]

_resolutions_cache = {}
_ctrls_cache = {}
_ctrl_values_cache = {}

_DEV_V4L_BY_ID = '/dev/v4l/by-id/'
_V4L2_TIMEOUT = 10

def validate_device_path(device):
    """Validate and sanitize device path input to prevent injection attacks"""
    if not device:
        raise ValueError("Device path cannot be empty")

    device = make_str(device)

    # Allow only valid device paths
    valid_patterns = [
        r'^/dev/video\d+$',  # Standard video devices
        r'^/dev/v4l/by-id/[a-zA-Z0-9_.-]+$',  # Persistent device paths
        r'^/dev/v4l/by-path/[a-zA-Z0-9_:.-]+$'  # Path-based persistent devices
    ]

    if not any(re.match(pattern, device) for pattern in valid_patterns):
        raise ValueError(f"Invalid device path format: {device}")

    # Verify device exists and is a character device
    if os.path.exists(device):
        try:
            st = os.stat(device)
            if not stat.S_ISCHR(st.st_mode):
                raise ValueError(f"Device {device} is not a character device")
        except OSError as e:
            raise ValueError(f"Cannot access device {device}: {e}")

    return device

def find_v4l2_ctl():
    try:
        result = execute_secure_command(['which', 'v4l2-ctl'], timeout=5)
        return result.stdout.strip()
    except Exception:
        return None

def list_devices():
    global _resolutions_cache, _ctrls_cache, _ctrl_values_cache

    logging.debug('listing V4L2 devices')

    try:
        result = execute_secure_command(['v4l2-ctl', '--list-devices'], timeout=_V4L2_TIMEOUT)
        output = result.stdout
    except Exception as e:
        logging.error(f'v4l2-ctl error: {e}')
        return []

    name = None
    devices = []

    for line in output.split('\n'):
        if line.startswith('\t'):
            device = line.strip()
            try:
                validated_device = validate_device_path(device)
                persistent_device = find_persistent_device(validated_device)
                devices.append((validated_device, persistent_device, name))
                logging.debug(f'found device {name}: {validated_device}, {persistent_device}')
            except ValueError as e:
                logging.warning(f'Skipping invalid device {device}: {e}')
                continue
        else:
            name = line.split('(')[0].strip()

    # Clear the cache
    _resolutions_cache = {}
    _ctrls_cache = {}
    _ctrl_values_cache = {}

    return devices

def list_resolutions(device):
    try:
        from motioneye import motionctl
    except ImportError:
        motionctl = None

    device = make_str(device)

    if device in _resolutions_cache:
        return _resolutions_cache[device]

    logging.debug(f'listing resolutions of device {device}...')

    # Validate device path
    try:
        validated_device = validate_device_path(device)
    except ValueError as e:
        logging.error(f"Device validation failed: {e}")
        return []

    resolutions = set()

    try:
        # Secure command execution
        cmd_args = ["v4l2-ctl", "-d", validated_device, "--list-formats-ext"]
        result = execute_secure_command(cmd_args, timeout=_V4L2_TIMEOUT)
        output = result.stdout
    except Exception as e:
        logging.error(f'failed to list resolutions of device "{device}": {e}')
        output = ""

    # Process output to find resolutions
    resolution_pattern = re.compile(r'([0-9]+x[0-9]+)')
    for line in output.split('\n'):
        if 'stepwise' in line.lower():
            continue

        matches = resolution_pattern.findall(line)
        for pair in matches:
            pair = pair.strip()
            if not pair:
                continue

            try:
                width, height = pair.split('x')
                width = int(width)
                height = int(height)

                if (width, height) in resolutions:
                    continue

                if width < 96 or height < 96:
                    continue

                if motionctl and hasattr(motionctl, 'resolution_is_valid'):
                    if not motionctl.resolution_is_valid(width, height):
                        continue

                resolutions.add((width, height))
                logging.debug(f'found resolution {width}x{height} for device {device}')

            except (ValueError, AttributeError) as e:
                logging.warning(f'Invalid resolution format "{pair}": {e}')
                continue

    if not resolutions:
        logging.debug(f'no resolutions found for device {device}, using common values')
        resolutions = COMMON_RESOLUTIONS
        if motionctl and hasattr(motionctl, 'resolution_is_valid'):
            resolutions = [r for r in resolutions if motionctl.resolution_is_valid(*r)]

    resolutions = list(sorted(resolutions, key=lambda r: (r[0], r[1])))
    _resolutions_cache[device] = resolutions

    return resolutions

def device_present(device):
    device = make_str(device)
    try:
        st = os.stat(device)
        return stat.S_ISCHR(st.st_mode)
    except:
        return False

def find_persistent_device(device):
    device = make_str(device)
    try:
        devs_by_id = os.listdir(_DEV_V4L_BY_ID)
    except OSError:
        return device

    for p in devs_by_id:
        p = os.path.join(_DEV_V4L_BY_ID, p)
        if os.path.realpath(p) == device:
            return p

    return device

def list_ctrls(device):
    device = make_str(device)

    if device in _ctrls_cache:
        return _ctrls_cache[device]

    # Validate device path
    try:
        validated_device = validate_device_path(device)
    except ValueError as e:
        logging.error(f"Invalid device path: {e}")
        return {}

    cmd_args = ['v4l2-ctl', '-d', validated_device, '--list-ctrls']
    logging.debug(f'running command "{" ".join(cmd_args)}"')

    try:
        result = execute_secure_command(cmd_args, timeout=_V4L2_TIMEOUT)
        output = result.stdout
    except Exception as e:
        logging.error(f'failed to list controls of device "{validated_device}": {e}')
        return {}

    controls = {}

    for line in output.split('\n'):
        if not line:
            continue

        match = re.match(r'^\s*(\w+)\s+([a-f0-9x\s]+)?\(\w+\)\s*:\s*(.+)\s*', line)
        if not match:
            continue

        (control, _, properties) = match.groups()
        try:
            properties = dict(
                [v.split('=', 1) for v in properties.split(' ') if v.count('=')]
            )
            controls[control] = properties
        except (ValueError, AttributeError) as e:
            logging.warning(f'Invalid control properties "{properties}": {e}')
            continue

    _ctrls_cache[device] = controls
    return controls