========
Yardbird
========

----------------------
Writing Your First App
----------------------

.. contents::

Get Started
===========

First of all, it is recommended that before you work through this
document that you have gone through the `Getting Started`_ document and
at least read through the `Django Tutorial`_ or are otherwise familiar
with Django.

.. _Getting Started: getting_started.html
.. _Django Tutorial: http://docs.djangoproject.com/en/dev/intro/tutorial01/

Our Example App
===============

The application we will be writing is a simple "karma" system for the
bot.  Many bots provide a mechanism for granting or revoking kudos for
users or arbitrary phrases.  The following is an example of how this
system might be used.

.. sourcecode:: irc

        <User> nerdbird: kudos for python
        notice: <nerdbird> python has neutral kudos
        <User> python++
        <User> nerdbird: kudos for python
        -nerdbird- python has a kudos of 1
        <User> bugs--
        <User> nerdbird: kudos for bugs
        -nerdbird- bugs has a kudos of -1
        <User> Bugs suck!
        <User> Python rules!
        <User> nerdbird: kudos for bugs
        -nerdbird- bugs has a kudos of -2
        <User> nerdbird: kudos for python
        -nerdbird- python has a kudos of 2

As you can see, the use of C-inspired increment and decrement operators
manage a persistent counter for each term.

Create a Django Application
===========================

The first step is to use the ``django-admin`` command to create a `Django
application`_ for your bot.  

.. _Django application: http://www.b-list.org/weblog/2006/sep/10/django-tips-laying-out-application/

.. sourcecode:: console

        $ mkdir -p ~/src/yardbird-kudos
        $ cd ~/src/yardbird-kudos/
        $ django-admin startapp kudos
        $ cd kudos/
        $ ls
        __init__.py  models.py  tests.py  views.py

It is recommended that you create a project space that contains the
application in a subdirectory, and use symbolic links or additions to
your ``PYTHONPATH`` to make it visible to your bot.

Add the Application to our Bot
------------------------------

For simplicity, we'll cd to our bot's project directory and use symlinks
to make the kudos app visible to the example bot.

.. sourcecode:: console

        $ ln -s ~/src/yardbird-kudos/kudos
        $ ls
        __init__.py  kudos@  manage.py*  settings.py  urls.py

Now we'll edit our bot's ``settings.py`` and add the kudos app.

.. sourcecode:: python
        :linenos:

        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'yardbird',
            'kudos',
        )


Writing our Models
==================

Yardbird uses the `Django ORM`_ to manage a relational database.

.. _Django ORM: http://docs.djangoproject.com/en/dev/topics/db/models/

Two Approaches
--------------

We have two options for storing the 

Tests
=====

...

Writing Views
-------------

...

A Stock URLconf
---------------

...
