from django.conf.urls.defaults import include
from yardbird.ircresolvers import patterns


urlpatterns = patterns('',
                       (r'^\W*(?:(?P<addressee>\S+):\s+)?',
                        include('example.iotower.commands')),
                      )
