import unittest
from yardbird.test import TransactionTestCase

class FactoidTestCase(TransactionTestCase):
    def setUp(self):
        self.client.join('#testing')
    def _call_and_response(self, assertion, query, substring):
        response = self.client.msg(self.client.nickname, assertion)
        self.assertContains(response, self.client.my_nickname,
                method='PRIVMSG')
        response = self.client.msg(self.client.nickname, query)
        self.assertContains(response, substring, method='PRIVMSG')

    def test_set_factoid(self):
        self._call_and_response('emad is a troll', 'what is emad?',
                'emad is a troll')

    def test_explicit_verb(self):
        self._call_and_response('apple =hates= your freedom',
                'what does apple hate?', 'apple hates your freedom')

