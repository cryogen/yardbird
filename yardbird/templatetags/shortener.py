from django.template.defaultfilters import stringfilter
from django import template
from yardbird.contrib import shortener

register = template.Library()

@register.filter
@stringfilter
def lengthen(value):
    return shortener.decode64(value)

@register.filter
def shorten(value):
    return shortener.encode64(int(value))
