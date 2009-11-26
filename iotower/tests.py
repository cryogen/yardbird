import unittest
from yardbird.test import TransactionTestCase

class GoofyTestCase(TransactionTestCase):
    def test_set_factoid(self):
        response = self.client.msg(self.client.nickname, 'emad is a troll')
        self.assertContains(response, self.client.my_nickname,
                method='PRIVMSG')
