#!/usr/bin/python

import os

from django.conf import settings

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'

if __name__ == '__main__':
    from twisted.internet import ssl
    from twisted.internet import reactor, protocol
    from yardbird.bot import DjangoBot

    # SRSLY?  I set up a FACTORY and my bot class is its PROTOCOL and
    # then we pass my FACTORY and ANOTHER FACTORY into a REACTOR to run
    # things.  Is Java responsible for this idiocy, or Heroin?

    f = protocol.ReconnectingClientFactory()
    f.protocol = DjangoBot
    f.nickname, f.channels = settings.IRC_NICK, settings.IRC_CHANNELS
    for server in settings.IRC_SERVERS:
        hostname, port = server
        reactor.connectSSL(hostname, port, f, ssl.ClientContextFactory())
    reactor.run()

