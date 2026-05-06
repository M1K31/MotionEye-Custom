"""Source-level guards for the TLS verification hardening (C4)."""
import inspect
import unittest

from motioneye import utils


class TlsVerificationTest(unittest.TestCase):
    def test_no_cert_none_in_module(self):
        """ssl.CERT_NONE bypass must be removed (C4)."""
        src = inspect.getsource(utils)
        self.assertNotIn(
            'CERT_NONE',
            src,
            'ssl.CERT_NONE bypass must be removed (C4)',
        )

    def test_no_check_hostname_false(self):
        """check_hostname must never be set to False."""
        src = inspect.getsource(utils)
        compact = ''.join(src.split())
        self.assertNotIn(
            'check_hostname=False',
            compact,
            'check_hostname=False bypass must be removed (C4)',
        )

    def test_validate_certs_setting_removed(self):
        """The VALIDATE_CERTS setting was a footgun; it must be gone."""
        from motioneye import settings
        self.assertFalse(
            hasattr(settings, 'VALIDATE_CERTS'),
            'VALIDATE_CERTS setting was removed; use CA_BUNDLE_PATH for custom CAs',
        )


if __name__ == '__main__':
    unittest.main()
