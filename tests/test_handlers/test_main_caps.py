"""Tests for camera capability rendering in the main template."""
import sys
import unittest
from unittest.mock import patch

from motioneye import platform_caps
from motioneye.handlers.main import MainHandler
from tests.test_handlers import HandlerTestCase


def _caps(**overrides):
    base = {
        'is_linux': False, 'is_macos': False, 'is_raspberry_pi': False,
        'has_v4l2': False, 'has_mmal': False, 'has_avfoundation': False,
        'has_motion': False, 'has_netcam': False,
    }
    base.update(overrides)
    return base


class MainCapsRenderingTest(HandlerTestCase):
    handler_cls = MainHandler

    def setUp(self):
        super().setUp()
        platform_caps.invalidate()

    def tearDown(self):
        platform_caps.invalidate()
        super().tearDown()

    def test_macos_with_motion_renders_avfoundation_only(self):
        fake = _caps(is_macos=True, has_avfoundation=True,
                     has_motion=True, has_netcam=True)
        with patch('motioneye.platform_caps.detect', return_value=fake):
            response = self.fetch('/')
        self.assertEqual(200, response.code)
        body = response.body.decode()
        # AVFoundation flag true, V4L2/MMAL false
        self.assertIn('avfoundation: true', body)
        self.assertIn('v4l2:         false', body)
        self.assertIn('mmal:         false', body)
        self.assertIn('netcam:       true', body)

    def test_linux_non_pi_with_motion_renders_v4l2_not_mmal(self):
        fake = _caps(is_linux=True, has_v4l2=True,
                     has_motion=True, has_netcam=True)
        with patch('motioneye.platform_caps.detect', return_value=fake):
            response = self.fetch('/')
        body = response.body.decode()
        self.assertIn('v4l2:         true', body)
        self.assertIn('mmal:         false', body)
        self.assertIn('avfoundation: false', body)

    def test_pi_renders_both_v4l2_and_mmal(self):
        fake = _caps(is_linux=True, is_raspberry_pi=True,
                     has_v4l2=True, has_mmal=True,
                     has_motion=True, has_netcam=True)
        with patch('motioneye.platform_caps.detect', return_value=fake):
            response = self.fetch('/')
        body = response.body.decode()
        self.assertIn('v4l2:         true', body)
        self.assertIn('mmal:         true', body)

    def test_no_motion_hides_local_and_netcam(self):
        # V4L2 platform capability is true but Motion is absent —
        # local + netcam options should both be hidden.
        fake = _caps(is_linux=True, has_v4l2=True,
                     has_motion=False, has_netcam=False)
        with patch('motioneye.platform_caps.detect', return_value=fake):
            response = self.fetch('/')
        body = response.body.decode()
        self.assertIn('v4l2:         false', body)  # gated on AND has_motion
        self.assertIn('netcam:       false', body)


if __name__ == '__main__':
    unittest.main()
