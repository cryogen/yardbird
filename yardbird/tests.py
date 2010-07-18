import unittest, mock

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

class LineMocker(mock.Mock):
    def assert_line_sent(self, line):
        assert ((line,),{}) in self.call_args_list, \
                'Expected: %s\nCalled with: %s' % (line,
                    self.call_args_list)
    def assert_next_line(self, line):
        assert self.call_args_list[0][0][0] == line, \
                'Expected: %s\nCalled with: %s' % (line,
                    self.call_args_list[0][0][0])
        return self.call_args_list.pop(0)
    def assert_quiet(self):
        assert self.call_args_list == [], \
                '%s called unexpectedly with %s' % (self._name,
                        self.call_args_list[0][0][0])

class DjangoBotIrcTestCase(unittest.TestCase):
    """Use mocks to test the IRC activity of the bot object."""
    def setUp(self):
        yardbird.bot.log = mock.Mock()
        self.bot = yardbird.bot.DjangoBot()
        self.bot.sendLine = LineMocker(name='sendLine')
        self.bot.factory = mock.Mock()
        self.bot.factory.nickname = 'testbot'
        self.bot.factory.password = 'secret'
        self.bot.factory.channels = ('#yardbird', '#testing')
        self.bot.factory.privchans = ('#yardbird',)
        self.bot.sendLine.assert_quiet()
    def test_myInfo(self):
        self.bot.sendLine.assert_quiet()
        self.bot.myInfo('testsvr', 'mockirc', 'foo', 'bar')
        self.bot.sendLine.assert_next_line('PING testsvr')
        self.bot.sendLine.assert_quiet()
    def test_connectionMade(self):
        self.bot.sendLine.assert_quiet()
        self.bot.connectionMade()
        self.bot.sendLine.assert_next_line('PASS %s' %
                self.bot.factory.password)
        self.bot.sendLine.assert_next_line('NICK %s' %
                self.bot.factory.nickname)
        self.bot.sendLine.assert_next_line(
                'USER %s foo bar :%s' % (self.bot.nickname,
                    self.bot.realname))
        self.bot.sendLine.assert_quiet()
    def test_signedOn(self):
        self.bot.sendLine.assert_quiet()
        self.bot.signedOn()
        self.bot.sendLine.assert_next_line(
                'PRIVMSG %s :Watching for my own hostmask' %
                self.bot.nickname)
        self.bot.sendLine.assert_next_line('JOIN #yardbird')
        self.bot.sendLine.assert_next_line('JOIN #testing')
        self.bot.sendLine.assert_quiet()
    def test_ping(self):
        self.bot.sendLine.assert_quiet()
        self.bot.lineReceived('PING :AA4B4873')
        self.bot.sendLine.assert_next_line('PONG AA4B4873')
        self.bot.sendLine.assert_quiet()
    def test_joined(self):
        self.bot.sendLine.assert_quiet()
        self.bot.joined('#yardbird')
        self.bot.sendLine.assert_next_line('WHO #yardbird')
        self.bot.joined('#testing')
        self.bot.sendLine.assert_next_line('WHO #testing')
        self.bot.sendLine.assert_quiet()
    def test_noticed(self):
        self.bot.sendLine.assert_quiet()
        self.bot.noticed('whatever')
        self.bot.sendLine.assert_quiet()
    def test_connectionLost(self):
        self.bot.sendLine.assert_quiet()
        self.bot.connectionLost('The end. No moral!')
        self.assertEqual(self.bot.connected, 0,
                'Bot did not notice loss of connection')
        self.bot.sendLine.assert_quiet()
    #def test_defer(self):
        #self.bot.sendLine.assert_quiet()
        #yardbird.bot.threads.deferToThread = mock.Mock(
                #'twisted.internet.threads.deferToThread')
        #yardbird.bot.defer = mock.Mock('twisted.internet.defer')
        #self.bot.privmsg('SpaceHobo', '#yardbird', 'What is real?')
        #print self.bot.sendLine.call_args_list
        #print yardbird.bot.threads.deferToThread.method_calls, yardbird.bot.threads.deferToThread.call_args_list
        #print yardbird.bot.defer.method_calls, yardbird.bot.defer.call_args_list


