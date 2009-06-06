#!/usr/bin/python
import time
import logging

from twisted.words.protocols.irc import IRCClient
from twisted.internet import defer, threads, task
from django.core import urlresolvers
from django.conf import settings

from irc import IRCRequest
from shortcuts import reply


def terrible_error(failure, bot, request, *args, **kwargs):
    logging.debug(failure)
    e = str(failure.getErrorMessage())
    if 'path' in e and 'tried' in e:
        return reply(bot, request, 'Dude?')
    return reply(bot, request, u'Dude! %s' % e)

class DjangoBot(IRCClient):
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.methods = {'PRIVMSG': self.msg,
                        'ACTION':  self.me,
                        'NOTICE':  self.notice,
                        'TOPIC':   self.topic,
                       }
        self.chanmodes = {}
        self.whoreplies = {}
        self.hostmask = '' # until we see ourselves speak, we do not know
        self.versionName = 'yardbird'
        self.sourceURL = 'http://zork.net/~nick/yardbird/'
        self.realname = 'YardBird'
        self.lineRate = 1
        self.servername = ''

    def myInfo(self, servername, version, umodes, cmodes):
        self.servername = servername
    def connectionMade(self):
        self.nickname = self.factory.nickname
        IRCClient.connectionMade(self)
        self.l = task.LoopingCall(self.PING)
        self.l.start(60.0) # call every minute
        logging.info("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def connectionLost(self, reason):
        IRCClient.connectionLost(self, reason)
        self.l.stop() # All done now.
        logging.info("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def signedOn(self):
        self.msg(self.nickname, 'Watching for my own hostmask')
        for channel in self.factory.channels:
            self.join(channel)
    def joined(self, channel):
        logging.info("[I have joined %s]" % channel)
        self.who(channel)
        self.msg(channel, 'what up, meatbags')

    def PING(self):
        if self.servername:
            logging.debug('PING %s' % self.servername)
            self.sendLine('PING %s' % self.servername)
    def who(self, channel):
        self.whoreplies[channel] = {}
        self.sendLine('WHO %s' % channel)
    def irc_RPL_WHOREPLY(self, prefix, args):
        me, chan, uname, host, server, nick, modes, name = args
        mask = '%s!%s@%s' % (nick, uname, host)
        self.whoreplies[chan][mask] = modes
    def irc_RPL_ENDOFWHO(self, prefix, args):
        channel = args[1]
        self.chanmodes[channel] = self.whoreplies[channel]
    def modeChanged(self, user, chan, setp, modes, args):
        self.who(chan)


    @defer.inlineCallbacks
    def dispatch(self, req):
        """This method abuses the django url resolver to detect
        interesting messages and dispatch them to callback functions
        based on regular expression matches."""
        resolver = urlresolvers.get_resolver('.'.join(
            (settings.ROOT_MSGCONF, req.method.lower())))
        callback, args, kwargs = yield resolver.resolve('/' + req.message)
        response = yield threads.deferToThread(callback, req, *args,
                                               **kwargs)
        if response.method == 'QUIET':
            logging.info(response)
            defer.returnValue(True)
        elif response.method == 'PRIVMSG':
            opts = {'length':
                    510 - len(':! PRIVMSG  :' + self.nickname +
                              response.recipient + self.hostmask)}
            logging.info(response)
        else:
            opts = {}
        defer.returnValue(
            self.methods[response.method](response.recipient,
                                          response.data.encode('UTF-8'),
                                          **opts))

    def noticed(self, *args, **kwargs):
        pass # We're automatic for the people
    def privmsg(self, user, channel, msg):
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self, user, channel, msg, 'privmsg')
            logging.info(req)
            self.dispatch(req).addErrback(terrible_error, self, req)
        else:
            self.hostmask = user.split('!', 1)[1]
    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self, user, channel, msg, 'action')
            self.dispatch(req)
    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        #self.who(channel)
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        if self.nickname not in (old_nick, new_nick):
            req = IRCRequest(self, old_nick, '', new_nick, 'nick')
            self.dispatch(req)

