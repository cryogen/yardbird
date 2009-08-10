from django.conf.urls.defaults import include, patterns

urlpatterns = patterns('',
    (r'(?iux) ^ \W* (?: (?P<addressee> \S+ ) : \s+ )? stats \W* $',
        'yardbird.contrib.stats.gather_statistics'),
    (r'(?iux) ^ \s* (?: (?P<addressee> \S+ ) : \s+ )?',
        include('iotower.commands')),
                      )
