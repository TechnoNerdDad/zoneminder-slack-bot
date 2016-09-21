# ZoneMinder Slack Bot

This is a [Slack Bot](https://api.slack.com/bot-users) that monitors one or more [Slack](https://slack.com) channels for commands and interacts with a [ZoneMinder](https://www.zoneminder.com/) system to report events and
obtain information.

The primary use for this bot is to allow access to some parts of a ZoneMinder system that is behind a firewall, without having to expose the actual system to the Internet. Making a ZoneMinder system available to the Internet has several requirements (static IP, secure system) that may not be feasible for all users.

By providing a bot that can interact with both ZoneMinder and Slack, remote access to and notification from ZoneMinder is possible, without needing a static IP and using the security provided by the Slack environment.

## Installation

### Easiest : Using pip

The easiest method of installation is via `pip` as the package is available
from the [Python Package Index](https://pypi.python.org/pypi)

```sh
> pip install zonebot
```    

This will create a script called `zonebot` in your path ("`which zonebot`" will tell
you exactly where) that you can run.

### Download source and build

You can download the source from GitHub and build it yourself if you would like.

1. Download the release you want from https://github.com/rjclark/zoneminder-slack-bot/releases
1. Extract it
1. Run `python setup.py build install`

### Clone the source and build

You can also clone the source from GitHub if you would like to build the very latest version. **This is not guaranteed to work**. The unreleased source code from GitHub could be in the middle of development and running it directly is not recommended.

1. Clone this repository https://github.com/rjclark/zoneminder-slack-bot
1. Run `python setup.py build install`

Configuration
-------------

Also installed is a sample configuration file called `zonebot-example-config.cfg`.
You can copy this to your preferred location for config files and edit it to put in
your [Slack API token](https://api.slack.com/tokens) and the
[ID of your bot user](https://api.slack.com/bot-users)

The example configuration file is installed into the Python package directory on
your system, which can be somewhat difficult to find. The latest version of the
file is always available from
[the GitHub repository](https://github.com/rjclark/zoneminder-slack-bot/blob/master/docs/zonebot-example-config.cfg)
if needed.

To configure the bot, you will need several pieces of information

1. Your Slack API token. This can be found by
    1. Going to the [Slack Bot user page](https://api.slack.com/bot-users) and creating a new bot user. You will have a chance to get the API token here
    2. Going to the page for your [existing bot user](https://my.slack.com/apps/manage/custom-integrations).
2. The User ID of your bot user. This can be found by:
    1. Running the script `zonebot-getid` distributed with this package and providing the name of the Slack bot user and you Slack API token as command line options. For example:

```sh
> zonebot-getid  -a "your-slack-token" -b zoneminder
> User ID for bot 'zoneminder' is AA22BB44C
```

Once you have those, make a copy of the config file and add the Slack API token and user ID of the bot, You will also want to edit the `Permissions` section.

**NOTE**: The default config file allows only read permission to the ZoneMinder system.

The default config file can be placed in any of these locations (checked in this order)

* Any file specified by the `-c/--config` command line option
* `$XDG_CONFIG_HOME/zonebot/zonebot.conf` if the `XDG_CONFIG_HOME` environment variable is defined
* `${DIR}/zonebot/zonebot.conf` for any directory in the `XDG_CONFIG_DIRS` environment variable
* `~/.config/zonebot/zonebot.conf`
* `/etc/zonebot/zonebot.conf`
* `/etc/default/zonebot`

Building and Contributing
-------------------------

Instructions for building the ZoneMinder Slack bot are in the `docs/BUILDING.md`
file.

[![Build Status](https://travis-ci.org/rjclark/zoneminder-slack-bot.svg?branch=master)](https://travis-ci.org/rjclark/zoneminder-slack-bot)
[![Coverage Status](https://coveralls.io/repos/github/rjclark/zoneminder-slack-bot/badge.svg?branch=master)](https://coveralls.io/github/rjclark/zoneminder-slack-bot?branch=master)
[![PyPI version](https://badge.fury.io/py/zonebot.svg)](https://pypi.python.org/pypi/zonebot)
[![Dependency Status](https://www.versioneye.com/user/projects/57def689037c2000458f770d/badge.svg?style=flat-square)](https://www.versioneye.com/user/projects/57def689037c2000458f770d)
[![Code Health](https://landscape.io/github/rjclark/zoneminder-slack-bot/master/landscape.svg?style=flat)](https://landscape.io/github/rjclark/zoneminder-slack-bot/master)

If you wish to contribute, pull requests against the
[GitHub repository](https://github.com/rjclark/zoneminder-slack-bot) are welcomed.
