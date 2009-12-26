import unittest
from yardbird.test import TestCase

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
        self.assertContains(response, "Roger that", method='PRIVMSG',
                count=1)
        self.assertNotContains(response, "sandwiches", method='PRIVMSG')
                
