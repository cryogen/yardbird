from django.conf.urls.defaults import include, patterns
from yardbird.shortcuts import render_silence

urlpatterns = patterns('',
                       (r'.', render_silence),
                      )
