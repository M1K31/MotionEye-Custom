# Copyright (c) 2020 Vlsarro
# Copyright (c) 2013 Calin Crisan
# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import hmac
import json
import logging
import weakref

from tornado.web import HTTPError, RequestHandler

from motioneye import VERSION, config, passwords, prefs, settings, template, utils

__all__ = ('BaseHandler', 'NotFoundHandler', 'ManifestHandler')


class BaseHandler(RequestHandler):
    _active_handlers = weakref.WeakSet()
    # Operability flags: emit a single warning per process when an
    # @*_password is set but its corresponding sig_key is missing.
    _warned_admin_sig_key_missing = False
    _warned_normal_sig_key_missing = False

    def on_finish(self):
        """Cleanup after request completes."""
        super().on_finish()
        self._cleanup()

    def on_connection_close(self):
        """Cleanup when connection closes."""
        super().on_connection_close()
        self._cleanup()

    def _cleanup(self):
        """Drop large per-request buffers to help GC.

        Q2: removed the previous `gc.collect()` call that fired on every
        request when >50 handlers were active — that synchronously
        stalled the Tornado event loop. Python's generational GC
        handles this automatically; the periodic background sweep in
        setup_memory_management still runs every 5 minutes if needed.
        """
        if getattr(self, '_cleanup_registered', False):
            return

        self._cleanup_registered = True

        if hasattr(self, '_image_data'):
            self._image_data = None

    @classmethod
    def get_active_count(cls):
        """Get number of active handlers."""
        return len(cls._active_handlers)

    def prepare(self):
        if self._finished:
            return

        BaseHandler._active_handlers.add(self)
        self._cleanup_registered = False

        user = self.current_user
        if user != 'admin':
            return

        main_config = config.get_main()
        if main_config.get('@force_password_change'):
            # Allow access to essential URLs for password change.
            # This is to avoid redirect loops while allowing the user
            # to access the necessary pages to change the password.
            allowed_paths = [
                '/',
                '/login',
                '/login/',
                '/config/list',
                '/config/list/',
                '/config/main/get',
                '/config/main/get/',
                '/config/main/set',
                '/config/main/set/',
                '/version',
                '/version/',
                '/prefs',
                '/prefs/',
                '/prefs/set',
                '/prefs/set/',
                '/prefs/get',
                '/prefs/get/',
            ]

            # Also allow access to static files, logs, etc.
            if (self.request.path not in allowed_paths and
                    not self.request.path.startswith('/static/') and
                    not self.request.path.startswith('/log/')):
                logging.info(
                    'Admin user has a temporary password. '
                    f'Redirecting from "{self.request.path}" to settings page to force change.'
                )
                self.redirect('/')

    def check_xsrf_cookie(self):
        """Enforce XSRF cookie for state-changing requests (Q5).

        GET/HEAD/OPTIONS are XSRF-safe by HTTP spec — skip.

        Signature-authenticated server-to-server requests (e.g. relay
        events from remote cameras) carry `_signature` and authenticate
        via HMAC over the full request — these have no browser cookies
        and must bypass the cookie check. The signature is verified
        independently in `get_current_user`.

        Everything else (browser-driven POST/PUT/DELETE) requires a
        valid XSRF cookie matching the X-XSRFToken header or _xsrf
        body field, per Tornado's default.
        """
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return
        if self.get_argument('_signature', None):
            return
        super().check_xsrf_cookie()

    def get_all_arguments(self) -> dict:
        keys = list(self.request.arguments.keys())
        arguments = {key: self.get_argument(key) for key in keys}

        for key in self.request.files:
            files = self.request.files[key]
            if len(files) > 1:
                arguments[key] = files

            elif len(files) > 0:
                arguments[key] = files[0]

            else:
                continue

        # consider the json passed in body as well
        data = self.get_json()
        if data and isinstance(data, dict):
            arguments.update(data)

        return arguments

    def get_json(self):
        if not hasattr(self, '_json'):
            self._json = None
            if self.request.headers.get('Content-Type', '').startswith(
                'application/json'
            ):
                self._json = json.loads(self.request.body)

        return self._json

    def get_argument(self, name, default=None, strip=True):
        def_ = {}
        argument = RequestHandler.get_argument(self, name, default=def_)
        if argument is def_:
            # try to find it in json body
            data = self.get_json()
            if data:
                argument = data.get(name, def_)

            if argument is def_:
                argument = default

        return argument

    def finish(self, chunk=None):
        if not self._finished:
            # Security headers
            self.set_header('Server', f'motionEye/{VERSION}')
            self.set_header('X-Content-Type-Options', 'nosniff')
            self.set_header('X-Frame-Options', 'DENY')
            self.set_header('Referrer-Policy', 'no-referrer')
            # Q9: strict CSP prevents inline-script XSS. style-src keeps
            # 'unsafe-inline' because the existing UI uses inline styles;
            # script-src is locked down to same-origin.
            self.set_header(
                'Content-Security-Policy',
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "media-src 'self' blob:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
            # Q9: HSTS only on TLS connections — over plain HTTP it's
            # ignored anyway (RFC 6797) and gives a false sense of security.
            if self.request.protocol == 'https':
                self.set_header(
                    'Strict-Transport-Security',
                    'max-age=31536000; includeSubDomains',
                )
            # X-XSS-Protection deprecated/harmful in modern browsers — removed.

            return super().finish(chunk=chunk)
        else:
            logging.debug('Already finished')

    def render(self, template_name, content_type='text/html', **context):
        self.set_header('Content-Type', content_type)

        context.setdefault('version', VERSION)
        if self.xsrf_token:
            context['xsrf_token'] = self.xsrf_token.decode('utf-8')

        content = template.render(template_name, **context)
        self.finish(content)

    def finish_json(self, data=None):
        if data is None:
            data = {}
        self.set_header('Content-Type', 'application/json')
        return self.finish(json.dumps(data))

    def get_current_user(self):
        main_config = config.get_main()

        username = self.get_argument('_username', None)
        signature = self.get_argument('_signature', None)
        login = self.get_argument('_login', None) == 'true'

        admin_username = main_config.get('@admin_username')
        normal_username = main_config.get('@normal_username')

        admin_password = main_config.get('@admin_password', '')
        normal_password = main_config.get('@normal_password', '')

        # Signature HMAC key — separate from the (bcrypt) password hash. Falls back
        # to the legacy SHA-1 hash for installs not yet re-saved on bcrypt.
        admin_sig_key = main_config.get('@admin_password_sig_key') or (
            admin_password if passwords.is_legacy_hash(admin_password) else ''
        )
        normal_sig_key = main_config.get('@normal_password_sig_key') or (
            normal_password if passwords.is_legacy_hash(normal_password) else ''
        )

        # Operability: warn once per process when @*_password is bcrypt but
        # the corresponding sig_key is missing — signature auth would silently
        # break for that user until the password is re-saved.
        if admin_password and not admin_sig_key and not BaseHandler._warned_admin_sig_key_missing:
            logging.warning(
                '@admin_password_sig_key is missing while @admin_password is set; '
                'signature auth disabled for admin until the password is re-saved.'
            )
            BaseHandler._warned_admin_sig_key_missing = True
        if normal_password and not normal_sig_key and not BaseHandler._warned_normal_sig_key_missing:
            logging.warning(
                '@normal_password_sig_key is missing while @normal_password is set; '
                'signature auth disabled for normal user until the password is re-saved.'
            )
            BaseHandler._warned_normal_sig_key_missing = True

        if settings.HTTP_BASIC_AUTH and 'Authorization' in self.request.headers:
            up = utils.parse_basic_header(self.request.headers['Authorization'])
            if up:
                if up['username'] == admin_username and passwords.verify_password(
                    up['password'], admin_password
                ):
                    return 'admin'

                if up['username'] == normal_username and passwords.verify_password(
                    up['password'], normal_password
                ):
                    return 'normal'

        # Empty sig_key would let an attacker forge a deterministic HMAC of an
        # empty key; require a non-empty key for signature auth to succeed.
        # Use hmac.compare_digest for constant-time comparison (C2: prevents
        # byte-level timing-attack signature recovery).
        if (
            username == admin_username
            and admin_sig_key
            and signature is not None
            and hmac.compare_digest(
                signature,
                utils.compute_signature(
                    self.request.method, self.request.uri, self.request.body, admin_sig_key
                ),
            )
        ):
            return 'admin'

        # no authentication required for normal user
        if not username and not normal_password:
            return 'normal'

        if (
            username == normal_username
            and normal_sig_key
            and signature is not None
            and hmac.compare_digest(
                signature,
                utils.compute_signature(
                    self.request.method, self.request.uri, self.request.body, normal_sig_key
                ),
            )
        ):
            return 'normal'

        if username and username != '_' and login:
            logging.error(f'authentication failed for user {username}')

        return None

    def get_pref(self, key):
        return prefs.get(self.current_user or 'anonymous', key)

    def set_pref(self, key, value):
        return prefs.set(self.current_user or 'anonymous', key, value)

    def _handle_request_exception(self, exception):
        try:
            if isinstance(exception, HTTPError):
                logging.error(str(exception))
                self.set_status(exception.status_code)
                self.finish_json(
                    {
                        'error': exception.log_message
                        or getattr(exception, 'reason', None)
                        or str(exception)
                    }
                )

            else:
                logging.error(str(exception), exc_info=True)
                self.set_status(500)
                self.finish_json({'error': 'internal server error'})

        except RuntimeError:
            pass  # nevermind

    @staticmethod
    def auth(admin=False, prompt=True):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                _admin = self.get_argument('_admin', None) == 'true'

                user = self.current_user
                if (user is None) or (user != 'admin' and (admin or _admin)):
                    self.set_header('Content-Type', 'application/json')
                    self.set_status(403)

                    return self.finish_json({'error': 'unauthorized', 'prompt': prompt})

                return func(self, *args, **kwargs)

            return wrapper

        return decorator

    def get(self, *args, **kwargs):
        raise HTTPError(400, 'method not allowed')

    def post(self, *args, **kwargs):
        raise HTTPError(400, 'method not allowed')

    def head(self, *args, **kwargs):
        self.finish()


class NotFoundHandler(BaseHandler):
    def get(self, *args, **kwargs):
        raise HTTPError(404, 'not found')

    post = head = get


class ManifestHandler(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'application/manifest+json')
        self.set_header('Cache-Control', 'max-age=2592000')  # 30 days
        self.render('manifest.json')
