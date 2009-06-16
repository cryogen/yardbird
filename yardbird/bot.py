#!/usr/bin/python
import logging

from twisted.words.protocols.irc import IRCClient
from twisted.internet import defer, threads, task
from django.core import urlresolvers
from django.conf import settings

from irc import IRCRequest, IRCResponse
from signals import request_started, request_finished

log = logging.getLogger('yardbird')
log.setLevel(logging.DEBUG)

def terrible_error(failure, bot, request, *args, **kwargs):
    def reply(bot, request, message, *args, **kwargs):
        recipient = request.reply_recipient
        res = IRCResponse(recipient, message % kwargs, method='NOTICE')
        return bot.methods[res.method](res.recipient, res.data.encode('utf-8'))
    log.warn(failure)
    e = str(failure.getErrorMessage())
    if 'path' in e and 'tried' in e:
        return reply(bot, request, 'Dude?')
    return reply(bot, request, u'Dude! %s' % e)

class DjangoBot(IRCClient):
    def __init__(self):
        self.methods = {'PRIVMSG':  self.msg,
                        'ACTION':   self.me,
                        'NOTICE':   self.notice,
                        'TOPIC':    self.topic,
                        'RESET':    self.reimport,
                       }
        self.chanmodes = {}
        self.whoreplies = {}
        self.hostmask = '' # until we see ourselves speak, we do not know
        self.servername = ''
        self.lineRate = 1

        self.versionName = 'Yardbird'
        self.versionNum = 'Ah-Leu-Cha'
        self.versionEnv = 'Django'
        self.sourceURL = 'http://zork.net/~nick/yardbird/ '
        self.realname = 'Charlie Parker Jr.'
        self.fingerReply = 'Trollabye in Birdland'

    def myInfo(self, servername, version, umodes, cmodes):
        self.servername = servername
        log.info("Connected to %s" % self.servername)
        self.l = task.LoopingCall(self.PING)
        self.l.start(60.0) # call every minute
    def connectionMade(self):
        self.nickname = self.factory.nickname
        IRCClient.connectionMade(self)
    def connectionLost(self, reason):
        IRCClient.connectionLost(self, reason)
        self.l.stop() # All done now.
        log.warn("Disconnected from %s" % self.servername)
    def signedOn(self):
        self.msg(self.nickname, 'Watching for my own hostmask')
        for channel in self.factory.channels:
            self.join(channel)
    def joined(self, channel):
        log.info("[I have joined %s]" % channel)
        self.who(channel)
        self.msg(channel, 'what up, meatbags')
    def PING(self):
        log.debug('PING %s' % self.servername)
        self.sendLine('PING %s' % self.servername)

    def who(self, channel):
        self.whoreplies[channel.lower()] = {}
        self.sendLine('WHO %s' % channel.lower())
    def irc_RPL_WHOREPLY(self, prefix, args):
        me, chan, uname, host, server, nick, modes, name = args
        mask = '%s@%s' % (uname, host)
        self.whoreplies[chan.lower()][mask] = modes
    def irc_RPL_ENDOFWHO(self, prefix, args):
        channel = args[1].lower()
        self.chanmodes[channel] = self.whoreplies[channel]
    def invalidate_chanmodes(self, user, channel, *args, **kwargs):
        """Some functions just need to get a new listing of users and
        mode flags"""
        self.who(channel)
    modeChanged = invalidate_chanmodes
    userJoined = invalidate_chanmodes
    userLeft = invalidate_chanmodes

    def userKicked(self, kickee, channel, kicker, message):
        channel = channel.lower()
        nick, mask = kickee.split('!', 1)
        kicker_nick, kicker_mask = kicker.split('!', 1)
        # Remove the kickee from our chanmodes dictionaries
        if mask in self.chanmodes[channel]:
            del(self.chanmodes[channel][mask])
        if self.nickname not in (nick, kicker_nick):
            req = IRCRequest(self, kicker_nick, channel, message,
                             'kick', kickee=kickee)
            self.dispatch(req)

    def userQuit(self, user, message):
        mask = user.split('!', 1)[1]
        for channel in self.chanmodes:
            if mask in self.chanmodes[channel]:
                del(self.chanmodes[channel][mask])

    @defer.inlineCallbacks
    def dispatch(self, req):
        """This method abuses the django url resolver to detect
        interesting messages and dispatch them to callback functions
        based on regular expression matches."""
        def asynchronous_work(request, args, kwargs):
            """This function runs in a separate thread, as the signal
            handlers and callback functions may take forever and a day
            to execute."""
            request_started.send(sender=self, request=request)
            response = callback(req, *args, **kwargs)
            request_finished.send(sender=self, request=request,
                                  response=response)
            return response

        resolver = urlresolvers.get_resolver('.'.join(
            (settings.ROOT_MSGCONF, req.method.lower())))
        callback, args, kwargs = yield resolver.resolve('/' + req.message)
        response = yield threads.deferToThread(asynchronous_work, req,
                                               args, kwargs)
        if response.method == 'QUIET':
            log.debug(response)
            defer.returnValue(True)
        elif response.method == 'PRIVMSG':
            opts = {'length':
                    510 - len(':! PRIVMSG  :' + self.nickname +
                              response.recipient + self.hostmask)}
        else:
            opts = {}
        log.info(unicode(response))
        defer.returnValue(
            self.methods[response.method](response.recipient,
                                          response.data.encode('UTF-8'),
                                          **opts))

    def reimport(self, recipient, data, **kwargs):
        import sys
        for modname, module in sys.modules.iteritems():
            # We reload yardbird library code as well as all known
            # django apps.
            for app in ['yardbird.'] + settings.INSTALLED_APPS:
                if module and modname.startswith(app):
                    reload(module)
                    break # On to next module
        urlresolvers.clear_url_caches() # Drop stale references to apps 
        self.notice(recipient, data)
    def dispatchable_event(self, user, channel, msg, method):
        if user.split('!', 1)[0] != self.nickname:
            req = IRCRequest(self, user, channel, msg, method)
            log.info(unicode(req))
            self.dispatch(req).addErrback(terrible_error, self, req)
        else:
            self.hostmask = user.split('!', 1)[1]

    def noticed(self, *args, **kwargs):
        pass # We're automatic for the people
    def privmsg(self, user, channel, msg):
        return self.dispatchable_event(user, channel, msg, 'privmsg')
    def action(self, user, channel, msg):
        return self.dispatchable_event(user, channel, msg, 'action')
    def topicUpdated(self, user, channel, msg):
        return self.dispatchable_event(user, channel, msg, 'topic')
    def irc_NICK(self, user, params):
        """Called when an IRC user changes their nickname."""
        old_nick, mask = user.split('!', 1)
        new_nick = params[0]
        if self.nickname not in (old_nick, new_nick):
            for channel in self.chanmodes:
                if mask in self.chanmodes[channel]:
                    return self.dispatchable_event(user, channel,
                                                   new_nick, 'nick')

