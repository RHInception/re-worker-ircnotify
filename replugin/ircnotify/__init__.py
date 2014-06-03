#!/usr/bin/env python
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
IRC Notification worker.
"""


from reworker.worker import Worker

from irc.client import IRC


class IRCNotifyWorkerError(Exception):
    """
    Base exception class for IRCNotifyWorker errors.
    """
    pass


class IRCNotifyWorker(Worker):
    """
    Worker which knows how to push notification to IRC.
    """

    def process(self, channel, basic_deliver, properties, body, output):
        """
        Sends notifications to IRC.

        `Params Required`:
            * target: The person or channel who will receive the message.
            * msg: The message to send.
        """
        # Ack the original message
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        # Notify we are starting
        self.send(
            properties.reply_to, corr_id, {'status': 'started'}, exchange='')

        try:
            required_keys = ('slug', 'message', 'phase', 'target')
            try:
                # Remove target from this check
                for key in required_keys[0:3]:
                    if key not in body.keys():
                        raise KeyError()
                    if type(body[key]) is not str:
                        raise ValueError()
                # Check target on it's own since it's a list of strs
                if 'target' not in body.keys():
                    raise KeyError()
                if type(body['target']) is not list:
                    raise ValueError()
                for key in body['target']:
                    if type(key) is not str:
                        raise ValueError()
            except KeyError:
                raise IRCNotifyWorkerError(
                    'Missing a required param. Requires: %s' % str(
                        required_keys))
            except ValueError:
                raise IRCNotifyWorkerError('All inputs must be str.')

            output.info('Sending notification to %s on IRC' % ", ".join(
                body['target']))
            for target in body['target']:
                self._send_msg(target, body['message'])
            output.info('IRC notification sent!')
            self.app_logger.info('Finished IRC notification with no errors.')

        except IRCNotifyWorkerError, fwe:
            # If a IRCNotifyWorkerError happens send a failure, notify and log
            # the info for review.
            self.app_logger.error('Failure: %s' % fwe)

            self.send(
                properties.reply_to,
                corr_id,
                {'status': 'failed'},
                exchange=''
            )
            output.error(str(fwe))

    def _send_msg(self, target, msg):
        """
        Sends a message to IRC.

        `Parameters`:
            * target: The person or channel who will receive the message.
            * msg: The message to send.
        """
        # If we are sending to a channel we are not in then join it!
        if target.startswith('#') and target not in self._config['channels']:
            self.app_logger.info('Joining %s to send a message' % irc_chan)
            self._irc.transport.join(target)
            self._config['channels'].append(target)
        self.app_logger.debug('Sending "%s" the message "%s"', (target, msg))
        self._irc_transport.privmsg(target, msg)
        self.app_logger.debug('Executing IRC.process_once(5)')
        self._irc_client.process_once(5)
        self.app_logger.debug('IRCNotifyWorker._send_msg() finished.')

    def _setup_irc(self):
        """
        Sets up the IRC related variables.
        """
        self._irc_client = IRC()
        self._irc_transport = self._irc_client.server()
        self.app_logger.info(
            'Connecting to IRC %s:%s as %s' % (
                self._config['server'],
                self._config['port'],
                self._config['nick']))
        self._irc_transport.connect(
            self._config['server'],
            int(self._config['port']),
            self._config['nick'])
        self.app_logger.info('IRC connection established.')
        for irc_chan in self._config['channels']:
            self.app_logger.info('Joining %s' % irc_chan)
            self._irc_transport.join(irc_chan)

    def run_forever(self):
        """
        Override run_forever so we can wrap IRC connection/disconnection.
        """
        self._setup_irc()
        # Execute Worker's run_forver
        Worker.run_forever(self)
        self._irc_transport.disconnect('Worker exit.')
        self.app_logger.info('Disconnected from IRC.')


if __name__ == '__main__':  # pragma nocover
    from reworker.worker import runner
    runner(IRCNotifyWorker)
