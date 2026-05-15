"""Tests for the persistent cookie secret store (Q10)."""
import os
import stat
import tempfile
import unittest

from motioneye import secrets_store


class SecretsStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, 'cookie.secret')

    def test_get_or_create_returns_64_hex_chars(self):
        secret = secrets_store.get_or_create_secret(self.path)
        self.assertEqual(len(secret), 64)
        int(secret, 16)  # raises if not hex

    def test_get_or_create_stable_across_calls(self):
        first = secrets_store.get_or_create_secret(self.path)
        second = secrets_store.get_or_create_secret(self.path)
        self.assertEqual(first, second, 'secret must persist across calls')

    def test_secret_file_has_owner_only_perms(self):
        secrets_store.get_or_create_secret(self.path)
        mode = stat.S_IMODE(os.stat(self.path).st_mode)
        self.assertEqual(mode, 0o600, 'cookie secret must be 0o600')

    def test_empty_file_regenerates(self):
        # Create empty file, then call should regenerate
        open(self.path, 'w').close()
        secret = secrets_store.get_or_create_secret(self.path)
        self.assertEqual(len(secret), 64)
        # And it should now persist
        self.assertEqual(secret, secrets_store.get_or_create_secret(self.path))


if __name__ == '__main__':
    unittest.main()
