========
Yardbird
========

---------------
Getting Started
---------------

.. contents::

Getting Your Bot On-Line
========================

The first step to using Yardbird is to just get a bot running and
connected to an IRC network.  While it's possible to use the
``example/`` tree to build your bot, it is not recommended for security
reasons.

Create a Django Project
-----------------------

The first step is to use the ``django-admin`` command to create a `Django
project`_ for your bot.  Just as the project unifies a number of apps into
an individual Web site, it also unfies apps into a single running chat bot
instance.

.. sourcecode:: console

        $ django-admin startproject nerdbot
        $ cd nerdbot/
        $ ls
        __init__.py  manage.py*  settings.py  urls.py

Now we need to configure the database `just as we do with pure Django`_.
In this example we'll use sqlite in ``/tmp/nerdb`` (but please choose a
more permanent location for your own database).

Open up ``settings.py`` and adjust the database fields as shown.

.. sourcecode:: python

        DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        DATABASE_NAME = '/tmp/nerdb'   # Or path to database file if using sqlite3.
        DATABASE_USER = ''             # Not used with sqlite3.
        DATABASE_PASSWORD = ''         # Not used with sqlite3.
        DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
        DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

.. _Django project: http://docs.djangoproject.com/en/dev/intro/tutorial01/#creating-a-project
.. _just as we do with pure Django: http://docs.djangoproject.com/en/dev/intro/tutorial01/#database-setup

Add Yardbird
------------

If you have yardbird installed in your ``PYTHONPATH``, you can simply add it
to your ``INSTALLED_APPS``.  If you're having trouble getting it properly
installed, you can always copy the tree into your project in a pinch.

.. sourcecode:: python
        :linenos:

        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'yardbird',
        )



Configure IRC Channels
----------------------

Now comes the first bit of yardbird-specific configuration.  You'll need to
create a variable named ``IRC_CHANNELS`` which contains a tuple of IRC
URIs.  

.. sourcecode:: python
        :linenos:

        IRC_CHANNELS = (
         'ircs://nerdbird:password@irc.slashnet.org:6697/privileged/#yardbird',
         'ircs://irc.slashnet.org:6697/#birdland',
         u'ircs://irc.slashnet.org:6697/#\u2615', # unicode teacup
         )

The above will connect to Slashnet_ via SSL, with nickname ``nerdbird``
and server password ``password`` [1]_.  Since Slashnet_ passes the server
password through to NickServ, this avoids the need for a special NickServ
application.  The first line also joins ``#yardbird`` and notes that it is
*privileged*, meaning that the operators in that channel may use restricted
commands.

The next two channels (``#birdland`` and ``#☕``) are part of the same
connection, so they use the same settings that ``#yardbird`` did.

.. _Slashnet: http://www.slashnet.org/

.. [1] You will, of course, want to change these to avoid clashing with
   someone else!

Configure Paths for Pattern Matchers
------------------------------------

Django only has one kind of input to match against: urls.  Yardbird, by
contrast, has a pattern matching configurations for several types of IRC
events.  The default Django ``ROOT_URLCONF`` is fine as it comes,
specifying a specific ``urls.py`` module.  For Yardbird, you'll want to
specify a *package* (directory) in your ``ROOT_MSGCONF`` where you will put
files like ``privmsg.py`` and ``action.py``.  Typically the parent package
of the ``ROOT_URLCONF`` is fine.

.. sourcecode:: python

        ROOT_URLCONF = 'nerdbird.urls'
        ROOT_MSGCONF = 'nerdbird'


Making Your Bot Do Something
============================

At this point if you run ``./manage.py runircbot`` it will connect to
Slashnet_ and join the three channels you specified.  
