from yardbird.ircresolvers import patterns

urlpatterns = patterns('example.iotower.ircviews',
(r"""^(?P<key>.*?)
 \s+ =~ \s+
 s(?P<sep>[^\w\s]) (?P<pattern>.*) (?P=sep) (?P<replacement>.*)
 (?P=sep)
 (?P<re_flags>[ig]*)
 \s*$""", 'edit'),

 (r"""^what's \s+ (?P<key>.*?) \W*$""", 'trigger'),
(r"""^what \s+ (?:do|does|did) \s+ (?P<key>.*?) \s+ (?P<verb>\w+?) \W*$""",
  'trigger'),
 (r"""^what \s+ (?P<verb>\w+) \s+ (?P<key>.*?) \W*$""", 'trigger'),

 (r"""^(?P<key>.*) \s+ (?P<verb>is|are) \s+ (?P<also>also\s+)?
  (?P<tag><[^>]+>\s+)? (?P<value>\S+.*) \W*$""", 'learn'),
 (r"""^(?P<key>.*?) \s+ (?P<also>also\s+)? =(?P<verb>\w+)= \s+
  (?P<tag><[^>]+>\s+)? (?P<value>\S+.*) \W*$""", 'learn'),
 (r"""^(?P<key>.*)'s \s+ (?P<also>also\s+)? (?P<tag><[^>]+>\s+)?
  (?P<value>\S+.*) \W*$""", 'learn'),

 (r"""^literal \s+ (?P<key>.+?) \W*$""", 'literal'),

 (r"""^(?P<key>.+?) \W*$""", 'trigger'),
 (r"""^(?P<key>.*)""", 'trigger')
)

