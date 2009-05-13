#!/usr/bin/python
import time
import os

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from django.core import urlresolvers
from django.utils.encoding import force_unicode
from django.conf import settings

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'test.settings'

class IRCRequest(object):
    def __init__(self, nick, user, channel, msg, method='privmsg',
                 **kwargs):
        self.nick = nick
        self.user = user
        self.channel = channel
        self.message = force_unicode(msg)
        self.method = method.lower()
        self.context = kwargs

class IRCResponse(object):
    def __init__(self, recipient, data, method=irc.IRCClient.msg,
                 **kwargs):
        self.recipient = recipient
        self.data = data
        self.method = method
        self.context = kwargs
    def __call__(self):
        return self.method(recipient, data)
    def __str__(self):
        return u'%s: <%s> %s' % (self.method, self.recipient, self.data)


class DjangoBot(irc.IRCClient):
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
        resolver = urlresolvers.get_resolver('.'.join((settings.ROOT_MSGCONF,
                                           req.method.lower())))
        callback, args, kwargs = yield resolver.resolve('/' + req.message)
        response = yield callback(req, *args, **kwargs)
        print response
        defer.returnValue(response.method(self, response.recipient,
                                          response.data.encode('UTF-8')))

    def privmsg(self, user, channel, msg):
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self.nickname, user, channel, msg, 'privmsg')
            self.dispatch(req)
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

