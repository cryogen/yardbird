========
Yardbird
========

------------------------------
A Django-based Chat Bot System
------------------------------

::

	    ,__,       (Another Hairdo!)
	  ,'    `.     /
	 /`-,   @ `__
	|    `-, ,'\
	|       `-, 
	|     /    `-, 
	 \    |   /   `,
	  `._  `-'   ,'
	     `-....-'
	        /
	       (__

What It Is
==========

Yardbird is a Python package that allows you to write IRC chat bots using
Django.  Internally it uses Twisted Python to provide a sort of "IRC client
runserver" that dispatches incoming messages to your Django apps.  This
saves you from having to ever see or touch Twisted code, and lets you use
Django models and templates in your bot.

How to Get It
=============

	* The latest source tarballs can be downloaded from
	  https://launchpad.net/yardbird/+download 
	* Packages for Ubuntu (the repository works with Hardy or later) are
	  available from https://launchpad.net/~spacehobo/+archive/ppa
	  where you can install the ``python-django-yardbird`` and
	  ``python-yardbird-iotower`` packages.

How to Develop It
-----------------

Development of both the Yardbird chatbot system and the IOTower example app
is done from a single bazaar_ tree.  To get access to the development tree,
simply run::

	bzr branch lp:yardbird

...and you will have a complete source tree with the ``yardbird`` and
``iotower`` packages as well as an example Django IRC Bot setup.

.. _bazaar: http://bazaar-vcs.org/

How to Install
==============

If you are using the PPA or other provided packages, you're all set!
Otherwise, you can either use the provided ``setup.py`` to install the
``yardbird/`` package into your ``PYTHONPATH``, or copy/link the yardbird/
tree directly into your project as an application, like so::

	example/
	|-- __init__.py
	|-- manage.py
	|-- settings.py
	|-- testapp
	|   |-- __init__.py
	|   |-- models.py
	|   `-- views.py
	|-- urls.py
	`-- yardbird
	    |-- __init__.py
	    ...

Now you're ready to write some IRC dispatchers and views!

How to Run
==========

The ``yardbird`` app inculdes a ``runircbot`` management command, so that
you can simply::

	./manage.py runircbot

and it will connect via SSL according to the following variables from
``settings.py``:

	:IRC_NICK:	The bot's desired nickname.  The server may set the
			bot to an alternate nick if the desired one is in
			use.
	:IRC_CHANNELS:	A list of channels to join on connection.
	:IRC_SERVERS:	A tuple of 2-tuples containing server hostname and
			connecting SSL port.

How to Code for Yardbird
========================

Writing apps for Yardbird, or hooking existing Web apps into Yardbird, is
similar to writing ordinary Django apps.  The key differences are as
follows:

	1. There are multiple message types, so in place of `urls.py`, you
	   will have a number of dispatchers: one for each message type you
	   wish to handle.
	2. Since IRC is not HTTP, the request and response objects are
	   different, and new shortcuts are provided.
	3. A different set of signals exists for the IRC request
	   start/finish events.  Model signals, however, remain the same.

Dispatchers
-----------

The key dispatchable events are as follows:

	:privmsg:	Normal messages sent either privately or in a
			channel
	:action:	"Emotes" sent using the /me command
	:topic:		Changes to a channel's topic
	:nick:		Changes in a user's nickname

Typical bots are only interested in the ``privmsg`` and possibly ``action``
events.  As an example, a bot that wished to treat them both the same would
create a ``privmsg.py`` in the directory specified by
``settings.ROOT_MSGCONF`` with a standard Django ``urlpatterns`` structure,
and would then symlink ``actions.py`` to the privmsg dispatcher.

It is recommended that you keep IRC-specific views in a separate package.
The Yardbird maintainers use ``ircviews.py``, but anything will do.


Request and Response Objects
----------------------------

The ``IRCRequest`` and ``IRCResponse`` objects in the ``yardbird.irc``
module are notably simpler than their HTTP counterparts.  They effectively
behave as simple structs, with only a little initialization logic.  

While HTTP Django assumes that any successful response will be an HTTP 200
code, IRC responses must specify which mechanism the reply will use.
Currently the options are:

	:PRIVMSG:	To reply as IRC 'speech' either privately or in a
			channel
	:ACTION:	To reply with the description of an action, as with
			the /me command in most clients.
	:NOTICE:	To reply with a CTCP NOTICE that is clearly the
			result of an automated system.
	:TOPIC:		To change the topic of a channel.
	:QUIET:		To silently discard the ``IRCResponse`` data.
	:RESET:		To trigger a reimport of all loaded apps.

Shortcuts
---------

The ``yardbird.shortcuts`` module has a few handy shortcuts to simplify the
crafting of IRCResponse objects:

	:render_to_response:	Renders a *template* using a supplied
				*dictionary*, and sends the result to a
				specified *recipient* by an optional
				*method* (defaults to ``PRIVMSG``)
	:render_to_reply:	Renders a *template* using a supplied
				*dictionary* as a reply to the user in the
				supplied *request* object.
	:render_quick_reply:	Renders a *template* using the supplied
				*request* object's ``__dict__`` as context,
				and sends as a reply to the original
				recipient.
	:render_silence:	Returns an IRCResponse which uses the
				``QUIET`` method.
	:render_error:		Returns an error *message* to the specified
				*recipient* with the ``NOTICE`` method.

Signals
-------

The ``yardbird.signals`` package implements two new signals:

	:request_started:	Fired off before an IRCRequest is
				dispatched to yardbird views.
	:request_finished:	Fired off after an IRCRequest is dispatched
				to yardbird views.
