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
from yardbird.signals import request_started, request_finished
from django.conf import settings
from django.core import urlresolvers
from django.test import signals
from django.test.client import store_rendered_templates
from django.utils.functional import curry
from django.test.testcases import to_list

class TestResponse(IRCResponse):
    """
    This is a rough parallel to the core django testing Response object.
    """
    def __init__(self, response, request, client, opts):
        self.request = request
        self.client = client
        self.recipient = response.recipient.encode('utf-8')
        self.content = response.data.encode('utf-8')
        self.method = response.method
        self.opts = opts
        self.template = []
        self._charset = 'utf-8' # It's the Network Byte Order of
                                # charsets.  Deal with it.
    def __unicode__(self):
        self.template_names = [t.name for t in to_list(self.template)]
        fmt = u'%(method)s: %(template_names)s %(content)s -> '
        fmt += u'%(recipient)s' 
        return fmt % self.__dict__


class MockSignalSender(list):
    """This is meant to be used as the sender= parameter for django
    signals. This way, the signal handlers that expect to get a bot
    object can call sender.notice('message') and it will be queued up
    for later analysis."""
    def drain(self):
        self[:] = []
    def get_event(self):
        return self.pop(0)
    def __call__(self, *args, **kwargs):
        self.append((args, kwargs))
    def __getattr__(self, attr):
        def f(*args, **kwargs):
            return self(attr, *args, **kwargs)
        return f

class Client(object):
    """
    A class that can act as a client for testing purposes.
    """
    def __init__(self, user='TestUser!testuser@localhost',
            bot='TestBot!testbot@localhost', chanmodes=(), **defaults):
        self.defaults = defaults
        self.mask = user
        self.my_nickname, self.my_hostmask = user.split('!', 1)
        self.nickname, self.hostmask = bot.split('!', 1)
        self.chanmodes = dict(chanmodes)
        self.privileged_channels = []
        self.signal_sender = MockSignalSender()
        if 'ROOT_MSGCONF' in self.defaults:
            self.ROOT_MSGCONF = self.defaults['ROOT_MSGCONF']
        else:
            self.ROOT_MSGCONF = settings.ROOT_MSGCONF

    def join(self, channel):
        if channel.lower() not in self.chanmodes:
            self.chanmodes[channel.lower()] = {}
        self.chanmodes[channel.lower()][self.my_hostmask] = 'H'
    def part(self, channel):
        del(self.chanmodes[channel.lower()][self.my_hostmask])

    def op(self, hostmask, channel, mode='@'):
        channel = self.chanmodes[channel.lower()]
        if mode not in channel[hostmask]:
            channel[hostmask] += mode
    def deop(self, hostmask, channel, mode='@'):
        channel = self.chanmodes[channel.lower()]
        if mode in channel[hostmask]:
            channel[hostmask] = channel[hostmask].replace(mode, '')

    def _dispatch(self, request):
        urlresolvers.clear_url_caches()
        resolver = urlresolvers.get_resolver('.'.join(
            (self.ROOT_MSGCONF, request.method.lower())))
        callback, args, kwargs = resolver.resolve('/' + request.message)
        request_started.send(sender=self.signal_sender, request=request)
        response = callback(request, *args, **kwargs)
        request_finished.send(sender=self.signal_sender,
                request=request, response=response)
        return response

    def _send_event(self, user, recipient, message, method):
        data = {}
        on_template_render = curry(store_rendered_templates, data)
        signals.template_rendered.connect(on_template_render)

        request = IRCRequest(self, user, recipient, message, method,
                privileged_channels=self.privileged_channels)
        response = self._dispatch(request)
        opts = {}
        if response.method == 'PRIVMSG':
            opts['length'] = 510 - len(':! PRIVMSG  :' + self.nickname +
                    response.recipient.encode('utf-8') + self.hostmask)

        # Add any rendered template detail to the response.
        # If there was only one template rendered (the most likely case),
        # flatten the list to a single element.
        response = TestResponse(response, request, self, opts)
        for detail in ('template', 'context'):
            if data.get(detail):
                if len(data[detail]) == 1:
                    setattr(response, detail, data[detail][0]);
                else:
                    setattr(response, detail, data[detail])
            else:
                setattr(response, detail, None)
        return response

    def msg(self, recipient, message):
        return self._send_event(self.mask, recipient, message,
                'privmsg')
    def me(self, recipient, message):
        return self._send_event(self.mask, recipient, message,
                'action')
    def topic(self, channel, topic):
        return self._send_event(self.mask, channel, topic,
                'topic')
    def nick(self, channel, new_nick):
        return self._send_event(self.mask, channel, new_nick,
                'nick')
