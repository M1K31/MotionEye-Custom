"""Source-level guard for the daemon umask hardening (Q6)."""
import inspect
import unittest

from motioneye.server import Daemon


class DaemonUmaskTest(unittest.TestCase):
    def test_daemonize_does_not_use_world_writable_umask(self):
        """umask(0) creates world-writable files (Q6)."""
        src = inspect.getsource(Daemon.daemonize)
        self.assertNotIn(
            'os.umask(0)',
            src,
            'umask(0) creates world-readable+writable daemon files (Q6)',
        )
        self.assertIn(
            'umask(0o027)',
            src.replace(' ', ''),
            'expected restrictive umask 0o027',
        )


if __name__ == '__main__':
    unittest.main()
