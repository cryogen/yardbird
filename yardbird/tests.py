import mox

from django.http import Http404
from django.core import exceptions
from django.conf import settings

from yardbird.test import TestCase

import yardbird.bot
from yardbird.irc import IRCResponse
from yardbird.contrib import shortener

from yardbird.utils import encoding
from django.utils.encoding import DjangoUnicodeDecodeError


# Override settings that might cause trouble if set to something unexpected
settings.IRC_INPUT_ENCODINGS = ['utf-8', 'cp1252']

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
        """ We manually stub out the two twisted methods that were used
        to defer/multi-thread execution, causing flow to execute
        sequentially.  The logging and protocol send functions are
        mocked for our test verification, and we make a bogus factory
        object to communicate the test bot object's settings. Finally we
        mock out all possible Twisted features that would cause
        concurrency."""
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

class DjangoBotConnectionTestCase(DjangoBotIrcTestCase):
    """Test Case for initial setup/tear-down of irc connections"""
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
    def test_connectionLost(self):
        msg = 'The end. No moral!'
        yardbird.bot.log.warn('Disconnected from %s (%s:%d): %s' %
                (self.bot.servername, self.bot.factory.hostname,
                    self.bot.factory.port, msg))
        self.mox.ReplayAll()

        self.bot.connectionLost(msg)
        self.assertEqual(self.bot.connected, 0,
                'Bot did not notice loss of connection')

class DjangoBotChannelModesListTestCase(DjangoBotIrcTestCase):
    """Tests of the bot.chanmodes dict, and events that update it."""
    def test_whoreplies(self):
        me = self.bot.factory.nickname
        chan = '#yardbird'

        self.bot.sendLine('WHO %s' % chan)
        self.mox.ReplayAll()

        self.bot.userJoined('Spacehobo', chan)
        self.bot.irc_RPL_WHOREPLY('foo', (me, chan, '~' + me,
            'server.example.com', 'irc.example.com', me,
            'H', self.bot.realname))
        self.bot.irc_RPL_WHOREPLY('foo', (me, chan,
            '~spacehobo', 'laptop.example.com', 'irc.example.com',
            'SpaceHobo', 'Hr@', 'Space Hobo, esq.' ))
        self.bot.irc_RPL_ENDOFWHO('foo', (me, chan))

        yardmodes = self.bot.chanmodes['#yardbird']
        self.assertEqual('Hr@',
                yardmodes['~spacehobo@laptop.example.com'],
                'SpaceHobo not listed as chanop in bot.chanmodes.')
        self.assertEqual('H',
                yardmodes['~testbot@server.example.com'],
                'yardbird bot not listed as user in bot.chanmodes.')
    def test_nick_change(self):
        old = 'SpaceHobo!~spacehobo@laptop.example.com'
        new = ['BindleStiff']
        yardmodes = {'~spacehobo@laptop.example.com': 'Hr@',
                '~testbot@server.example.com': 'H'}
        self.bot.chanmodes['#yardbird'] = yardmodes

        yardbird.bot.log.info(u'#yardbird: <%s> %s' % (old, new[0]))
        self.bot.dispatch(mox.IsA(yardbird.irc.IRCRequest)
                ).AndReturn(self.bogus_deferred)
        self.bogus_deferred.addErrback(yardbird.bot.report_error,
                self.bot, mox.IsA(yardbird.irc.IRCRequest)
                ).AndReturn(self.bogus_deferred)
        self.bogus_deferred.addErrback(yardbird.bot.unrecoverable_error,
                self.bot, mox.IsA(yardbird.irc.IRCRequest)
                ).AndReturn(self.bogus_deferred)
        self.mox.ReplayAll()

        self.bot.irc_NICK(old, new)
    def test_quit(self):
        yardmodes = {'~spacehobo@laptop.example.com': 'Hr@',
                '~testbot@server.example.com': 'H'}
        self.bot.chanmodes['#yardbird'] = yardmodes
        self.mox.ReplayAll()

        self.assertTrue('~spacehobo@laptop.example.com' in
                self.bot.chanmodes['#yardbird'])
        self.bot.irc_QUIT('SpaceHobo!~spacehobo@laptop.example.com',
                'Goodbye.')
        self.assertFalse('~spacehobo@laptop.example.com' in
                self.bot.chanmodes['#yardbird'])

