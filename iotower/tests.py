"""
=======
IOTower
=======

---------------------------
An Infobot App for Yardbird
---------------------------

::

	 / ,     . \
	( ( ( O ) ) )
	 \ `  |  ' /
	      |
	    /===\
	    |\ /|
	    | X |
	    |/ \|
	   /=====\
	   |\   /|
	   | \ / |
	   |  X  |
	   | / \ |
	   |/   \|

IOTower is a reimplementation of Kevin Lenzo's famous Infobot as a
Yardbird app.  Infobots were originally  meant to sit idle in a channel
and listen for declarative statements containing the verbs "is" or
"are", then spit this tidbit of knowledge back at the channel if someone
asks the right question.  They pretend to be helpful users in your
channel, and as such they break RFC bot etiquette and use PRIVMSG
instead of NOTICE for their replies.

To demonstrate the behavior of a stock IOTower bot, we will be using the
yardbird test client::

    >>> from yardbird.test.client import Client
    >>> c = Client(user='TestUser!testuser@localhost',
    ... bot='TestBot!testbot@localhost', ROOT_MSGCONF='example')
    >>> c.privileged_channels.append('#testing')

Factoids
--------

Factoids are key->value mappings stored in the database.  The simplest
way to create one is to state a phrase containing the word "is" or
"are", and the factoid can then be retrieved with a "what is" or "what
are" question::

    >>> print c.msg(c.nickname, 'emad is a troll')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'what is emad?')
    PRIVMSG: [...'factoid.irc'...] emad is a troll -> TestUser

The question format is somewhat forgiving, and the default
``commands.py`` allows for common variations in how the question is
asked::

    >>> print c.msg(c.nickname, 'what on earth is emad?')
    PRIVMSG: [...'factoid.irc'...] emad is a troll -> TestUser
    >>> print c.msg(c.nickname, 'emad?')
    PRIVMSG: [...'factoid.irc'...] emad is a troll -> TestUser

Or it need not even be a question at all::

    >>> print c.msg(c.nickname, 'emad!')
    PRIVMSG: [...'factoid.irc'...] emad is a troll -> TestUser

Once a factoid has a response associated with it, the standard assertion
syntax will not work::

    >>> print c.msg(c.nickname, 'emad is a troll')
    PRIVMSG: [...'already.irc'...] I already had it that way, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'emad is your best nightmare!')
    Traceback (most recent call last):
        ...
    PermissionDenied

To append to an existing factoid, you need to use the word "also"::

    >>> print c.msg(c.nickname, 'emad is also your best nightmare!')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser

Nonstandard Verbs
~~~~~~~~~~~~~~~~~

The verbs "is" and "are" hold special status in the bot.  Another verb
may be specified by surrounding it in equal signs::

    >>> print c.msg(c.nickname, 'Python =loves= invisible syntax.')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'python')
    PRIVMSG: [...'factoid.irc'...] python loves invisible syntax. -> TestUser
    >>> print c.msg(c.nickname, 'Python also =hates= implicit variables')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser

Although factoids with multiple responses will choose at random when
queried, you can specify a particular verb by asking the question "What
does *factoid* *verb*" where "verb" can have a final 's' added to become
the verb stored in the database::

    >>> print c.msg(c.nickname, 'what does python love?')
    PRIVMSG: [...'factoid.irc'...] python loves invisible syntax. -> TestUser
    >>> print c.msg(c.nickname, 'what does PYTHON hate?')
    PRIVMSG: [...'factoid.irc'...] PYTHON hates implicit variables -> TestUser

Behavioral Tags
~~~~~~~~~~~~~~~

IOTower, like Infobot before it, pretends to be an actual user.  To make
responses more flexible (and thus realistic) it is possible to avoid the
predictable factoid format by using ``<reply>`` or ``<action>`` tags.

The ``<reply>`` tag allows you to specify the response in full, omitting
the factoid name and verb::

    >>> print c.msg(c.nickname, "love is <reply> Baby don't hurt me!")
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'What is love?')
    PRIVMSG: [...'factoid-reply.irc'...] Baby don't hurt me! -> TestUser

The ``<action>`` tag also allows you to specify the response in full,
but uses ACTION instead of PRIVMSG to deliver the reply, as though the
bot had typed ``/me`` in an IRC client::

    >>> print c.msg(c.nickname, 'whatever is <action> shrugs')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'whatever')
    ACTION: [...'factoid-action.irc'...] shrugs -> TestUser

Factoids as Templates
~~~~~~~~~~~~~~~~~~~~~

To further the effect, factoids are rendered as Django templates.  These
templates have access to all of the request variables such as ``nick``
and ``channel`` as well as all of the standard template tags and
functions::

    >>> print c.msg(c.nickname, "hello is <reply> Howdy, {{nick}}!")
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'Hello!')
    PRIVMSG: [...'factoid-reply.irc'...] Howdy, TestUser! -> TestUser

    >>> print c.msg(c.nickname, 
    ...             'the day of the week is <reply> Today is {% now "l" %}')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, "What's the day of the week?")
    PRIVMSG: [...'factoid-reply.irc'...] Today is ...day -> TestUser

Editing Factoids
~~~~~~~~~~~~~~~~

Factoids can be edited using a regex substitution syntax similar to that
used by Perl.  This syntax comes directly from Infobot, and is kept
largely for historical reasons::

    >>> print c.msg(c.nickname, 'perl is the shiznit')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'perl =~ s/the/complete/')
    PRIVMSG: [...'factoid.irc'...] perl is complete shiznit -> TestUser

Edits are one operation that require the bot be addressed (if in a
public channel) or privately messaged (as we have been doing so far)::

    >>> print c.join('#testing')
    None
    >>> print c.msg('#testing', 'perl =~ s/complete/utter/')
    QUIET: []  -> 
    >>> print c.msg('#testing', 'TestBot: perl =~ s/complete/utter/')
    PRIVMSG: [...'factoid.irc'...] TestUser: perl is utter shiznit -> #testing

Limits to Factoid Keys
----------------------

As a note, factoid keys are normalized before storage in the database.
These normalized keys are limited to 64 characters, tops::

    >>> print c.msg(c.nickname, '%s =is= bogus' % ('a' * 65))
    Traceback (most recent call last):
        ...
    OverflowError

Some factoids will look like attempts to train a bot with other
factoids::

    >>> print c.msg(c.nickname, 'A is a letter.')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'A is A =is= a tautology.')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> print c.msg(c.nickname, 'what is a?')
    PRIVMSG: [...'factoid.irc'...] a is a letter. -> TestUser
    >>> print c.msg(c.nickname, 'A is A')
    PRIVMSG: [...'factoid.irc'...] A is A is a tautology. -> TestUser

Privileged Operations
---------------------

Some operations only work when a user is trusted.  Yardbird defines a
trusted user as one that has operator privilege in a predefined trusted
channel::

    >>> opc = Client(user='SuperUser!superuser@localhost',
    ... bot='TestBot!testbot@localhost', ROOT_MSGCONF='example')
    >>> opc.join('#testing')
    >>> opc.op(opc.my_hostmask, '#testing')
    >>> opc.privileged_channels.append('#testing')

Note that from here on, we now have two clients (``c`` and ``opc``) in
the ``#testing`` channel, and we will send most of our communication
with the bot through that channel.

Lock
~~~~

Locking and unlocking factoids is only available to privileged users.
This prevents a much-loved factoid from being damaged by a user that
does not appreciate this::

    >>> print c.msg('#testing', 'TestBot: lock python')
    Traceback (most recent call last):
        ...
    PermissionDenied
    >>> print opc.msg('#testing', 'TestBot: lock python')
    PRIVMSG: ['ack.irc'] Roger that, SuperUser. -> #testing
    >>> print c.msg('#testing',
    ... 'TestBot: python also =haxxors= j00!!! Hacked by TestClient!!!!!')
    Traceback (most recent call last):
        ...
    PermissionDenied

Even privileged users are unable to modify the factoid until it is
unlocked::

    >>> print opc.msg('#testing', 'TestBot: python is also free to use')
    Traceback (most recent call last):
        ...
    PermissionDenied
    >>> print opc.msg('#testing', 'TestBot: unlock python')
    PRIVMSG: ['ack.irc'] Roger that, SuperUser. -> #testing
    >>> print opc.msg('#testing', 'TestBot: python is also free to use')
    PRIVMSG: ['ack.irc'] Roger that, SuperUser. -> #testing



Signal Handlers
---------------

Many Infobots out in the wild have been hacked full of customizations
that do not fit the factoid model.  Yardbird takes advantage of the
Django signal system to raise signals before and after a dispatched
request has been serviced, and this is an excellent place to put your
customized handlers.

We will demonstrate with the Yardbird test client's mock sender queue,
which stores all the actions any handlers tried to perform::

    >>> c.signal_sender
    []
    >>> c.msg(c.nickname, '242')
    Traceback (most recent call last):
        ...
    Http404: No Factoid matches the given query.
    >>> c.signal_sender.get_event()
    (('notice', 'TestUser', '242 sighting!'), {})

Here our *242 sighting* handler called ``sender.notice('TestUser', '242
sighting!')`` and we caught it, even though the actual request raised an
error because no such factoid exists.

The *242 sighting* handler has a very forgiving regex, and all kinds of
things can go between the digits:: 

    >>> print c.msg(c.nickname,
    ...             '2 is the loneliest number, but 4 times 2 is 8')
    PRIVMSG: ['ack.irc'] Roger that, TestUser. -> TestUser
    >>> c.signal_sender.get_event()
    (('notice', 'TestUser', '242 sighting!'), {})

The bot's own responses do not trigger these handlers, though::

    >>> print c.msg(c.nickname, 'What is 2?')
    PRIVMSG: [...'factoid.irc'...] 2 is the loneliest number, but 4 times 2 is 8 -> TestUser
    >>> c.signal_sender
    []



"""
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

