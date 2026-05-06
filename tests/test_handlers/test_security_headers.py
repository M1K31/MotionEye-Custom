"""Security headers (Q9): CSP, gated HSTS, dropped X-XSS-Protection.

Also covers the XSRF guard restoration (Q5) — see XsrfTest.
"""
import inspect
import unittest

from motioneye.handlers.base import BaseHandler, ManifestHandler
from tests.test_handlers import HandlerTestCase


class SecurityHeadersTest(HandlerTestCase):
    handler_cls = ManifestHandler

    def test_csp_header_set(self):
        response = self.fetch('/manifest.json')
        self.assertIn('Content-Security-Policy', response.headers)
        csp = response.headers['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)

    def test_referrer_policy_set(self):
        response = self.fetch('/manifest.json')
        self.assertEqual('no-referrer', response.headers.get('Referrer-Policy'))

    def test_x_xss_protection_removed(self):
        # Deprecated/harmful in modern browsers — must be gone.
        response = self.fetch('/manifest.json')
        self.assertNotIn('X-XSS-Protection', response.headers)

    def test_hsts_not_sent_on_http(self):
        # Over plain HTTP, HSTS is ignored anyway (RFC 6797) and gives
        # a false sense of security. The test fixture uses HTTP.
        response = self.fetch('/manifest.json')
        self.assertNotIn('Strict-Transport-Security', response.headers)


class XsrfGuardSourceTest(unittest.TestCase):
    """Source-level guard for Q5 — XSRF re-enabled for state-changing requests."""

    def test_check_xsrf_cookie_is_not_a_pass_stub(self):
        src = inspect.getsource(BaseHandler.check_xsrf_cookie)
        # The override must do something other than `pass` for browser
        # POST/PUT/DELETE — it must call super().check_xsrf_cookie().
        self.assertIn('super().check_xsrf_cookie()', src)

    def test_check_xsrf_cookie_bypasses_signature_auth(self):
        src = inspect.getsource(BaseHandler.check_xsrf_cookie)
        # Server-to-server signature auth must bypass the cookie check.
        self.assertIn("_signature", src)

    def test_check_xsrf_cookie_skips_safe_methods(self):
        src = inspect.getsource(BaseHandler.check_xsrf_cookie)
        # GET/HEAD/OPTIONS are XSRF-safe by HTTP spec.
        self.assertIn('GET', src)


if __name__ == '__main__':
    unittest.main()
