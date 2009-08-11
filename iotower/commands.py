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
 (r"""(?iux)^what's \s+ (?P<key>.*?) [?!.\s]*$""", 'trigger'), # What's foo?
(r"""(?iux)^what \s+ (?:do|does|did) \s+ (?P<key>.*?) \s+ (?P<verb>\w+?) [?!.\s]*$""",
  'trigger'), # What does foo eat?
 (r"""(?iux)^what \s+ (?P<verb>\w+) \s+ (?P<key>.*?) [?!.\s]*$""",
     'trigger'), # What thinks foo?

 # Learning factoids:
 (r"""(?iux)^(?P<key>.*) \s+ (?P<verb>is|are) \s+ (?P<also>also\s+)?
  (?P<tag><[^>]+>\s*)? (?P<value>\S+.*) \s*$""",
  'learn'), # foo is also <reply> bar! or foo is baz
 (r"""(?iux)^(?P<key>.*?) \s+ (?P<also>also\s+)? =(?P<verb>\w+)= \s+
  (?P<tag><[^>]+>\s*)? (?P<value>\S+.*) \s*$""",
  'learn'), # foo also =eats= baz
 (r"""(?iux)^(?P<key>.*)'s \s+ (?P<also>also\s+)? (?P<tag><[^>]+>\s*)?
  (?P<value>\S+.*) \s*$""", 'learn'), # foo's such a bar

 # Direct commands
 (r"""(?iux)^lock \s+ (?P<key>.+?) \s*$""", 'lock'), # lock foo
 (r"""(?iux)^unlock \s+ (?P<key>.+?) \s*$""", 'unlock'), # unlock foo
 (r"""(?iux)^literal \s+ (?P<key>.+?) [?!.\s]*$""", 'literal'), # literal foo
 (r"""(?iux)^undelete \s+ (?P<key>.+?) \s*$""", 'undelete'), # undelete foo
 (r"""(?iux)^unedit \s+ (?P<key>.+?) \s*$""", 'unedit'), # unedit foo
 (r"""(?iux)^reload""", 'reimport'), # re-import all yardbird apps

 # By default, the bot tries to trigger factoids, and fails silently
 (r"""(?iux)^(?P<key>.+?) [?!.\s]*$""", 'trigger'),
 (r"""(?iux)^(?P<key>.*)""", 'trigger')
)

