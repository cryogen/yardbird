import unittest
from yardbird.test import TestCase
from django.core import exceptions
from django.http import Http404

class IoTowerTestCase(TestCase):
    msgconf = 'example' # Test using the distributed privmsg.py et al

    def _call_and_response(self, assertion, query, substring=None,
            method='PRIVMSG', template='factoid.irc'):
        if not substring:
            substring = assertion
        response = self.client.msg(self.client.nickname, assertion)
        self.assertTemplateUsed(response, 'ack.irc') # successful set

        response = self.client.msg(self.client.nickname, query)
        self.assertTemplateUsed(response, template) # trigger
        self.assertContains(response, substring, method=method)

    def _assert_disallowed(self, message):
        self.assertRaises(exceptions.PermissionDenied, self.client.msg,
                self.client.nickname, message)
    def _assert_missing(self, message):
        self.assertRaises(Http404, self.client.msg,
                self.client.nickname, message)

class FactoidTestCase(IoTowerTestCase):
    """Test all the ways we can set and retrieve factoids."""

    def test_set_factoid(self):
        self._call_and_response('emad is a troll', 'what is emad?')
    def test_append_factoid(self):
        self._call_and_response('clavicle is a brazillion',
                'what is clavicle?')
        self._assert_disallowed('clavicle is a collarbone')
        response = self.client.msg(self.client.nickname,
                'clavicle is also a collarbone')
        self.assertTemplateUsed(response, 'ack.irc') # successful set

    def test_incredulous_request(self):
        self._call_and_response('sinkers are doughnuts',
                'what in the name of emad are sinkers???')
    def test_short_request(self):
        self._call_and_response('goobers are peanuts', 'goobers')

    def test_explicit_verb(self):
        self._call_and_response('apple =hates= your freedom',
                'what does apple hate?', 'apple hates your freedom')
    def test_append_explicit_factoid(self):
        self._call_and_response('python =loves= invisible syntax',
                'what does python love?', 'python loves invisible syntax')
        self.assertRaises(exceptions.PermissionDenied, self.client.msg,
                self.client.nickname, 'python =hates= implicit variables')
        self._call_and_response('python also =hates= implicit variables',
                'what does python hate?', 'python hates implicit variables')

    def test_reply_tag(self):
        self._call_and_response("love is <reply> Baby don't hurt me!",
                'what is love?', "Baby don't hurt me!",
                template='factoid-reply.irc')

    def test_action_tag(self):
        self._call_and_response("whatever is <action> shrugs",
                'whatever', "shrugs", method='ACTION',
                template='factoid-action.irc')

    def test_factoid_template_rendering(self):
        self._call_and_response("beats me is <action> beats {{nick}}",
                'beats me', "beats %s" % self.client.my_nickname,
                method='ACTION', template='factoid-action.irc')

    def test_edit(self):
        response = self._call_and_response('perl is the shiznit',
                'perl')
        response = self.client.msg(self.client.nickname,
                'perl =~ s/the //')
        self.assertTemplateUsed(response, 'factoid.irc')
        response = self.client.msg(self.client.nickname, 'perl')
        self.assertNotContains(response, 'the', method='PRIVMSG')


class PrivilegedOperations(IoTowerTestCase):
    """Test all the commands that require elevated privilege"""
    def setUp(self):
        self.client.join('#testing')
        self.client.privileged_channels.append('#testing')
        self.client.join('#moretests')
    def test_locking(self):
        self._assert_disallowed('lock the door')
        self.client.op(self.client.my_hostmask, '#testing')

        r = self.client.msg(self.client.nickname, 'lock the door')
        self.assertTemplateUsed(r, 'ack.irc')
        self._assert_disallowed('the door is ajar')

        self.client.deop(self.client.my_hostmask, '#testing')
        self._assert_disallowed('unlock the door')
        self.client.op(self.client.my_hostmask, '#testing')

        r = self.client.msg(self.client.nickname, 'unlock the door')
        self.assertTemplateUsed(r, 'ack.irc')

        # Unlocked, but we cannot create it as a new factoid any more
        self._assert_disallowed('the door is ajar')
        r = self.client.msg(self.client.nickname, 'the door is also ajar')
        self.assertTemplateUsed(r, 'ack.irc')

        self.client.deop(self.client.my_hostmask, '#testing')

    def test_literal(self):
        response = self.client.msg(self.client.nickname,
                'the moon is made of green cheese')
        self.assertTemplateUsed(response, 'ack.irc')
        self._assert_disallowed('literal the moon')

        self.client.op(self.client.my_hostmask, '#testing')
        response = self.client.msg(self.client.nickname,
                'literal the moon')
        self.assertContains(response, '=is=', method='PRIVMSG')
        self.assertContains(response, 'made of green cheese',
                method='PRIVMSG')
        #self.assertTemplateUsed(response, 'literal.irc') # FIXME
        self.client.deop(self.client.my_hostmask, '#testing')

    def test_delete(self):
        response = self._call_and_response('ponies are pretty',
                'ponies')
        self._assert_disallowed('ponies =~ g/pretty/d')

        self.client.op(self.client.my_hostmask, '#testing')
        response = self.client.msg(self.client.nickname,
                'ponies =~ g/pretty/d')
        self.assertTemplateUsed(response, 'ack.irc')
        self._assert_missing('ponies')

        self.client.deop(self.client.my_hostmask, '#testing')
