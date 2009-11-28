import unittest
from yardbird.test import TestCase
from django.core import exceptions

class FactoidTestCase(TestCase):
    msgconf = 'example' # Test using the distributed privmsg.py et al
    def setUp(self):
        self.client.join('#testing')
        self.client.privileged_channels.append('#testing')
        self.client.join('#moretests')
    def _call_and_response(self, assertion, query, substring):
        response = self.client.msg(self.client.nickname, assertion)
        self.assertTemplateUsed(response, 'ack.irc') # successful set

        response = self.client.msg(self.client.nickname, query)
        self.assertTemplateUsed(response, 'factoid.irc') # trigger
        self.assertContains(response, substring, method='PRIVMSG')

    def test_set_factoid(self):
        self._call_and_response('emad is a troll', 'what is emad?',
                'emad is a troll')

    def test_explicit_verb(self):
        self._call_and_response('apple =hates= your freedom',
                'what does apple hate?', 'apple hates your freedom')

    def test_locking(self):
        self.client.op(self.client.my_hostmask, '#testing')
        r = self.client.msg(self.client.nickname, 'lock the door')
        self.assertTemplateUsed(r, 'ack.irc')
        self.assertRaises(exceptions.PermissionDenied, self.client.msg,
                self.client.nickname, 'the door is ajar')
        r = self.client.msg(self.client.nickname, 'unlock the door')
        self.assertTemplateUsed(r, 'ack.irc')
        # Unlocked, but we cannot create it as a new factoid any more
        self.assertRaises(exceptions.PermissionDenied, self.client.msg,
                self.client.nickname, 'the door is ajar')
        r = self.client.msg(self.client.nickname, 'the door is also ajar')
        self.assertTemplateUsed(r, 'ack.irc')
        self.client.deop(self.client.my_hostmask, '#testing')

