from django.core.management.base import BaseCommand, CommandError
import urlparse

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

        # Parse the connection URIs into a dict
        # First we need to beat urlparse into submission
        for scheme in ("irc", "ircs"):
            urlparse.uses_netloc.append(scheme)
            urlparse.uses_query.append(scheme)
            urlparse.uses_params.append(scheme)

        connections = {}
        for uri in settings.IRC_CHANNELS:
            p = urlparse.urlparse(uri, 'irc')
            if p.port == None:
                port = 6667
            else:
                port = p.port
            key = (p.hostname, port)

            if key not in connections:
                connections[key] = {
                        'scheme':'',
                        'nick':'',
                        'password':'',
                        'hostname':p.hostname,
                        'port':port,
                        'channels':[],
                        'privileged_channels':[],
                }

            for (urielem, irc) in (('username', 'nick'), ('password', 'password'), ('scheme', 'scheme')):
                try:
                    value = p.__getattribute__(urielem)
                    if value == None:
                        continue
                    if connections[key][irc] != '' and connections[key][irc] != value:
                        print("WARNING - Overwriting value '%s'='%s' with '%s'" % (irc, connections[key][irc], value))
                    connections[key][irc] = value
                except AttributeError:
                    pass

            path = p.path.split("/")[1:]
            if len(path) == 2 and path[0] == "privileged":
                connections[key]['privileged_channels'].append(path[1])
                path.pop(0)
            connections[key]['channels'].append(path.pop())

        # SRSLY?  I set up a FACTORY and my bot class is its PROTOCOL and
        # then we pass my FACTORY and ANOTHER FACTORY into a REACTOR to run
        # things.  Is Java responsible for this idiocy, or Heroin?

        for key, connection in connections.iteritems():
            if connection['nick'] == '':
                raise Exception, "No nick set for %s" % key
            f = protocol.ReconnectingClientFactory()
            f.protocol = DjangoBot
            f.protocol.password = connection['password']

            f.nickname = connection['nick']
            f.channels = connection['channels']
            f.privchans = connection['privileged_channels']
            hostname = connection['hostname']
            port = connection['port']
            scheme = connection['scheme']
            if scheme == "ircs":
                reactor.connectSSL(hostname, port, f, ssl.ClientContextFactory())
            else:
                reactor.connectTCP(hostname, port, f)
        reactor.run()

