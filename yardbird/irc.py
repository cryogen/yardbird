#!/usr/bin/python

from django.utils.encoding import force_unicode

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
        if self.channel == self.my_nick:
            self.addressed = True
            self.reply_recipient = self.nick
        elif self.my_nick.lower() in self.message.lower():
            self.addressed = True
            self.reply_recipient = self.channel
        else:
            self.addressed = False
            self.reply_recipient = self.channel
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
