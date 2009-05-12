#!/usr/bin/python
import time

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer
from django.core import urlresolvers
from django.utils.encoding import force_unicode


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
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        print("[I have joined %s]" % channel)
    def privmsg(self, user, channel, msg):
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self.nickname, user, channel, msg, 'privmsg')
            self.dispatch(req)
    @defer.inlineCallbacks
    def dispatch(self, req):
        resolver = urlresolvers.get_resolver(req.method.lower())
        callback, args, kwargs = yield resolver.resolve('/' + req.message)
        response = yield callback(req, *args, **kwargs)
        print response
        defer.returnValue(response.method(self, response.recipient,
                                          response.data.encode('UTF-8')))


if __name__ == '__main__':
    import sys
    from twisted.internet import ssl
    f = protocol.ReconnectingClientFactory()
    f.protocol,f.nickname,f.channel = DjangoBot,sys.argv[1],sys.argv[2]
    reactor.connectSSL("irc.slashnet.org", 6697, f,
                       ssl.ClientContextFactory())
    reactor.run()

