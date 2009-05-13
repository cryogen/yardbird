from django.conf.urls.defaults import *
from foobar import ircviews
from django.conf import settings

urlpatterns = patterns('',
                       (r'^%s: foo' % settings.IRC_NICK, ircviews.foo),
                       (r'welcome datacomp', ircviews.foo),
                       (r'^%s: ' % settings.IRC_NICK, ircviews.bar),

                      )
# vim:set shiftwidth=4 tabstop=4 expandtab smarttab textwidth=72:
