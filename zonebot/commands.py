#! -*- coding: utf-8 -*-

#
# Copyright 2016 Robert Clark (clark@exiter.com)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

"""
All the commands possible for the bot. This is basically a big routing table.
"""

import zonebot

import logging
from abc import ABCMeta, abstractmethod

LOGGER = logging.getLogger("zonebot")


class Command:
    """ Static mapping of Slack user IDs to user names """

    __metaclass__ = ABCMeta

    _usermap = {}

    def __init__(self, config=None):
        self.config = config

    @abstractmethod
    def perform(self, user_name, commands, zoneminder):
        pass

    @abstractmethod
    def report(self, slack, channel):
        pass

    @staticmethod
    def log_slack_result(result):
        """
        Logs the result of a slack API call.

        :param result: The result object from Slack
        """

        if not result:
            return

        if not result['ok']:
            error = "Error: "
            if 'error' in result:
                error = result['error']
            elif 'warning' in result:
                error = result['warning']

            LOGGER.error("Could not respond to the command: %s", error)

    @staticmethod
    def resolve_user(user_id, slack):
        """
        Resolve (if not already cached) the Slack user ID into a user name

        :param user_id: Slack user ID of the user (e.g. 'U1234567890')
        :type user_id: str
        :param slack: A fully configured `slackclient` instance
        :return: The resolved name of the user or `None` if the user ID could not be resolved.
        """

        if not user_id:
            return None

        user_name = None
        if user_id in Command._usermap:
            user_name = Command._usermap[user_id]

        if not user_name:
            LOGGER.info("Doing Slack lookup for user ID %s", user_id)
            result = slack.api_call("users.info",
                                    user=user_id,
                                    as_user=True)

            if result['ok']:
                user_name = result['user']['name'].lower()
                Command._usermap[user_id] = user_name
            else:
                LOGGER.error("Could not convert %s to a user name: %s", user_id, result['error'])

        return user_name

    @staticmethod
    def has_permission(user_name, config, command, permission):
        """
        Checks to see if the user has the required permissions to execute the provided
        command.

        :param user_name: Name of the user (*not* the Slack user ID)
        :type user_name: str
        :param permission:
        :param command:
        :param config:
        :return: True if the user is allow the execute the command and false if they are not.
        :rtype: bool
        """

        if 'any' == permission:
            return True

        # Now things get complicated.

        # First check to see if any permissions are defined. If they are not, then
        # anyone can do anything.
        if not config or not config.has_section('Permissions'):
            LOGGER.info("No config section")
            return True

        if not user_name:
            LOGGER.error('Could not resolve user ID %s', user_name)
            return False

        # Not listed in the permissions section, they only have read access
        access = config.get('Permissions', user_name.lower(), fallback='read')
        access = [x.strip() for x in access.split(',')]

        # They have specific permissions listed. See if this command is one of them

        if 'any' in access:
            # they are allowed to do anything
            return True
        if permission in access:
            # check by type
            return True
        elif command in access:
            # check by specific command
            return True

        # No match, not allowed
        LOGGER.info("User name %s and has access %s. They are not allowed the %s command",
                    user_name,
                    access,
                    command)

        return False


class About(Command):
    """
    Prints about text.
    """
    def __init__(self, config=None):
        super(About, self).__init__(config=config)

    def perform(self, user_name, commands, zoneminder):
        pass

    def report(self, slack, channel):
        text = "*{0}* version {1}\n".format(zonebot.__project_name__, zonebot.__version__)
        text += "_Copyright_ (c) 2016 <mailto:{1}|{0}> .".format(zonebot.__author__, zonebot.__email__)

        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text=text,
                              as_user=True)


class Help(Command):
    """
    Generates the help test that lists available commands
    """

    def __init__(self, config=None):
        super(Help, self).__init__(config=config)
        self.user_name = None
        self.config = config

    def perform(self, user_name, commands, zoneminder):
        self.user_name = user_name
        pass

    def report(self, slack, channel):
        text = 'Supported commands\n'

        global _all_commands
        for command_name in sorted(_all_commands.keys(), key=lambda x: _all_commands[x]['index']):
            command = _all_commands[command_name]

            if 'meta' in command and command['meta']:
                continue

            permission = command['permission']
            if Command.has_permission(self.user_name, self.config, command_name, permission):
                text += "• _{0}_ : {1}\n".format(command_name, command['help'])

        text += "_{0} version {1}_".format(zonebot.__project_name__, zonebot.__version__)

        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text=text,
                              as_user=True)


