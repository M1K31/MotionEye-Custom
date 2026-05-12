"""Tests for motioneye.platform_caps."""
import sys
import unittest
from unittest.mock import patch

from motioneye import platform_caps


class PlatformCapsTest(unittest.TestCase):
    def setUp(self):
        platform_caps.invalidate()

    def tearDown(self):
        platform_caps.invalidate()

    def test_returns_required_keys(self):
        caps = platform_caps.detect()
        for k in (
            'has_motion', 'has_v4l2', 'has_avfoundation',
            'has_mmal', 'has_netcam',
            'is_linux', 'is_macos', 'is_raspberry_pi',
        ):
            self.assertIn(k, caps, f'missing capability key: {k}')

    def test_macos_flags(self):
        with patch.object(sys, 'platform', 'darwin'), \
             patch('motioneye.motionctl.find_motion', return_value=(None, None)):
            caps = platform_caps.detect(force_refresh=True)
        self.assertTrue(caps['is_macos'])
        self.assertFalse(caps['is_linux'])
        self.assertFalse(caps['is_raspberry_pi'])
        self.assertTrue(caps['has_avfoundation'])
        self.assertFalse(caps['has_v4l2'])    # no /dev/video* on macOS
        self.assertFalse(caps['has_mmal'])    # not a Pi

    def test_linux_non_pi(self):
        with patch.object(sys, 'platform', 'linux'), \
             patch('motioneye.motionctl.find_motion', return_value=('/usr/bin/motion', '4.6')), \
             patch('motioneye.platform_caps._detect_raspberry_pi', return_value=False):
            caps = platform_caps.detect(force_refresh=True)
        self.assertTrue(caps['is_linux'])
        self.assertFalse(caps['is_macos'])
        self.assertFalse(caps['is_raspberry_pi'])
        self.assertTrue(caps['has_v4l2'])
        self.assertFalse(caps['has_mmal'])
        self.assertFalse(caps['has_avfoundation'])

    def test_raspberry_pi(self):
        with patch.object(sys, 'platform', 'linux'), \
             patch('motioneye.motionctl.find_motion', return_value=('/usr/bin/motion', '4.6')), \
             patch('motioneye.platform_caps._detect_raspberry_pi', return_value=True):
            caps = platform_caps.detect(force_refresh=True)
        self.assertTrue(caps['is_raspberry_pi'])
        self.assertTrue(caps['has_v4l2'])     # Pi supports V4L2 too
        self.assertTrue(caps['has_mmal'])     # And MMAL

    def test_no_motion_clears_netcam(self):
        # netcam is gated on Motion (it does the detection pipeline)
        with patch.object(sys, 'platform', 'linux'), \
             patch('motioneye.motionctl.find_motion', return_value=(None, None)), \
             patch('motioneye.platform_caps._detect_raspberry_pi', return_value=False):
            caps = platform_caps.detect(force_refresh=True)
        self.assertFalse(caps['has_motion'])
        self.assertFalse(caps['has_netcam'])
        # has_v4l2 reflects platform capability, not Motion presence
        self.assertTrue(caps['has_v4l2'])

    def test_detect_raspberry_pi_missing_file(self):
        # /proc/device-tree/model is absent on macOS — must not raise
        with patch('builtins.open', side_effect=FileNotFoundError()):
            self.assertFalse(platform_caps._detect_raspberry_pi())

    def test_cache_is_used(self):
        # Second call without force_refresh returns the cached dict
        first = platform_caps.detect()
        second = platform_caps.detect()
        self.assertIs(first, second)


if __name__ == '__main__':
    unittest.main()
