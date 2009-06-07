#!/usr/bin/python

# XXX: this should be replaced with stock urlresolvers using (?iLmsux)
# stuff at the front of individual regexes instead!

import re

from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.core.exceptions import ImproperlyConfigured

# Overload URL Regex stuff to be case-insensitive.
class RegexIRCPattern(RegexURLPattern):
    def __init__(self, regex, *args, **kwargs):
        RegexURLPattern.__init__(self, regex, *args, **kwargs)
        self.regex = re.compile(regex,
                                re.UNICODE|re.IGNORECASE|re.VERBOSE)

# overload patterns to use RegexIRCPattern insead of RegexURLPattern
def patterns(prefix, *args):
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = msg(prefix=prefix, *t)
        elif isinstance(t, RegexIRCPattern):
            t.add_prefix(prefix)
        pattern_list.append(t)
    return pattern_list

# msg function to replace the 'url' function from patterns()
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
