"""Single source of truth for what camera backends the host can drive.

Used by `handlers.main.MainHandler` to populate the template context
that gates camera-type options in the Add Camera dialog. Backend
modules (`v4l2ctl`, `macoscamctl`, `mmalctl`) still self-filter — this
module is only about *what UI options to show*, not *what devices
exist*.

Returned shape:
    {
        'is_linux': bool,
        'is_macos': bool,
        'is_raspberry_pi': bool,
        'has_v4l2': bool,         # any Linux: V4L2 API
        'has_mmal': bool,         # Raspberry Pi only: legacy MMAL stack
        'has_avfoundation': bool, # macOS only: AVFoundation via ffmpeg
        'has_motion': bool,       # `which motion` succeeds
        'has_netcam': bool,       # alias of has_motion (netcam needs Motion)
    }
"""
import sys

_cache = None


def _detect_raspberry_pi() -> bool:
    """Return True iff the host is a Raspberry Pi.

    Reads /proc/device-tree/model, which is world-readable on Pi OS
    and contains a string like "Raspberry Pi 4 Model B Rev 1.4". Any
    failure (file missing, permission denied) → False.
    """
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return 'raspberry pi' in f.read().lower()
    except (FileNotFoundError, PermissionError, OSError):
        return False


def detect(force_refresh: bool = False) -> dict:
    """Return the capability dict, lazily detecting on first call."""
    global _cache
    if _cache is not None and not force_refresh:
        return _cache

    # Import here so tests can mock motionctl without circular imports
    from motioneye import motionctl

    is_linux = sys.platform.startswith('linux')
    is_macos = sys.platform == 'darwin'
    is_pi = is_linux and _detect_raspberry_pi()
    has_motion = bool(motionctl.find_motion()[0])

    _cache = {
        'is_linux': is_linux,
        'is_macos': is_macos,
        'is_raspberry_pi': is_pi,
        # Local camera backends
        'has_v4l2': is_linux,
        'has_mmal': is_pi,
        'has_avfoundation': is_macos,
        # Motion daemon — required to drive local V4L2/MMAL capture
        # AND to run motion-detection on netcam (RTSP/HTTP) streams.
        'has_motion': has_motion,
        'has_netcam': has_motion,
    }
    return _cache


def invalidate() -> None:
    """Clear the cache. Used by tests and after installing Motion."""
    global _cache
    _cache = None
