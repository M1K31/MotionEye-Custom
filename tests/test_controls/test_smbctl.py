"""Tests for SMB credential handling (Q11)."""
import inspect
import os
import stat
import unittest

from motioneye.controls import smbctl


class SmbctlSecurityTest(unittest.TestCase):
    def test_password_not_passed_via_cli_options(self):
        """SMB password must not appear in mount.cifs -o options string (Q11)."""
        src = inspect.getsource(smbctl)
        compact = ''.join(src.split())
        self.assertNotIn(
            "',password='",
            compact,
            'mount.cifs password=... in -o options leaks via /proc/<pid>/cmdline',
        )
        self.assertNotIn(
            'f"username={username},password={password}"',
            src,
            'mount.cifs password=... in -o options leaks via /proc/<pid>/cmdline',
        )
        self.assertIn(
            'credentials=',
            src,
            'use credentials file for mount.cifs',
        )

    def test_credentials_file_helper_uses_0600(self):
        """The credentials file helper must chmod 0o600 before returning."""
        username = 'alice'
        password = 'p@ssw0rd'
        path = smbctl._write_credentials_file(username, password)
        try:
            mode = stat.S_IMODE(os.stat(path).st_mode)
            self.assertEqual(mode, 0o600, 'credentials file must be 0o600')
            with open(path, 'r') as f:
                content = f.read()
            self.assertIn(f'username={username}', content)
            self.assertIn(f'password={password}', content)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
