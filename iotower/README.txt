=======
IOTower
=======

-----------------------------------------
An Infobot Replacement Inspired by Bucket
-----------------------------------------

::

	 / ,     . \    (((acbf)))
	( ( ( O ) ) )
	 \ `  |  ' /
	      |
	    |===|
	    |\ /|
	    | X |
	    |/ \|
	   /=====\
	   |\   /|
	   | \ / |
	   |  X  |
	   | / \ |
	   |/   \|

How Bucket Did It
=================

My survey of bucket turned up the following public functions:

        1. edit factoid
        2. trigger factoid
        3. literal
        4. random factoid
        5. stats
	6. shut up (shuts bucket up for one minute, but if you use it too
	   much the bot ignores you for a while.)
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
one::

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

Data Structures and Edit History
================================

We store factoids in a table that just has the trigger-keys and access
limits (and a few other ancillary bits of info).  In another table we
have responses, with a foreign key to the factoid row in question, the
verb, and the text of the response

In addition to these basic fields, we have four more:

        * response creator
        * date/time of factoid creation
        * response disabler (can be NULL)
        * date/time of factoid disabling (can be NULL)

This provides possibilities for detailed statistics and logs, and gives us
some bucket features for free in our database:

        :lookup: random limit 1 select from responses with disable
                fields set to NULL
        :delete: set the disabled time to now
        :undelete: NULL out the disabled time!
        :edit: Add a new response with the new text, and set the disable
                time for the old row to the creation for this new one
        :un-edit: find the two rows where creation and delete time
                match, and do a new edit with the old version's text (to
                preserve history)
        :snapshot in time: select responses where provided time is between
                creation and delete times.  Can tie into more elaborate
                rollback operations.

