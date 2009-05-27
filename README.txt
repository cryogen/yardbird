Yardbird
========

A Django-based Chat Bot System
------------------------------

::

	     __//  (Ornithology!)
	cf  /.__.\ /
	    \ \/ /
	 '__/    \
	  \-      )
	   \_____/
	_____|_|____
	     " "


Background
==========

What follows is a mail I wrote to a friend about the future of our
rickety old Infobot.  It's been running in our channel for nearly a
decade now, and the code is warty and full of one-off additions and
surgical hacks that make it impossible to follow.  We've known for
nearly the bot's entire life that the software cried out for a
replacement.

Some friends in another channel had installed an Infobot, inspired by
our own, and quickly reimplemented it.  Over time, they kind of subtly
evangelized this software to us, and it seemed at times like they felt
we were simply rejecting it out of Pythonic snobbery against Perl (not
that Infobot isn't Perl, of course).

So I decided to investigate, and gave the "bucket" bot software a fair
shake.  In so doing, I had something of an inspiration, about which read
further:

The Explanation
===============

I took a look at bucket, and it's about a thousand lines of code.  It
uses POE, which is basically Perl's answer to Twisted.  It's an
asynchronous deferred-execution-with-callbacks way of coding, and comes
with lots of network protocol modules and database access modules.  One
day I'll find out why these features tend to be lumped together like
that.

The thing that killed me was that the deferred database access code was
all too mysql-specific, and was basically just raw SQL parcelled with
some context variables and forwarded on to output callbacks.  It kind of
weeps for an ORM, about which see:

        http://zork.net/motd/nick/django/your-favorite-orm-sucks.html

The code for bucket has a lot of logic that goes like this::

  if ($msg =~ GREATBIGHOARYREGEX) {
        ...
  else if ($msg =~ ANOTHERCRAZYREGEX) {
        ...

And so I thought to myself "Gosh, wouldn't it be great if this had
a dispatch mechanism where you could associate regexes with functions in
some kind of data structure, along with some kind of application data
for context?"  Oh hangon, that reminds me of...

        http://docs.djangoproject.com/en/dev/topics/http/urls/

I've been looking at twisted, which seems to be the system of choice for
writing IRC bots.  It's a bit hairy and bureaucratic, unfortunately.
The examples for setting up basic IRC bots are clean enough, but once
you turn the page it's all factories and reactors and aspect-oriented
bragging about how great it is to reduce your code to dozens of
three-line classes.  But it gives you that great responsive asynchronous
network library, which is nothing to sneeze at!

Django doesn't have any facilities for network protocols or asynchronous
coding, because it assumes that apache or some other web server will
take care of all that for you.  Once this occurred to me, the light
really went on: twisted need only provide a sort of "IRC Client Server"
model, and dispatch incoming requests to Django code the way apache does!

I can write a small twisted python script that basically uses the django
RegexURLResolver class on a separate file, and matches not against URL
path strings but IRC messages.  It can use the django ORM to store data
in an SQL database, and those data are immediately accessible to a
django web app in the same tree.  It can even use the template language
to format responses, although that may be overkill (still, nice to be
able to drop in IRC colors and control codes and things).  About the
only thing that I haven't looked into, which may or may not fit the
model, is the Forms library -- but hey, maybe there's some useful input
validation routines to call there.  Even the settings file is a great
place to stow things like nicks to use and servers to connect to and
channels to join.

So the only detail now is the request and response objects.  This is the
one place where django really fits in nicely with an asynchronous
twisted app: the functions are handed an HttpRequest object as a
parameter, and that tells them everything they want to know about the
request. They return an HttpResponse object that contains the return
code and the template to render and a sort of scope full of variables
for the template to use.  At each stage you're just populating a data
structure with all relevant information and yielding execution back to
the scheduler.

So my JFDI approach is to abuse these two objects for now, and write
proper IRC-centric classes.  I imagine that instead of GET and POST
variables, they'd have things like PRIVMSG and ACTION and NOTICE.  And
instead of things like the virtualhost hostname, there'd be the channel.
But for now I can overload enough of these variables to abuse them as
they are, I think.

Some side-effects of doing things this way:

        1. We'd get the django database management webapp for free
        2. The above also gets us user and group tables for free
        3. We can write other django web apps that yardbird could control
        4. We could write web front-ends to yardbird's factoid database
        5. We can probably port this model to XMPP trivially

