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


class IRCWorkerError(Exception):
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
            * target: The person or channel to get the message.
        """
        # Ack the original message
        self.ack(basic_deliver)
        corr_id = str(properties.correlation_id)
        # Notify we are starting
        self.send(
            properties.reply_to, corr_id, {'status': 'started'}, exchange='')


if __name__ == '__main__':
    from reworker.worker import runner
    runner(IRCNotifyWorker)
