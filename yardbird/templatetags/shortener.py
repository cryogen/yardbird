from django.template.defaultfilters import stringfilter
from yardbird.contrib import shortener

@register.filter
@stringfilter
def lengthen(value):
    return shortener.decode64(value)

@register.filter
def shorten(value):
    return shortener.encode64(int(value))
