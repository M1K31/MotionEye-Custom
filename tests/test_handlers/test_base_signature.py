"""Source-level guards for the timing-attack hardening in BaseHandler (C2)."""
import inspect
import unittest

from motioneye.handlers import base


class SignatureComparisonTest(unittest.TestCase):
    def test_get_current_user_uses_compare_digest(self):
        """BaseHandler.get_current_user must use hmac.compare_digest
        for signature comparison to prevent byte-level timing attacks."""
        src = inspect.getsource(base.BaseHandler.get_current_user)
        self.assertIn(
            'compare_digest',
            src,
            'signature comparison must use hmac.compare_digest (C2)',
        )

    def test_no_naive_signature_equality_in_get_current_user(self):
        """The naive `signature == utils.compute_signature(...)` pattern must be gone."""
        src = inspect.getsource(base.BaseHandler.get_current_user)
        compact = ''.join(src.split())
        self.assertNotIn(
            'signature==utils.compute_signature',
            compact,
            'direct == comparison of signatures is timing-vulnerable (C2)',
        )


if __name__ == '__main__':
    unittest.main()
