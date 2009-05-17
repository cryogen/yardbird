from example.privmsg import patterns

urlpatterns = patterns('example.iotower.ircviews',
         (r"""^what's\s+(?P<key>.*?)\W*$""", 'trigger'),
         (r"""^what\s+do(?:es)?\s+(?P<key>.*?)\s+(?P<verb>\w+?)\W*$""", 'trigger'),
         (r"""^what\s+(?P<verb>\w+)\s+(?P<key>.*?)\W*$""", 'trigger'),
         (r"""^(?P<key>.*)\s+(?P<verb>is|are)\s+(?P<also>also\s+)?(?P<value>\S+.*)\W*$""",
          'learn'),
         (r"""^(?P<key>.*)\s+<(?P<verb>\w+)>\s+(?P<also>also\s+)?(?P<value>\S+.*)\W*$""",
          'learn'),
         (r"""^(?P<key>.*)'s\s+(?P<also>also\s+)?(?P<value>\S+.*)\W*$""",
          'learn'),
         (r"""^literal\s+(?P<key>......+?)\W*$""", 'literal'),
         (r"""^(?P<key>......+?)\W*$""", 'trigger'),
        )
    
