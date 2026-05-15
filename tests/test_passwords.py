import unittest
from motioneye import passwords


class PasswordsTest(unittest.TestCase):
    def test_hash_password_returns_bcrypt_string(self):
        h = passwords.hash_password('secret')
        self.assertTrue(h.startswith('$2b$') or h.startswith('$2a$'))

    def test_verify_correct_password(self):
        h = passwords.hash_password('secret')
        self.assertTrue(passwords.verify_password('secret', h))

    def test_verify_wrong_password(self):
        h = passwords.hash_password('secret')
        self.assertFalse(passwords.verify_password('wrong', h))

    def test_legacy_sha1_hash_is_recognized(self):
        legacy = 'e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4'
        self.assertTrue(passwords.is_legacy_hash(legacy))
        self.assertFalse(passwords.is_legacy_hash(passwords.hash_password('x')))

    def test_verify_legacy_sha1_password(self):
        legacy = 'e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4'
        self.assertTrue(passwords.verify_password('secret', legacy))
        self.assertFalse(passwords.verify_password('wrong', legacy))

    def test_empty_password_handling(self):
        self.assertTrue(passwords.verify_password('', ''))
        self.assertFalse(passwords.verify_password('anything', ''))

    def test_compute_sig_key_is_sha1(self):
        import hashlib
        self.assertEqual(
            passwords.compute_sig_key('secret'),
            hashlib.sha1(b'secret').hexdigest()
        )

    def test_compute_sig_key_empty(self):
        self.assertEqual(passwords.compute_sig_key(''), '')

    def test_verify_malformed_stored_hash(self):
        # bcrypt.checkpw raises on malformed input; verify_password must swallow
        # the exception and return False (no traceback leakage to callers).
        self.assertFalse(passwords.verify_password('anything', 'garbage'))
        self.assertFalse(passwords.verify_password('x', '$2b$invalid'))
        self.assertFalse(passwords.verify_password('x', '$2b$12$short'))

    def test_basic_auth_does_not_accept_bcrypt_hash_as_password(self):
        # Q8 regression: previously the basic-auth check accepted EITHER the
        # raw password OR its stored hash. Now we must reject the stored
        # hash being submitted as a password.
        h = passwords.hash_password('secret')
        self.assertFalse(passwords.verify_password(h, h),
                         'bcrypt hash submitted as password must not authenticate')

    def test_basic_auth_does_not_accept_legacy_sha1_hash_as_password(self):
        # Same Q8 regression for legacy SHA-1 stored hashes.
        legacy = 'e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4'  # sha1('secret')
        self.assertFalse(passwords.verify_password(legacy, legacy),
                         'SHA-1 hash submitted as password must not authenticate')
