import mox

from django.http import Http404
from django.core import exceptions

from yardbird.test import TestCase

import yardbird.bot
import yardbird.irc
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
        from twisted.internet import ssl, defer
        from twisted.python import failure
        yardbird.bot.log = self.mox.CreateMock(logging._loggerClass)
        self.bogus_deferred = self.mox.CreateMock(defer.Deferred)
        self.bogus_failure = self.mox.CreateMock(failure.Failure)

        self.bot = yardbird.bot.DjangoBot()
        self.mox.StubOutWithMock(self.bot, "sendLine")
        self.mox.StubOutWithMock(self.bot, "dispatch")
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
        mask = '%s!%s@example.com' % (self.bot.nickname, self.bot.nickname)
        msg = 'Watching for my own hostmask'

        self.bot.sendLine('PRIVMSG %s :%s' % (self.bot.nickname, msg))
        for chan in self.bot.factory.channels:
            self.bot.sendLine('JOIN %s' % chan)
        self.mox.ReplayAll()

        self.bot.signedOn()
        self.bot.privmsg(mask, mask, msg)
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
        msg = 'What is real?'

        yardbird.bot.log.info(u'%s: <%s> %s' % (chan, nick, msg))
        self.bot.dispatch(mox.IsA(yardbird.irc.IRCRequest)
                ).AndReturn(self.bogus_deferred)
        self.bogus_deferred.addErrback(yardbird.bot.report_error,
                self.bot, mox.IsA(yardbird.irc.IRCRequest)
                ).AndReturn(self.bogus_deferred)
        self.bogus_deferred.addErrback(yardbird.bot.unrecoverable_error,
                self.bot, mox.IsA(yardbird.irc.IRCRequest)
                ).AndReturn(self.bogus_deferred)
        self.mox.ReplayAll()

        d = self.bot.action(nick, chan, msg)
    def test_404(self):
        nick = 'SpaceHobo'
        chan = '#yardbird'
        msg = '%s: What is real?' % self.bot.nickname

        self.bogus_failure.trap(Http404, exceptions.PermissionDenied,
                exceptions.ValidationError).AndReturn(Http404)
        yardbird.bot.log.debug(self.bogus_failure)
        self.bot.sendLine("PRIVMSG %s :I don't know what you mean, %s."
                % (chan, nick))
        self.mox.ReplayAll()

        yardbird.bot.report_error(self.bogus_failure, self.bot,
                yardbird.irc.IRCRequest(self.bot, nick, chan, msg,
                'privmsg'))
    def test_unaddressed_404(self):
        nick = 'SpaceHobo'
        chan = '#yardbird'
        msg = 'What is real?'

        self.bogus_failure.trap(Http404, exceptions.PermissionDenied,
                exceptions.ValidationError).AndReturn(Http404)
        yardbird.bot.log.debug(self.bogus_failure)
        self.mox.ReplayAll()

        yardbird.bot.report_error(self.bogus_failure, self.bot,
                yardbird.irc.IRCRequest(self.bot, nick, chan, msg,
                'privmsg'))
    def test_403(self):
        nick = 'SpaceHobo'
        chan = '#yardbird'
        msg = '%s: delete the Internet!' % self.bot.nickname

        self.bogus_failure.trap(Http404, exceptions.PermissionDenied,
                exceptions.ValidationError
                ).AndReturn(exceptions.PermissionDenied)
        yardbird.bot.log.debug(self.bogus_failure)
        self.bot.sendLine("PRIVMSG %s :Sorry, %s." % (chan, nick))
        self.mox.ReplayAll()

        yardbird.bot.report_error(self.bogus_failure, self.bot,
                yardbird.irc.IRCRequest(self.bot, nick, chan, msg,
                'privmsg'))
    def test_unrecoverable_error(self):
        nick = 'SpaceHobo'
        chan = '#yardbird'
        msg = '%s: delete the Internet!' % self.bot.nickname

        yardbird.bot.log.warn(self.bogus_failure)
        self.bogus_failure.getErrorMessage().AndReturn('INTERNET DELETED!')
        self.bot.sendLine("NOTICE %s :INTERNET DELETED!" % chan)
        self.mox.ReplayAll()

        yardbird.bot.unrecoverable_error(self.bogus_failure, self.bot,
                yardbird.irc.IRCRequest(self.bot, nick, chan, msg,
                'privmsg'))



