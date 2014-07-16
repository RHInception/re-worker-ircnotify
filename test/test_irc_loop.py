# Copyright (C) 2014 SEE AUTHORS FILE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Unittests.
"""

import mock

from contextlib import nested

from . import TestCase

from multiprocessing import Queue

from replugin import ircnotify


CONFIG = {
    'server': '127.0.0.1',
    'port': 6667,
    'ssl': False,
    'nick': 'test',
    'channels': [],
}


class TestIRCLoop(TestCase):
    """
    Tests for the IRCLoop.
    """

    def test_irc_loop(self):
        """
        Test the IRCLoop class and make sure it works as expected.
        """
        with nested(
                mock.patch('logging.Logger'),
                mock.patch('replugin.ircnotify.IRC')) as (logger, IRC):

            in_queue = Queue()
            out_queue = Queue()

            in_queue.put(('test', 'test'))
            loop = ircnotify.IRCLoop(in_queue, out_queue, logger(), CONFIG)
            loop.check_and_send()
            assert loop.irc_client.process_forever.call_count == 1
            assert loop.irc_transport.privmsg.call_count == 1
