#!/usr/bin/python
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer

from django.core import exceptions, urlresolvers
from django.http import HttpRequest, HttpResponse
from django.utils.encoding import force_unicode

import time

class IRCRequest(object):
    def __init__(self, user, channel, msg, method='PRIVMSG'):
        self.user = user
        self.channel = channel
        self.message = force_unicode(msg)
        self.method = method.upper()

class IRCResponse(object):
    def __init__(self, recipient, data, method=irc.IRCClient.msg):
        self.recipient = recipient
        self.data = data
        self.method = method
    def __call__(self):
        return self.method(recipient, data)
    def __str__(self):
        return u'%s: <%s> %s' % (self.method, self.recipient, self.data)


class IRCReplyBot(irc.IRCClient):
    def __init__(self, *args, **kwargs):
        self.users = {}
    
    def connectionMade(self):
        self.nickname = self.factory.nickname
        irc.IRCClient.connectionMade(self)
        print("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        print("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def getUser(self, user):
        return defer.succeed(self.users.get(user, "No such user"))

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        print("[I have joined %s]" % channel)
    def privmsg(self, user, channel, msg):
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(user, channel, msg, 'PRIVMSG')
            self.dispatch(req)
    @defer.inlineCallbacks
    def dispatch(self, req):
        resolver = urlresolvers.RegexURLResolver(r'\S',
                                                 req.method.lower())
        callback, args, kwargs = yield resolver.resolve('/' + req.message)
        response = yield callback(req, *args, **kwargs)
        print response
        defer.returnValue(response.method(self, response.recipient,
                                          response.data.encode('UTF-8')))


if __name__ == '__main__':
    import sys
    from twisted.internet import ssl
    f = protocol.ReconnectingClientFactory()
    f.protocol,f.nickname,f.channel = IRCReplyBot,sys.argv[1],sys.argv[2]
    reactor.connectSSL("irc.slashnet.org", 6697, f,
                       ssl.ClientContextFactory())
    reactor.run()

