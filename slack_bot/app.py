# coding=utf-8
import os
import re
from functools import partial

from flask import Flask

from flask_slackbot import TalkBot

import settings
import plugins
from ext import redis_store, cache


plugin_modules = []
for plugin_name in plugins.__all__:
    __import__('slack_bot.plugins.%s' % plugin_name)
    plugin_modules.append(getattr(plugins, plugin_name))


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(settings)

    if isinstance(config, dict):
        app.config.update(config)
    elif config:
        app.config.from_pyfile(os.path.realpath(config))

    redis_store.init_app(app)
    cache.init_app(app)
    app.plugin_modules = plugin_modules

    slackbot = TalkBot(app)
    _callback = partial(callback, app=app)
    slackbot.set_handler(_callback)
    # slackbot.filter_outgoing(_filter)

    return app


def replaced(message, rep_words):
    for word in rep_words:
        message = message.replace(word, '', 1)
    return message


def callback(kwargs, app):
    s = kwargs['text']
    data = {
        'message': ''
    }
    if isinstance(s, unicode):
        data['message'] = s.encode('utf-8').strip()

    print data
    if not data['message']:
        return {'text': ''}

    for plugin_module in plugin_modules:
        if plugin_module.test(data):
            ret = plugin_module.handle(data, cache=cache, app=app)
            if not isinstance(ret, tuple):
                text = ret
                attaches = None
            else:
                text, attaches = ret
            return {'text': text}

    return {'text': '!呵呵'}


def _filter(line):
    return line.startswith('!')


if __name__ == '__main__':
    app = create_app()
    app.debug = True
    app.run()
