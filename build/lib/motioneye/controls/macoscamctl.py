# Copyright (c) 2024 Jules
# This file is part of motionEye.
#
# This module provides camera control functionality for macOS using ffmpeg.
# It is intended as a replacement for v4l2ctl.py on non-Linux platforms.

import logging
import re
import subprocess
import time

from motioneye import utils
from motioneye import motionctl

_resolutions_cache = {}
_devices_cache = None


def find_ffmpeg():
    """Check if ffmpeg is available on the system."""
    try:
        return utils.call_subprocess(['which', 'ffmpeg'])
    except subprocess.CalledProcessError:
        return None


def list_devices():
    """List available video devices using ffmpeg."""
    global _devices_cache
    if _devices_cache is not None:
        return _devices_cache

    logging.debug('listing AVFoundation devices using ffmpeg')
    output = b''
    devices = []

    if not find_ffmpeg():
        logging.warning('ffmpeg not found, cannot list macOS devices.')
        _devices_cache = []
        return _devices_cache

    try:
        # On macOS, ffmpeg uses avfoundation to list devices.
        cmd = ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""']
        output = utils.call_subprocess(cmd, stderr=subprocess.STDOUT)
    except Exception as e:
        logging.error(f'ffmpeg error while listing devices: {e}')
        _devices_cache = []
        return _devices_cache

    output = utils.make_str(output)
    name = None
    # We are looking for lines like:
    # [AVFoundation input device @ 0x7fb6b8d080c0] [0] FaceTime HD Camera
    for line in output.split('\n'):
        match = re.search(r'\[AVFoundation input device.*\] \[(\d+)\] (.*)', line)
        if match:
            device_index = match.group(1)
            device_name = match.group(2).strip()

            if 'Capture screen' in device_name:
                continue

            device_path = device_index
            persistent_device = device_path

            devices.append((device_path, persistent_device, device_name))
            logging.debug(f'found device "{device_name}": path {device_path}')

    _devices_cache = devices
    return devices


def list_resolutions(device):
    """
    List supported resolutions for a device by probing with ffmpeg.
    """
    device_str = utils.make_str(device)
    if device_str in _resolutions_cache:
        return _resolutions_cache[device_str]

    logging.debug(f'Probing resolutions of device "{device_str}" with ffmpeg...')

    if not find_ffmpeg():
        logging.warning('ffmpeg not found, cannot probe resolutions.')
        return []

    resolutions = set()
    output = b''

    try:
        # This ffmpeg command probes the device and prints its capabilities to stderr.
        # We capture stderr and parse it for resolution information.
        cmd = ['ffmpeg', '-f', 'avfoundation', '-i', device_str, '-f', 'null', '-']
        # The probe can take a moment, so we give it a timeout.
        output = utils.call_subprocess(cmd, stderr=subprocess.STDOUT, timeout=5)
    except subprocess.TimeoutExpired as e:
        # Timeout is expected as the command runs indefinitely until killed.
        # The useful output is what it prints to stderr before the timeout.
        output = e.output or b''
    except Exception as e:
        logging.error(f'ffmpeg error while probing device "{device_str}": {e}')
        output = getattr(e, 'output', b'') # Try to get output even on error

    output = utils.make_str(output)
    # Look for lines like:
    # Stream #0:0: Video: rawvideo (uyvy422 / 0x32325955), uyvy422, 1280x720, 30 fps
    # We use a regex to find all "widthxheight" patterns in the output.
    for match in re.finditer(r'(\d{3,})x(\d{3,})', output):
        width = int(match.group(1))
        height = int(match.group(2))

        if (width, height) in resolutions:
            continue

        if not motionctl.resolution_is_valid(width, height):
            continue

        resolutions.add((width, height))
        logging.debug(f'found resolution {width}x{height} for device {device_str}')

    if not resolutions:
        logging.warning(f'no resolutions found for device {device_str}, falling back to common values')
        resolutions = [r for r in utils.COMMON_RESOLUTIONS if motionctl.resolution_is_valid(*r)]

    sorted_resolutions = list(sorted(resolutions, key=lambda r: (r[0], r[1])))
    _resolutions_cache[device_str] = sorted_resolutions

    return sorted_resolutions


def list_ctrls(device):
    """
    List camera controls. Not supported on macOS via ffmpeg.
    """
    logging.debug('listing controls for macOS device (not supported, returning empty list)')
    return {}


def find_v4l2_ctl():
    """
    This is a compatibility function. v4l2-ctl does not exist on macOS.
    """
    return None