class DjangoBotDispatcherTestCase(DjangoBotIrcTestCase):
    """Test Case for events that dispatch Django views, and the
    associated error handlers."""
    def test_noticed(self):
        """The bot should never react to NOTICE events"""
        self.mox.ReplayAll()
        self.bot.noticed('whatever')
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
    def test_topicUpdated(self):
        nick = 'SpaceHobo'
        chan = '#yardbird'
        msg = 'My name is a kissing word'

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

        d = self.bot.topicUpdated(nick, chan, msg)


class DjangoBotMultiResponseObjsTestCase(DjangoBotIrcTestCase):
    """Test the MULTIPLE response type"""
    def test_multiple_response(self):
        responses = []
        responses.append(IRCResponse('emad', 'whoa nelly!'))
        responses.append(IRCResponse('#wut', 'APPLY TOPICALLY',
            method='TOPIC'))
        response = IRCResponse('', '', responses=responses,
                method='MULTIPLE')

        self.bot.sendLine('PRIVMSG emad :whoa nelly!')
        self.bot.sendLine('TOPIC #wut :APPLY TOPICALLY')
        self.mox.ReplayAll()
        self.bot.methods[response.method](
                response.recipient.encode('utf-8'),
                response.data.encode('utf-8'),
                responses=response.responses)


class DjangoBotMiscellaneousHacksTestCase(DjangoBotIrcTestCase):
    def test_me(self):
        """We provide our own /me function to work around encoding
        problems in the core twisted version."""
        self.bot.sendLine('PRIVMSG #yardbird :\001ACTION \\o/\001')
        self.mox.ReplayAll()
        self.bot.me('#yardbird', '\\o/')

class DjangoBotReloadTestCase(DjangoBotIrcTestCase):
    """Reload is destructive enough that it un-mocks everything we've
    painstakingly faked out.  So it gets its own TestCase."""
    def test_reload(self):
        chan = '#yardbird'
        msg = 'Reload successful'
        notice = 'NOTICE %s :%s' % (chan, msg)

        self.bot.sendLine(notice)
        # XXX: need to verify that our mocks are replaced with the real thing

        self.mox.ReplayAll()

        self.bot.reimport(chan, msg)

class DjangoBotAutoDecodeTestCase(TestCase):
    """Test a boatload of various conversions to and from different
    encodings"""
    def setUp(self):
        # Set encodings to make sure we know what's going on
        self.std_enc = ['utf_8', 'cp1252']

    def test_ascii_unchanged(self):
        self.assertEqual(encoding.force_unicode(
            "abc", encodings=self.std_enc), u'abc')

    def test_conversion(self):
        self.assertEqual(encoding.force_unicode(
            "\xC6", encodings=self.std_enc), "\xc3\x86".decode('utf-8'))
        self.assertRaises(DjangoUnicodeDecodeError,
                encoding.force_unicode, "\x9D", encodings=self.std_enc)

    def test_cp1252_latin9_differ(self):
        # CP1252 and ISO8859-15 differ slightly
        self.assertNotEqual(
                encoding.force_unicode("\xA4", encodings=self.std_enc),
                encoding.force_unicode("\xA4", encodings=['iso8859-15']))

    def test_cp1252_latin9_equal(self):
        # CP1252 and ISO8859-1 on the other hand are identical here
        self.assertEqual(
                encoding.force_unicode("\xA4", encodings=self.std_enc),
                encoding.force_unicode("\xA4", encodings=['iso8859-1']))

    def test_ruscii(self):
        # Now let's try some ruscii
        self.assertEqual(
                encoding.force_unicode("\xf2", encodings=['koi8_r']),
                "\xd0\xa0".decode('utf-8'))

    def test_empty_settings(self):
        # If settings.IRC_INPUT_ENCODINGS is empty, we expect an exception
        temp = settings.IRC_INPUT_ENCODINGS
        settings.IRC_INPUT_ENCODINGS = []
        self.assertRaises(ValueError, encoding.force_unicode, "\x83")

        # Set things back
        settings.IRC_INPUT_ENCODINGS = temp

    def test_unicode_object(self):
        # Passing a unicode object should return it unchanged
        snowman = "\xe2\x98\x83".decode('utf-8')
        self.assertEqual(
                encoding.force_unicode(snowman, encodings=['ascii']),
                snowman)

