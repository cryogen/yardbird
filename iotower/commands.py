from django.conf.urls.defaults import patterns

urlpatterns = patterns('iotower.ircviews',
(r"""(?iux)^(?P<key>.*?)
 \s+ =~ \s+
 s(?P<sep>[^\w\s]) (?P<pattern>.*) (?P=sep) (?P<replacement>.*)
 (?P=sep)
 (?P<re_flags>[ig]*)
 \s*$""", 'edit'),

 (r"""(?iux)^what's \s+ (?P<key>.*?) \W*$""", 'trigger'),
(r"""(?iux)^what \s+ (?:do|does|did) \s+ (?P<key>.*?) \s+ (?P<verb>\w+?) \W*$""",
  'trigger'),
 (r"""(?iux)^what \s+ (?P<verb>\w+) \s+ (?P<key>.*?) \W*$""", 'trigger'),

 (r"""(?iux)^(?P<key>.*) \s+ (?P<verb>is|are) \s+ (?P<also>also\s+)?
  (?P<tag><[^>]+>\s*)? (?P<value>\S+.*) \W*$""", 'learn'),
 (r"""(?iux)^(?P<key>.*?) \s+ (?P<also>also\s+)? =(?P<verb>\w+)= \s+
  (?P<tag><[^>]+>\s*)? (?P<value>\S+.*) \W*$""", 'learn'),
 (r"""(?iux)^(?P<key>.*)'s \s+ (?P<also>also\s+)? (?P<tag><[^>]+>\s*)?
  (?P<value>\S+.*) \W*$""", 'learn'),

 (r"""(?iux)^literal \s+ (?P<key>.+?) \W*$""", 'literal'),
 (r"""(?iux)^reload""", 'reimport'),

 (r"""(?iux)^(?P<key>.+?) \W*$""", 'trigger'),
 (r"""(?iux)^(?P<key>.*)""", 'trigger')
)

