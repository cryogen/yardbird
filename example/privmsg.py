import re

from django.conf.urls.defaults import include
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.core.exceptions import ImproperlyConfigured
import yardbird

# Overload URL Regex stuff to be case-insensitive.
class RegexIRCPattern(RegexURLPattern):
    def __init__(self, regex, *args, **kwargs):
        RegexURLPattern.__init__(self, regex, *args, **kwargs)
        self.regex = re.compile(regex, re.UNICODE|re.IGNORECASE)

def patterns(prefix, *args):
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = msg(prefix=prefix, *t)
        elif isinstance(t, RegexIRCPattern):
            t.add_prefix(prefix)
        pattern_list.append(t)
    return pattern_list

def msg(regex, view, kwargs=None, name=None, prefix=''):
    if type(view) == list:
        # For include(...) processing.
        return RegexURLResolver(regex, view[0], kwargs)
    else:
        if isinstance(view, basestring):
            if not view:
                raise ImproperlyConfigured('Empty IRC pattern view name not permitted (for pattern %r)' % regex)
            if prefix:
                view = prefix + '.' + view
        return RegexIRCPattern(regex, view, kwargs, name)

# Enough bikesheddin'!

from foobar import ircviews
#from bucket import ircviews as bucket

urlpatterns = patterns('',
   #msg(r'^(?P<addressed>\w+?):\s', include('privmsg.addressed')),
                       (r'^((?P<addressed>\S+):\s)?.*foo', ircviews.foo),
                       (r'^((?P<addressed>\S+):\s)?.*welcome datacomp', ircviews.foo),
                       (r'^((?P<addressed>\S+):\s)?.*bar', ircviews.bar),
                      )

# bucket patterns to dispatch to.  Horribly badly thought out.
#addressed = patterns(
#('(?P<key>.*?)\s+=~\s+s/(?P<from>(\\/|[^/])+)/(?P<to>.*)/(?P<flags>[gi]*)\s*$',
#bucket.edit),
#(r'^(?P<addressed>\S+:\s)?(?P<key>.*?)\s+=~\s+/(?P<match>(\\/|[^/])+)/',
#bucket.search),
#(r'^(?P<addressed>\S+:\s)?literal
#)

# vim:set shiftwidth=4 tabstop=4 expandtab smarttab textwidth=72:
