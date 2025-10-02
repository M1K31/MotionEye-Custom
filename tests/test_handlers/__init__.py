import os
import tempfile
from typing import Type, TypeVar
from unittest.mock import MagicMock

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler

from motioneye import config, meyectl, settings
from motioneye.server import make_app

__all__ = ('HandlerTestCase',)


T = TypeVar('T', bound=RequestHandler)


class HandlerTestCase(AsyncHTTPTestCase):
    handler_cls = NotImplemented  # type: Type[T]

    def get_app(self) -> Application:
        # Isolate test file system operations in a temporary directory
        self.tmpdir = tempfile.TemporaryDirectory()
        settings.CONF_PATH = self.tmpdir.name
        settings.RUN_PATH = self.tmpdir.name
        settings.LOG_PATH = self.tmpdir.name
        settings.MEDIA_PATH = self.tmpdir.name

        # Create an empty main config file so it can be written to
        open(os.path.join(settings.CONF_PATH, 'motion.conf'), 'a').close()

        # Invalidate any cached configs from previous runs
        config.invalidate()

        # Initialize translation services for testing to prevent i18n errors
        meyectl.load_l10n()
        self.app = make_app()
        return self.app

    def get_handler(self, request: MagicMock = None) -> T:
        req = request or MagicMock()
        return self.handler_cls(self.app, req)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        super().tearDown()