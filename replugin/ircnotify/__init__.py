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

import types

from time import sleep

from multiprocessing import Process, Queue

from reworker.worker import Worker

from irc.client import IRC


class IRCLoop(object):

    def __init__(self, in_queue, out_queue, app_logger, config):
        """
        Loop process for irc communications.

        in_queue is inward coms to pass through to irc
        out_queue is used to notify the parent process connection finished
        app_logger is a logger instance
        config is the configuration structure
        """
        # Set up
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.config = config
        self.app_logger = app_logger

        self.irc_client = IRC()
        self.irc_transport = self.irc_client.server()
        self.app_logger.info(
            'Connecting to IRC %s:%s as %s' % (
                self.config['server'],
                self.config['port'],
                self.config['nick']))

        self.irc_transport.connect(
            self.config['server'],
            int(self.config['port']),
            self.config['nick'])
        self.app_logger.info('IRC connection established.')
        for irc_chan in self.config['channels']:
            self.app_logger.info('Joining %s' % irc_chan)
            self.irc_transport.join(irc_chan)

        # Wait for a connection to be made
        for x in range(0, 20):
            if self.irc_transport.is_connected():
                self.out_queue.put(True)
                break
            else:
                sleep(2)

        # Check every second for datat to send to irc
        self.irc_transport.execute_every(1, self.check_and_send)
        # The blocking loop
        self.irc_client.process_forever()

    def check_and_send(self):
        """
        If there is any data to be sent to irc from the in_queue this internal
        function will send it.
        """
        if not self.in_queue.empty():
            target, msg = self.in_queue.get()
            # If we are sending to a channel we are not in then join it!
            if target.startswith('#') and target not in config['channels']:
                app_logger.info('Joining %s to send a message' % target)
                self.irc_transport.join(target)
                self.config['channels'].append(target)
            self.app_logger.debug('Sending "%s" the message "%s"', (target, msg))
            self.irc_transport.privmsg(target, msg)
            self.app_logger.debug('check_and_send()finished.')


class IRCNotifyWorkerError(Exception):
    """
    Base exception class for IRCNotifyWorker errors.
    """
    pass


class IRCNotifyWorker(Worker):
    """
    Worker which knows how to push notification to IRC.
    """

    def __init__(self, *args, **kwargs):
        """
        Creates an instance of the IRCNotifyWorker.
        """
        Worker.__init__(self, *args, **kwargs)
        self._irc_comm = Queue()
        self._irc_resp = Queue()
        self._irc_client = Process(
            target=IRCLoop,
            args=(self._irc_comm, self._irc_resp,
                  self.app_logger, self._config))
        self._irc_client.start()

    def process(self, channel, basic_deliver, properties, body, output):
        """
        Sends notifications to IRC.

        `Params Required`:
            * target: List of persons/channels who will receive the message.
            * msg: The message to send.
        """
        if not getattr(self, '_irc_comm', None):
            self.reject(basic_deliver, requeue=True)
            self.app_logger(
                'Not connected to IRC yet. Putting message back on the bus.')
            return

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
                    if not type(body[key]) in types.StringTypes:
                        raise ValueError()
                # Check target on it's own since it's a list of strs
                if 'target' not in body.keys():
                    raise KeyError()
                if type(body['target']) is not list:
                    raise ValueError()
                for key in body['target']:
                    if not type(key) in types.StringTypes:
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
                self._irc_comm.put((target, body['message']))
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

    def run_forever(self):
        """
        Override run_forever so we can wrap IRC connection/disconnection.
        """
        # Wait to get the connection response before joining the bus
        try:
            if self._irc_resp.get(timeout=30) is True:
                # Execute Worker's run_forver
                Worker.run_forever(self)
                self._irc_client.terminate()
                self._irc_client.join()
                self.app_logger.info('Disconnected from IRC.')
            else:
                raise Queue.Empty
        except Queue.Empty:
            self.app_logger.fatal('Unable to connect to IRC!')


def main():  # pragma nocover
    from reworker.worker import runner
    runner(IRCNotifyWorker)


if __name__ == '__main__':  # pragma nocover
    main()
