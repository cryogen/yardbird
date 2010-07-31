import mox
from twisted import trial

from yardbird.test import TestCase

import yardbird.bot
from yardbird.contrib import shortener


class ShortenerTestCase(TestCase):
    def test_encoder(self):
        self.assertEqual(shortener.encode64(242), 'cN')
        self.assertEqual(shortener.encode64(24242), 'eVN')
    def test_decoder(self):
        self.assertEqual(shortener.decode64('.'), 0)
        self.assertEqual(shortener.decode64('emad'), 1364036)
    def test_consistency(self):
        for i in xrange(0, 5000):
            self.assertEqual(shortener.decode64(shortener.encode64(i)), i)

class TestCaseTestCase(TestCase):
    """This is actually meant to exercise the TestCase object itself"""
    msgconf='example'
    def test_unsupported(self):
        self.assertRaises(NotImplementedError, self.assertRedirects)
        self.assertRaises(NotImplementedError, self.assertFormError)
    def test_assertions(self):
        response = self.client.msg(self.client.nickname,
                                '242 is an auspicious number')
        self.assertTemplateUsed(response, 'ack.irc')
        self.assertContains(response, "Roger that", method='PRIVMSG')
        self.assertContains(response, "Roger that", method='PRIVMSG',
                count=1)
        self.assertNotContains(response, "sandwiches", method='PRIVMSG')

class DjangoBotIrcTestCase(mox.MoxTestBase):
    """Use mocks to test the IRC activity of the bot object."""
    def setUp(self):
        """This test case's setup includes a heavily stubbed-out
        DjangoBot object.  We manually stub out the two twisted methods
        that were used to defer/multi-thread execution, causing flow to
        execute sequentially.  The logging and protocol send functions
        are mocked for our test verification, and we make a bogus
        factory object to communicate the test bot object's settings."""
        super(DjangoBotIrcTestCase, self).setUp()
        import logging
        from twisted.internet import ssl
        yardbird.bot.defer.inlineCallbacks = lambda f,a,k: list(f(*a,**k))
        yardbird.bot.threads.deferToThread = lambda f,r,a,k: f(r,a,k)
        yardbird.bot.log = self.mox.CreateMock(logging._loggerClass)
        self.bot = yardbird.bot.DjangoBot()
        self.mox.StubOutWithMock(self.bot, "sendLine")
        self.bot.factory = self.mox.CreateMock(
                ssl.DefaultOpenSSLContextFactory)
        self.bot.factory.protocol = yardbird.bot.DjangoBot
        self.bot.factory.password = 'secret'
        self.bot.factory.nickname = 'testbot'
        self.bot.factory.channels = ('#yardbird', '#testing')
        self.bot.factory.privchans = ('#yardbird',)
        self.bot.factory.hostname = 'irc.example.com'
        self.bot.factory.port = 6667
    def test_myInfo(self):
        servername = 'testsvr'
        yardbird.bot.log.info("Connected to %s" % servername)
        yardbird.bot.log.debug('PING %s' % servername)
        self.bot.sendLine('PING %s' % servername)
        self.mox.ReplayAll()

        self.bot.myInfo(servername, 'mockirc', 'hostname', 'servername')
    def test_connectionMade(self):
        self.bot.sendLine('PASS %s' % self.bot.factory.password)
        self.bot.sendLine('NICK %s' % self.bot.factory.nickname)
        self.bot.sendLine('USER %s foo bar :%s' %
                (self.bot.factory.nickname, self.bot.realname))
        self.mox.ReplayAll()

        self.bot.connectionMade()
    def test_signedOn(self):
        self.bot.sendLine('PRIVMSG %s :Watching for my own hostmask' %
                self.bot.nickname)
        for chan in self.bot.factory.channels:
            self.bot.sendLine('JOIN %s' % chan)
        self.mox.ReplayAll()

        self.bot.signedOn()
    def test_ping(self):
        self.bot.sendLine('PONG AA4B4873')
        self.mox.ReplayAll()

        self.bot.lineReceived('PING :AA4B4873')
    def test_joined(self):
        for chan in self.bot.factory.channels:
            yardbird.bot.log.info("[I have joined %s]" % chan)
            self.bot.sendLine('WHO %s' % chan)
        self.mox.ReplayAll()

        for chan in self.bot.factory.channels:
            self.bot.joined(chan)
    def test_noticed(self):
        self.bot.noticed('whatever')
        self.mox.ReplayAll()
    def test_connectionLost(self):
        msg = 'The end. No moral!'
        yardbird.bot.log.warn('Disconnected from %s (%s:%d): %s' %
                (self.bot.servername, self.bot.factory.hostname,
                    self.bot.factory.port, msg))
        self.mox.ReplayAll()

        self.bot.connectionLost(msg)
        self.assertEqual(self.bot.connected, 0,
                'Bot did not notice loss of connection')
    def test_defer(self):
        nick = 'SpaceHobo'
        chan = '#yardbird'
        msg = 'stats'
        reply = 'You must address me to perform this operation.'

        yardbird.bot.log.info(u'%s: <%s> %s' % (chan, nick, msg))
        yardbird.bot.log.info(u'NOTICE: <%s> %s' % (nick, reply))
        self.bot.sendLine('NOTICE %s :%s' % (nick, reply))
        self.mox.ReplayAll()

        self.bot.privmsg(nick, chan, msg)

