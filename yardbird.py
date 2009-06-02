#!/usr/bin/python
import time
import os
import re

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer, threads, task
from django.core import urlresolvers
from django.utils.encoding import force_unicode
from django.conf import settings
from django.template.loader import render_to_string
import logging

import logging.handlers

LOG_FILENAME = '/tmp/yardbird.log'

# Set up a specific logger with our desired output level
yardlogger = logging.getLogger('YardLogger')
yardlogger.setLevel(logging.DEBUG)
# Add the log message handler to the logger
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, 'm', 10)
yardlogger.addHandler(handler)


if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'


class IRCRequest(object):
    def __init__(self, connection, user, channel, msg, method='privmsg',
                 **kwargs):
        self.my_nick = connection.nickname
        self.chanmodes = connection.chanmodes
        self.user = user
        self.nick = user.split('!', 1)[0]
        self.channel = channel
        self.message = force_unicode(msg)
        self.method = method.upper()
        self.context = kwargs
        self.addressed = False
        if self.channel == self.my_nick or self.my_nick in self.message:
            self.addressed = True
            self.reply_recipient = self.nick
        else:
            self.reply_recipient = self.channel

    def __str__(self):
        s = u'%s: <%s> %s' % (self.channel, self.user, self.message)
        return s.encode('utf-8')

def render_to_response(recipient, template_name, dictionary={},
                       context_instance=None, method='PRIVMSG'):
    text = render_to_string(template_name, dictionary, context_instance)
    dictionary['method'] = method
    return IRCResponse(recipient, text, **dictionary)

def render_to_reply(request, template_name, dictionary={},
                    context_instance=None):
    if request.channel != request.my_nick:
        recipient = request.channel
    else:
        recipient = request.nick
    return render_to_response(recipient, template_name, dictionary,
                              context_instance, request.method)

def render_silence(*args, **kwargs):
    return IRCResponse('', '', 'QUIET')

def render_quick_reply(request, template_name, dictionary={}):
    dictionary.update(request.__dict__)
    if request.channel != request.nick:
        recipient = request.channel
    else:
        recipient = request.nick
    return render_to_response(recipient, template_name, dictionary)

def render_error(request, msg):
    return IRCResponse(request.nick, msg, method='NOTICE')

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
    recipient = request.user.split('!', 1)[0]
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
        irc.IRCClient.connectionMade(self)
        self.l = task.LoopingCall(self.PING)
        self.l.start(60.0) # call every minute
        print("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.l.stop() # All done now.
        print("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
    def signedOn(self):
        self.msg(self.nickname, 'Watching for my own hostmask')
        for channel in self.factory.channels:
            self.join(channel)
    def joined(self, channel):
        print("[I have joined %s]" % channel)
        self.who(channel)
        self.msg(channel, 'what up, meatbags')

    def PING(self):
        print 'PING %s' % self.servername
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
            yardlogger.info(response)
            defer.returnValue(True)
        elif response.method == 'PRIVMSG':
            opts = {'length':
                    510 - len(':! PRIVMSG  :' + self.nickname +
                              response.recipient + self.hostmask)}
            yardlogger.info(response)
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
            yardlogger.info(req)
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
        self.who(channel)
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        if self.nickname not in (old_nick, new_nick):
            req = IRCRequest(self, old_nick, '', new_nick, 'nick')
            self.dispatch(req)


if __name__ == '__main__':
    import sys
    from twisted.internet import ssl

    # SRSLY?  I set up a FACTORY and my bot class is its PROTOCOL and
    # then we pass my FACTORY and ANOTHER FACTORY into a REACTOR to run
    # things.  Is Java responsible for this idiocy, or Heroin?

    f = protocol.ReconnectingClientFactory()
    f.protocol = DjangoBot
    f.nickname, f.channels = settings.IRC_NICK, settings.IRC_CHANNELS
    reactor.connectSSL("irc.slashnet.org", 6697, f,
                       ssl.ClientContextFactory())
    reactor.run()

