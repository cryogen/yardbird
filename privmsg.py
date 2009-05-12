from django.conf.urls.defaults import *
import doody

urlpatterns = patterns('',
                       (r'^foo', doody.foo),
                       (r'.', doody.bar),
                      )
# vim:set shiftwidth=4 tabstop=4 expandtab smarttab textwidth=72:
