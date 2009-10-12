from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Starts a Yardbird IRC bot."
    #args = '[optional port number, or ipaddr:port]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = True

    def handle(self, *args, **options):
        import logging
        from django.conf import settings
        from twisted.internet import ssl
        from twisted.internet import reactor, protocol
        from yardbird.bot import DjangoBot, log

        # Configure up the logger
        termlog = logging.StreamHandler()
        termlog.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        termlog.setFormatter(formatter)
        log.addHandler(termlog)

        # SRSLY?  I set up a FACTORY and my bot class is its PROTOCOL and
        # then we pass my FACTORY and ANOTHER FACTORY into a REACTOR to run
        # things.  Is Java responsible for this idiocy, or Heroin?

        for place in settings.IRC_LOCATIONS:
            f = protocol.ReconnectingClientFactory()
            f.protocol = DjangoBot
            f.nickname, f.channels = place['nick'], place['channels']
            hostname, port, is_ssl = place['server']
            if is_ssl:
                reactor.connectSSL(hostname, port, f, ssl.ClientContextFactory())
            else:
                reactor.connectTCP(hostname, port, f)
        reactor.run()

