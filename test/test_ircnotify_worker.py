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

import pika
import mock
import json

from contextlib import nested

from . import TestCase

from replugin import ircnotify


MQ_CONF = {
    'server': '127.0.0.1',
    'port': 5672,
    'vhost': '/',
    'user': 'guest',
    'password': 'guest',
}


class TestIRCNotifyWorker(TestCase):

    def setUp(self):
        """
        Set up some reusable mocks.
        """
        TestCase.setUp(self)

        self.channel = mock.MagicMock('pika.spec.Channel')

        self.channel.basic_consume = mock.Mock('basic_consume')
        self.channel.basic_ack = mock.Mock('basic_ack')
        self.channel.basic_publish = mock.Mock('basic_publish')

        self.basic_deliver = mock.MagicMock()
        self.basic_deliver.delivery_tag = 123

        self.properties = mock.MagicMock(
            'pika.spec.BasicProperties',
            correlation_id=123,
            reply_to='me')

        self.logger = mock.MagicMock('logging.Logger').__call__()
        self.app_logger = mock.MagicMock('logging.Logger').__call__()
        self.connection = mock.MagicMock('pika.SelectConnection')

    def tearDown(self):
        """
        After every test.
        """
        TestCase.tearDown(self)
        self.channel.reset_mock()
        self.channel.basic_consume.reset_mock()
        self.channel.basic_ack.reset_mock()
        self.channel.basic_publish.reset_mock()

        self.basic_deliver.reset_mock()
        self.properties.reset_mock()

        self.logger.reset_mock()
        self.app_logger.reset_mock()
        self.connection.reset_mock()

    def test__setup_irc(self):
        """
        Verify _setup_irc properly sets up IRC variables.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.notify'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.send'),
                mock.patch('replugin.ircnotify.IRC')) as (
                    _, _, _, ircmock):
            worker = ircnotify.IRCNotifyWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json',
                output_dir='/tmp/logs/')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            worker._setup_irc()
            # IRC() should be called once
            ircmock.assert_called_once()
            # We should have the following variables defined
            assert worker._irc_client
            assert worker._irc_transport
            # Verify the connection used the config details
            with open('conf/example.json', 'r') as conf_f:
                config_data = json.load(conf_f)
                worker._irc_transport.connect.assert_called_once_with(
                    config_data['server'],
                    int(config_data['port']),
                    config_data['nick'])

    def test__send_msg(self):
        """
        Verify _send_msg calls the proper methods.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.notify'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.send'),
                mock.patch('replugin.ircnotify.IRC')):
            worker = ircnotify.IRCNotifyWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json',
                output_dir='/tmp/logs/')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            worker._setup_irc()
            worker._send_msg('someone', 'this is a test')
            # We should end up sending the data to the server
            worker._irc_transport.privmsg.assert_called_once_with(
                'someone', 'this is a test')
            worker._irc_client.process_once.assert_called_once()

    def test_run_forever(self):
        """
        Since this worker overrides run_forever, make sure it calls everything
        needed.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.notify'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.send'),
                mock.patch('replugin.ircnotify.Worker.run_forever'),
                mock.patch('replugin.ircnotify.IRC')) as (_, _, _, rf, _):

            worker = ircnotify.IRCNotifyWorker(
                MQ_CONF,
                logger=self.app_logger,
                config_file='conf/example.json',
                output_dir='/tmp/logs/')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)
            worker.run_forever()
            # We should have the following variables defined because
            # of _setup_irc
            assert worker._irc_client
            assert worker._irc_transport
            # Worker.run_forever must be called
            assert rf.assert_called_once()

    def test_irc_notification(self):
        """
        Verify that when a notification comes in the proper IRC results happen.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.notify'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.send'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker._send_msg'),
                mock.patch('replugin.ircnotify.IRC')):

            worker = ircnotify.IRCNotifyWorker(
                MQ_CONF,
                logger=self.app_logger,
                output_dir='/tmp/logs/')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)

            body = {
                'slug': 'short',
                'message': 'test message',
                'phase': 'started',
                'target': 'someone',
            }

            # Execute the call
            worker.process(
                self.channel,
                self.basic_deliver,
                self.properties,
                body,
                self.logger)
            # This should send a message
            worker._send_msg.assert_called_once_with(
                'someone', 'test message')

    def test_irc_notification_fails_with_bad_data(self):
        """
        Verify that when a notification comes in with bad data the
        proper exceptions happen.
        """
        with nested(
                mock.patch('pika.SelectConnection'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.notify'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker.send'),
                mock.patch('replugin.ircnotify.IRCNotifyWorker._send_msg'),
                mock.patch('replugin.ircnotify.IRC')):

            worker = ircnotify.IRCNotifyWorker(
                MQ_CONF,
                logger=self.app_logger,
                output_dir='/tmp/logs/')

            worker._on_open(self.connection)
            worker._on_channel_open(self.channel)

            fail_msgs = (
                {'slug': 'a', 'message': 1, 'phase': 'started', 'target': 'a'},
                {'slug': 1, 'message': 'a', 'phase': 'started', 'target': 'a'},
                {'slug': 'a', 'message': 'a', 'phase': 1, 'target': 'a'},
                {'slug': 'a', 'message': 'a', 'phase': 'a', 'target': 1},
                {'message': 'a', 'phase': 'a', 'target': 'a'},
                {'slug': 'a',  'phase': 'a', 'target': 'a'},
                {'slug': 'a', 'message': 'a', 'target': 'a'},
                {'slug': 'a', 'message': 'a', 'phase': 'a'},
            )

            for body in fail_msgs:
                # Reset some mocks
                worker.send.reset_mock()
                worker.notify.reset_mock()
                self.logger.reset_mock()

                # Execute the call
                worker.process(
                    self.channel,
                    self.basic_deliver,
                    self.properties,
                    body,
                    self.logger)

                assert worker.send.call_count == 2  # start then error
                assert worker.send.call_args[0][2] == {
                    'status': 'failed'}
                assert worker.notify.call_count == 1
                assert worker.notify.call_args[0][2] == 'failed'
                # Log should have one error
                assert self.logger.error.call_count == 1

                # This should not send a message
                assert worker._send_msg.call_count == 0
