#!/usr/bin/python
import time
import os
import re

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from django.core import urlresolvers
from django.utils.encoding import force_unicode
from django.conf import settings
import logging

import logging.handlers

LOG_FILENAME = '/tmp/yardbird.log'

# Set up a specific logger with our desired output level
yardlogger = logging.getLogger('YardLogger')
yardlogger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, 'm',
                                                    10)

yardlogger.addHandler(handler)


if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'


class IRCRequest(object):
    def __init__(self, connection, user, channel, msg, method='privmsg',
                 **kwargs):
        self.nick = connection.nickname
        self.user = user
        self.channel = channel
        self.message = force_unicode(msg)
        self.method = method.lower()
        self.context = kwargs
    def __str__(self):
        s = u'%s: <%s> %s' % (self.channel, self.user, self.message)
        return s.encode('utf-8')

class IRCResponse(object):
    def __init__(self, recipient, data, method='PRIVMSG',
                 **kwargs):
        self.recipient = recipient
        self.data = data
        self.method = method
        self.context = kwargs
    def __str__(self):
        s = u'%s: <%s> %s' % (self.method, self.recipient, self.data)
        return s.encode('utf-8')

def reply(bot, request, message, *args, **kwargs):
    nick = request.user.split('!', 1)[0]
    if request.channel != request.nick:
        recipient = request.channel
        kwargs['nick'] = nick
        message = '%(nick)s: ' + message
    else:
        recipient = nick
    res = IRCResponse(recipient, message % kwargs, method='NOTICE')
    return bot.methods[res.method](res.recipient, res.data.encode('utf-8'))

def terrible_error(failure, bot, request, *args, **kwargs):
    yardlogger.debug(failure)
    e = str(failure.getErrorMessage())
    if 'path' in e and 'tried' in e:
        return reply(bot, request, 'Dude?')
    return reply(bot, request, u'Dude! %s' % e)

class DjangoBot(irc.IRCClient):
    def __init__(self):
        self.methods = {'PRIVMSG': self.msg,
                        'ACTION':  self.me,
                        'NOTICE':  self.notice,
                        'TOPIC':   self.topic,
                       }
    def connectionMade(self):
        self.nickname = self.factory.nickname
        irc.IRCClient.connectionMade(self)
        print("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        print("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def signedOn(self):
        for channel in self.factory.channels:
            self.join(channel)
    def joined(self, channel):
        print("[I have joined %s]" % channel)

    @defer.inlineCallbacks
    def dispatch(self, req):
        """This method abuses the django url resolver to detect
        interesting messages and dispatch them to callback functions
        based on regular expression matches."""
        yardlogger.info(req)
        resolver = urlresolvers.get_resolver('.'.join(
            (settings.ROOT_MSGCONF, req.method.lower())))
        callback, args, kwargs = yield resolver.resolve('/' + req.message)
        response = yield callback(req, *args, **kwargs)
        yardlogger.info(response)
        defer.returnValue(self.methods[response.method](response.recipient,
                                          response.data.encode('UTF-8')))

    def privmsg(self, user, channel, msg):
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self, user, channel, msg, 'privmsg')
            self.dispatch(req).addErrback(terrible_error, self, req)
            # That Errback should be something smart that separates 404
            # from 500 etc.
    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self.nickname, user, channel, msg, 'action')
            self.dispatch(req)
    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        if self.nickname not in (old_nick, new_nick):
            req = IRCRequest(self.nickname, old_nick, '', new_nick, 'nick')
            self.dispatch(req)


if __name__ == '__main__':
    import sys
    from twisted.internet import ssl

    f = protocol.ReconnectingClientFactory()
    f.protocol = DjangoBot
    f.nickname, f.channels = settings.IRC_NICK, settings.IRC_CHANNELS
    reactor.connectSSL("irc.slashnet.org", 6697, f,
                       ssl.ClientContextFactory())
    reactor.run()