class PrivilegedOperations(IoTowerTestCase):
    """Test all the commands that require elevated privilege"""
    def setUp(self):
        self.client.join('#testing')
        self.client.privileged_channels.append('#testing')
        self.client.join('#moretests')

    def test_literal(self):
        response = self.client.msg(self.client.nickname,
                'the moon is made of green cheese')
        self.assertTemplateUsed(response, 'ack.irc')
        self._assert_disallowed('literal the moon')

        response = self.client.msg(self.client.nickname,
                'the moon is also <reply>Nuke the moon!')
        self.assertTemplateUsed(response, 'ack.irc')

        self.client.op(self.client.my_hostmask, '#testing')
        response = self.client.msg(self.client.nickname,
                'literal the moon')
        self.assertContains(response, '=is=', method='PRIVMSG')
        self.assertContains(response, 'made of green cheese',
                method='PRIVMSG')
        self.assertContains(response, '|', method='PRIVMSG')
        self.assertContains(response, '<reply> Nuke the moon!',
                method='PRIVMSG')
        #self.assertTemplateUsed(response, 'literal.irc') # FIXME

        response = self.client.msg(self.client.nickname,
                'lock the moon')
        self.assertTemplateUsed(response, 'ack.irc')
        response = self.client.msg(self.client.nickname,
                'literal the moon')
        self.assertContains(response, ' [LOCKED] ', method='PRIVMSG')
        
        self.client.deop(self.client.my_hostmask, '#testing')

    def test_delete(self):
        response = self._call_and_response('ponies are pretty',
                'ponies')
        self._assert_disallowed('ponies =~ g/pretty/d')

        self.client.op(self.client.my_hostmask, '#testing')
        response = self.client.msg(self.client.nickname,
                'ponies =~ gi/PrEtTy/d')
        self.assertTemplateUsed(response, 'ack.irc')
        self._assert_missing('ponies')

        self.client.deop(self.client.my_hostmask, '#testing')

    def test_undelete(self):
        response = self._call_and_response('ponies are pretty',
                'ponies')

        self.client.op(self.client.my_hostmask, '#testing')
        response = self.client.msg(self.client.nickname,
                'ponies =~ gi/PrEtTy/d')
        self.assertTemplateUsed(response, 'ack.irc')

        response = self.client.msg(self.client.nickname,
                'undelete ponies')
        self.assertTemplateUsed(response, 'ack.irc')

        self.client.deop(self.client.my_hostmask, '#testing')

        response = self.client.msg(self.client.nickname, 'ponies')
        self.assertContains(response, 'ponies are pretty', method='PRIVMSG')

    def test_unedit(self):
        response = self._call_and_response('perl is the shiznit',
                'perl')

        self.client.op(self.client.my_hostmask, '#testing')
        response = self.client.msg(self.client.nickname,
                'perl =~ s/the //')
        self.assertTemplateUsed(response, 'factoid.irc')

        self.assertRaises(Http404, self.client.msg,
                self.client.nickname, 'unedit pearl')
        response = self.client.msg(self.client.nickname, 'unedit perl')
        self.assertTemplateUsed(response, 'ack.irc')
        self.client.deop(self.client.my_hostmask, '#testing')

        response = self.client.msg(self.client.nickname, 'perl')
        self.assertContains(response, 'the shiznit', method='PRIVMSG')



class AncillaryStuff(IoTowerTestCase):
    """Test behavior not related to factoids."""
    def test_stats(self):
        self._call_and_response('statistics are useful', 'statistics')
        response = self.client.msg(self.client.nickname, 'stats')
        self.assertContains(response,
                'I have performed 1 edits on 1 factoids containing' +
                ' 1 active responses', method='PRIVMSG')

