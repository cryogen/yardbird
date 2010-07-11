#!/usr/bin/python

from django.utils.encoding import force_unicode
from yardbird.utils.encoding import unicode_fallback

class IRCRequest(object):
    def __init__(self, connection, user, channel, msg, method='privmsg',
            privileged_channels=[], **kwargs):
        self.my_nick = connection.nickname
        self.chanmodes = connection.chanmodes
        self.user = user
        if '!' in user:
            self.nick, self.mask = user.split('!', 1)
        else: # pragma: nocover
            self.nick, self.mask = user, None
        self.channel = force_unicode(channel)
        self.privileged_channels = [force_unicode(x) for x in
                privileged_channels]
        self.message = unicode_fallback(msg)
        self.method = method.upper()
        self.context = kwargs
        self.addressee = ''
        if self.channel == self.my_nick:
            self.addressed = True
            self.reply_recipient = self.nick
        elif self.message.lower().startswith(self.my_nick.lower()):
            self.addressed = True
            self.reply_recipient = self.channel
            self.addressee = self.nick
        else:
            self.addressed = False
            self.reply_recipient = self.channel
    def __unicode__(self): # pragma: nocover
        return u'%s: <%s> %s' % (self.channel, self.user, self.message)
    def __str__(self): # pragma: nocover
        return self.__unicode__()


class IRCResponse(object):
    def __init__(self, recipient, data, method='PRIVMSG',
                 **kwargs):
        self.recipient = force_unicode(recipient)
        self.data = force_unicode(data)
        self.method = method
        self.context = kwargs
    def __unicode__(self): # pragma: nocover
        return u'%s: <%s> %s' % (self.method, self.recipient, self.data)
    def __str__(self): # pragma: nocover
        return self.__unicode__()
