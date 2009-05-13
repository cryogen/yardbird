from django.conf.urls.defaults import *
from foobar import ircviews

urlpatterns = patterns('',
                       (r'^foo', ircviews.foo),
                       (r'welcome datacomp', ircviews.foo),
                       (r'.', ircviews.bar),
                      )
# vim:set shiftwidth=4 tabstop=4 expandtab smarttab textwidth=72:
