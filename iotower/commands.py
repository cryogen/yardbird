from django.conf.urls.defaults import patterns

urlpatterns = patterns('iotower.ircviews',
(r"""(?iux)^(?P<key>.*?)
 \s+ =~ \s+
 s(?P<sep>[^\w\s]) (?P<pattern>.*) (?P=sep) (?P<replacement>.*)
 (?P=sep)
 (?P<re_flags>[ig]*)
 \s*$""", 'edit'), # foo =~ s/bar/baz/ig <-- edit factoid
 (r"""(?iux)^(?P<key>.*?)
 \s+ =~ \s+
 (?P<re_flags>[ig]*) (?P<sep>[^\w\s]) (?P<pattern>.*) (?P=sep) d
 \s*$""", 'delete'), # foo =~ gi/foo/d <-- delete

 # Triggering factoids: 
 (r"""(?iux)^what's \s+ (?P<key>.*?) \W*$""", 'trigger'), # What's foo?
(r"""(?iux)^what \s+ (?:do|does|did) \s+ (?P<key>.*?) \s+ (?P<verb>\w+?) \W*$""",
  'trigger'), # What does foo eat?
 (r"""(?iux)^what \s+ (?P<verb>\w+) \s+ (?P<key>.*?) \W*$""",
     'trigger'), # What thinks foo?

 # Learning factoids:
 (r"""(?iux)^(?P<key>.*) \s+ (?P<verb>is|are) \s+ (?P<also>also\s+)?
  (?P<tag><[^>]+>\s*)? (?P<value>\S+.*) \W*$""",
  'learn'), # foo is also <reply> bar! or foo is baz
 (r"""(?iux)^(?P<key>.*?) \s+ (?P<also>also\s+)? =(?P<verb>\w+)= \s+
  (?P<tag><[^>]+>\s*)? (?P<value>\S+.*) \W*$""",
  'learn'), # foo also =eats= baz
 (r"""(?iux)^(?P<key>.*)'s \s+ (?P<also>also\s+)? (?P<tag><[^>]+>\s*)?
  (?P<value>\S+.*) \W*$""", 'learn'), # foo's such a bar

 # Direct commands
 (r"""(?iux)^lock \s+ (?P<key>.+?) \W*$""", 'lock'), # lock foo
 (r"""(?iux)^unlock \s+ (?P<key>.+?) \W*$""", 'unlock'), # unlock foo
 (r"""(?iux)^literal \s+ (?P<key>.+?) \W*$""", 'literal'), # literal foo
 (r"""(?iux)^undelete \s+ (?P<key>.+?) \W*$""", 'undelete'), # undelete foo
 (r"""(?iux)^unedit \s+ (?P<key>.+?) \W*$""", 'unedit'), # unedit foo
 (r"""(?iux)^reload""", 'reimport'), # re-import all yardbird apps

 # By default, the bot tries to trigger factoids, and fails silently
 (r"""(?iux)^(?P<key>.+?) \W*$""", 'trigger'),
 (r"""(?iux)^(?P<key>.*)""", 'trigger')
)