class Unknown(Command):
    def __init__(self, config=None):
        super(Unknown, self).__init__(config=config)
        self.commands = None

    def perform(self, user_name, commands, zoneminder):
        self.commands = ' '.join(commands)

    def report(self, slack, channel):
        text = "_*Error*_: Unrecognized command '{0}'. Use 'help' for a list of supported commands"\
            .format(self.commands)

        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text=text,
                              as_user=True)


class Denied(Unknown):
    def __init__(self, config=None):
        super(Denied, self).__init__(config=config)

    def report(self, slack, channel):
        text = "_*Error*_: You do not have permission to execute {0}".format(self.commands)

        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text=text,
                              as_user=True)


class ListMonitors(Command):
    def __init__(self, config=None):
        super(ListMonitors, self).__init__(config=config)

        self.attachments = []

    def perform(self, user_name, commands, zoneminder):
        monitors = zoneminder.get_monitors()
        monitors.load()

        for monitor_name in monitors.monitors:
            monitor = monitors.monitors[monitor_name]

            enabled = 'Yes' if monitor['Enabled'] == '1' else 'No'
            color = '#2fa44f' if monitor['Enabled'] == '1' else '#d52000'

            self.attachments.append({
                'text': '{0} (ID: {1})'.format(monitor['Name'], monitor['Id']),
                'fields': [
                    {
                        'title': 'Enabled',
                        'value': enabled,
                        'short': True
                    },
                    {
                        'title': 'Detection',
                        'value': monitor['Function'],
                        'short': True
                    }
                ],
                'color': color
            })

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              attachments=self.attachments,
                              as_user=True)


class ToggleMonitor(Command):
    def __init__(self, config=None):
        super(ToggleMonitor, self).__init__(config=config)
        self.result = None

    def perform(self, user_name, commands, zoneminder):
        if len(commands) < 3:
            self.result = '*Error*: the name of the monitor is required. ' \
                          '_\'list monitors\'_ will display them all'
            return

        on = True if commands[0] == 'enable' else False
        name = commands[2].strip().lower()

        monitors = zoneminder.get_monitors()
        monitors.load()

        if name not in monitors.monitors:
            self.result = '*Error*: monitor {0} not found. ' \
                          '_\'list monitors\'_ will display them all'.format(name)
            return

        changed = monitors.set_state(name, on)

        self.result = 'Monitor {0} state {1}'.format(name, changed)

    def report(self, slack, channel):
        return slack.api_call("chat.postMessage",
                              channel=channel,
                              text=self.result,
                              as_user=True)

#
# meta - true for meta (not user) command that should not show up in the help
# index - the oder in which the command should be displayed in the help output
#
_all_commands = {
    'unknown': {
        'permission': 'any',
        'meta': True,
        'classname': Unknown,
        'index': 0
    },
    'help': {
        'permission': 'any',
        'meta': True,
        'classname': Help,
        'index': 0
    },
    'denied': {
        'permission': 'any',
        'meta': True,
        'classname': Denied,
        'index': 0
    },
    'about': {
        'permission': 'any',
        'classname': About,
        'help': 'Display bot version information',
        'index': 1
    },
    'list monitors': {
        'permission': 'read',
        'help': 'List all monitors and their current state',
        'classname': ListMonitors,
        'index': 2
    },
    'enable monitor': {
        'permission': 'write',
        'help': 'Enable alarms on a monitor (supplied by name, not ID)',
        'classname': ToggleMonitor,
        'index': 3
    },
    'disable monitor': {
        'permission': 'write',
        'help': 'Disable alarms on a monitor (supplied by name, not ID)',
        'classname': ToggleMonitor,
        'index': 4
    }
}


def get_command(words, user_id=None, config=None, slack=None):
    """
    Gets the command that matches the input words.

    :param words: The list of words that make up the command and its arguments.
    :type words: List[str]
    :param user_id:
    :param config:
    :param slack:
    :return: The command matching the input. A command is always returned
    :rtype: Command
    """

    global _all_commands

    if not words or len(words) < 1:
        return Help()

    command_text = words[0].strip().lower()
    if command_text not in _all_commands:
        if len(words) > 1:
            command_text = '{0} {1}'.format(words[0].strip().lower(), words[1].strip().lower())

    if command_text not in _all_commands:
        return Unknown()

    perms = _all_commands[command_text]['permission']
    user_name = Command.resolve_user(user_id, slack)

    if not Command.has_permission(user_name, config, command_text, perms):
        return Denied()

    return _all_commands[command_text]['classname'](config=config)
