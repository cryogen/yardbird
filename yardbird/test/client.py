"""
response = client.nick('TestClient1')
response = client.join('#testchannel')
response = client.msg('gubble gubble frink and stubble')
response = client.action('hurgs the burg')
response = client.get('Internet')

...etc

We will not allow errbacks to catch anything, and we're not forking off
threads.  This will need to be more of a raw dispatch.

Our TestCase subclass will need to make one of these as self.client.
We'll also need to make some dummy channel logic (join of new channel
means oplist for that channel, plus explicit op/deop commands to diddle
bot's status structures) """

from yardbird.irc import IRCRequest, IRCResponse
from django.conf import settings
from django.test import signals
from django.core import urlresolvers

class TestResponse(IRCResponse):
    """
    This is a rough parallel to the core django testing Response object.
    Unfortunately because we render templates so early in the process
    (something that will need revisiting), we are unable to return any
    template/context info.
    """
    def __init__(self, response, request, client, opts):
        self.request = request
        self.client = client
        self.recipient = response.recipient.encode('utf-8')
        self.content = response.data.encode('utf-8')
        self.data = self.content # historic for __unicode__()
        self.method = response.method
        self.context = response.context
        self.opts = opts

class Client(object):
    """
    A class that can act as a client for testing purposes.
    """
    def __init__(self, nick='TestUser', hostmask='test@localhost',
            chanmodes=None, **defaults):
        self.defaults = defaults
        self.nickname = nick
        self.hostmask = hostmask
        self.mask = '!'.join(self.nickname, self.hostmask)
        self.chanmodes = dict(chanmodes)
        if 'ROOT_MSGCONF' in self.defaults:
            self.ROOT_MSGCONF = self.defaults['ROOT_MSGCONF']
        else:
            self.ROOT_MSGCONF = settings.ROOT_MSGCONF

    def join(self, channel):
        self.chanmodes[channel.lower()][self.hostmask] = 'H'
    def part(self, channel):
        del(self.chanmodes[channel.lower()][self.hostmask])

    def op(self, hostmask, channel, mode='@'):
        channel = self.chanmodes[channel.lower()]
        if mode not in channel[hostmask]:
            channel[hostmask] += mode
    def deop(self, hostmask, channel, mode='@'):
        channel = self.chanmodes[channel.lower()]
        if mode not in channel[hostmask]:
            channel[hostmask] = channel[hostmask].replace(mode, '')

    def _dispatch(self, request):
        resolver = urlresolvers.get_resolver('.'.join(
            (self.ROOT_MSGCONF, request.method.lower())))
        callback, args, kwargs = resolver.resolve('/' + req.message)
        #request_started.send(sender=self, request=request)
        response = callback(request, *args, **kwargs)
        #request_finished.send(sender=self, request=request, response=response)
        return response

    def _send_event(self, user, recipient, message, method):
        request = IRCRequest(self, user, recipient, msg, method,
                privileged_channels=self.chanmodes)
        response = self._dispatch(request)
        opts = {}
        if response.method == 'PRIVMSG':
            opts['length'] = 510 - len(':! PRIVMSG  :' + self.nickname +
                    response.recipient.encode('utf-8') + self.hostmask)
        return TestResponse(response, request, self, opts)

    def msg(self, recipient, message):
        return self._send_event(self.nickname, recipient, message,
                'privmsg')
    def me(self, recipient, message):
        return self._send_event(self.nickname, recipient, message,
                'action')
    def topic(self, channel, topic):
        return self._send_event(self.nickname, channel, topic,
                'topic')
    def nick(self, channel, new_nick):
        return self._send_event(self.nickname, channel, new_nick,
                'nick')
