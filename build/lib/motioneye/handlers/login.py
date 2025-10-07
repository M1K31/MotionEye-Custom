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

import logging
from tornado.web import HTTPError
from motioneye import database
from motioneye.handlers.base import BaseHandler

__all__ = ('LoginHandler',)


# this will only trigger the login mechanism on the client side, if required
class LoginHandler(BaseHandler):
    @BaseHandler.auth()
    def get(self):
        self.finish_json()

    def post(self):
        # Enforce rate limiting before attempting to log in.
        username = self.get_argument('_username', None)
        if username:
            try:
                database.check_rate_limit(username)
            except Exception as e:
                logging.warning(f"Rate limit exceeded for user '{username}': {e}")
                raise HTTPError(429, str(e))

        # The actual login logic is handled by BaseHandler.get_current_user,
        # which is called implicitly by the authentication mechanism.
        # We just need to finish the request.
        self.set_header('Content-Type', 'text/html')
        self.finish()