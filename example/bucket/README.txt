Bucket
======

An Exploratory Clone of the bucket.pl software
----------------------------------------------

My survey of bucket turned up the following public functions:
        1. edit factoid
        2. trigger factoid
        3. literal
        4. random factoid
        5. stats
        6. shut up (shuts bucket up for one minute, but if you use it
                too much the bot ignores you for a while.)
        7. Suggest a band name

The authentication system for bucket basically says "If you're an
operator in a particular channel, I trust you for these higher-level
commands."  These are:

	delete, un-shutup, join, part, ignore, unignore, list-ignored,
	protect factoid, unprotect factoid, alias one factoid to another,
	lookup (by data?), restart, set/get (seems to be raw db access
	somehow), plus an "undo" system for the most recent delete,
	insert, and edit commands done.

In addition, certain penalties and permissions don't apply to you if
you're in the oper list: You can shut up the bot indefinitely, you can
edit protected factoids, etc.

Sample Output
=============

So far this app has only implemented adding factoids and triggering
them.  It does not yet check for "also" when appending to an existing
one.

  	<SpaceHobo> yardbird: Clavicle is a troll
  	<yardbird> OK, SpaceHobo.
  	<SpaceHobo> yardbird: Clavicle is Brazillion
  	<yardbird> OK, SpaceHobo.
  	<SpaceHobo> yardbird: clavicle <hates> freedom
  	<yardbird> OK, SpaceHobo.
  	<SpaceHobo> what is clavicle?
  	<yardbird> SpaceHobo: clavicle =is= Brazillion
  	<SpaceHobo> what is clavicle?
  	<yardbird> SpaceHobo: clavicle =is= a troll
  	<SpaceHobo> what does clavicle hate?
  	<yardbird> SpaceHobo: clavicle =hates= freedom

