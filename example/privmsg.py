from django.conf.urls.defaults import include, patterns

urlpatterns = patterns('',
                       (r'(?iux)^\W*(?:(?P<addressee>\S+):\s+)?',
                        include('iotower.commands')),
                      )
